"""FastAPI application for Music Parser."""
import asyncio
import hashlib
import json
import math
import os
import random
import subprocess
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

import httpx
import yt_dlp
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

from downloader import DownloadRequest, download_and_process

app = FastAPI(title="Music Parser")

# Thread pool for blocking I/O (yt-dlp / ffmpeg)
_executor = ThreadPoolExecutor(max_workers=4)

# In-memory job store  {job_id: {"status": ..., "message": ..., "file": ...}}
_jobs: dict[str, dict] = {}

# Cache for waveform data
_waveform_cache: dict[str, dict] = {}

# Cache for downloaded audio files (for preview)
_audio_cache: dict[str, str] = {}
_audio_info_cache: dict[str, dict] = {}


# ── Request / response schemas ────────────────────────────────────────────────

class DownloadPayload(BaseModel):
    url: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    album_artist: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[str] = None
    track_number: Optional[int] = None

    @field_validator("url")
    @classmethod
    def url_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("url must not be empty")
        return v.strip()


# ── API routes ────────────────────────────────────────────────────────────────

@app.post("/api/download", status_code=202)
async def create_download(payload: DownloadPayload, background_tasks: BackgroundTasks):
    """Queue a download job and return its ID immediately."""
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "pending", "message": "Queued"}
    background_tasks.add_task(_run_download, job_id, payload)
    return {"job_id": job_id}


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """Poll the status of a download job."""
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/waveform/{video_id}")
async def get_waveform(video_id: str, url: Optional[str] = None):
    """Get waveform data for a video - uses fast metadata fetch + simulated waveform."""
    # Check cache first
    if video_id in _waveform_cache:
        return JSONResponse(content=_waveform_cache[video_id])

    if not url:
        raise HTTPException(status_code=400, detail="URL parameter required for waveform generation")

    def _extract_waveform(video_url: str) -> dict:
        # Fast metadata-only fetch - no audio download
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "logger": None,
            "skip_download": True,
            "extract_flat": False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            duration = info.get("duration", 0)
            title = info.get("title", "Unknown")
            artist = info.get("artist") or info.get("creator") or info.get("uploader") or info.get("channel") or ""

        # Generate deterministic pseudo-random waveform based on video_id
        # This is instant and gives consistent results
        import random
        random.seed(hash(video_id) % 2**32)

        # Generate waveform with structure (peaks and valleys like real audio)
        peaks = []
        base_freq = random.uniform(0.05, 0.15)  # Base rhythm frequency
        for i in range(100):
            # Combine multiple sine-like waves for natural look
            value = (
                0.5 * (0.5 + 0.5 * math.sin(i * base_freq * 6.28)) +
                0.3 * random.uniform(0, 1) +
                0.2 * (0.5 + 0.5 * math.sin(i * base_freq * 12.56))
            )
            peaks.append(min(1.0, max(0.1, value)))

        return {
            "peaks": peaks,
            "duration": duration,
            "video_id": video_id,
            "title": title,
            "artist": artist,
        }

    try:
        loop = asyncio.get_event_loop()
        waveform_data = await loop.run_in_executor(_executor, _extract_waveform, url)
        _waveform_cache[video_id] = waveform_data
        return JSONResponse(content=waveform_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audio-preview/{video_id}")
async def get_audio_preview(video_id: str, url: Optional[str] = None):
    """Download and stream a 30-second audio preview for playback."""
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter required")

    # Check if we already have this audio cached
    if video_id in _audio_cache and os.path.exists(_audio_cache[video_id]):
        audio_path = _audio_cache[video_id]
        return FileResponse(audio_path, media_type="audio/mp3", filename="preview.mp3")

    def _download_preview(video_url: str) -> str:
        import tempfile
        tmpdir = tempfile.mkdtemp()
        tmp = Path(tmpdir)
        
        # Download only first 30 seconds for preview
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(tmp / "preview"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }],
            "extract_args": ["-ss", "0", "-t", "30"],  # First 30 seconds
            "quiet": True,
            "no_warnings": True,
            "logger": None,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(video_url, download=True)
        
        # Find the mp3 file
        mp3_files = list(tmp.glob("*.mp3"))
        if mp3_files:
            return str(mp3_files[0])
        return None

    try:
        loop = asyncio.get_event_loop()
        audio_path = await loop.run_in_executor(_executor, _download_preview, url)
        
        if audio_path and os.path.exists(audio_path):
            _audio_cache[video_id] = audio_path
            return FileResponse(audio_path, media_type="audio/mp3", filename="preview.mp3")
        else:
            raise HTTPException(status_code=404, detail="Could not download audio preview")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Background task ───────────────────────────────────────────────────────────

async def _run_download(job_id: str, payload: DownloadPayload) -> None:
    _jobs[job_id] = {"status": "downloading", "message": "Downloading audio…"}
    loop = asyncio.get_event_loop()
    try:
        req = DownloadRequest(
            url=payload.url,
            start_time=payload.start_time,
            end_time=payload.end_time,
            title=payload.title,
            artist=payload.artist,
            album=payload.album,
            album_artist=payload.album_artist,
            genre=payload.genre,
            year=payload.year,
            track_number=payload.track_number,
        )
        filename = await loop.run_in_executor(_executor, download_and_process, req)
        _jobs[job_id] = {
            "status": "done",
            "message": f"Saved: {filename}",
            "file": filename,
        }
    except Exception as exc:  # noqa: BLE001
        _jobs[job_id] = {"status": "error", "message": str(exc)}


# ── Static files (must be last) ───────────────────────────────────────────────

_STATIC_DIR = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=str(_STATIC_DIR), html=True), name="static")
