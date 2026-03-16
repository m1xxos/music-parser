"""FastAPI application for Music Parser."""
import asyncio
import math
import os
import random
import shutil
import subprocess
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

import yt_dlp
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

app = FastAPI(title="Music Parser")

_executor = ThreadPoolExecutor(max_workers=4)
_jobs: dict[str, dict] = {}
_waveform_cache: dict[str, dict] = {}
_preview_cache: dict[str, str] = {}

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/music")


class DownloadPayload(BaseModel):
    url: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None

    @field_validator("url")
    @classmethod
    def url_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("url must not be empty")
        return v.strip()


@app.post("/api/download", status_code=202)
async def create_download(payload: DownloadPayload, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "pending", "message": "Queued"}
    background_tasks.add_task(_run_download, job_id, payload)
    return {"job_id": job_id}


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/metadata/{video_id}")
async def get_metadata(video_id: str, url: str):
    """Fetch video metadata and generate waveform."""
    if video_id in _waveform_cache:
        return JSONResponse(content=_waveform_cache[video_id])

    def _fetch_metadata(video_url: str) -> dict:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": False,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

        duration = info.get("duration", 0)
        title = info.get("title", "Unknown")
        artist = info.get("artist") or info.get("creator") or info.get("uploader") or info.get("channel") or ""
        thumbnail = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

        # Generate waveform
        random.seed(hash(video_id) % 2**32)
        base_freq = random.uniform(0.05, 0.15)
        peaks = []
        for i in range(100):
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
            "thumbnail": thumbnail,
        }

    try:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(_executor, _fetch_metadata, url)
        _waveform_cache[video_id] = data
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/preview/{video_id}")
async def get_preview(video_id: str, url: str):
    """Download and stream 30-second audio preview."""
    if video_id in _preview_cache and os.path.exists(_preview_cache[video_id]):
        return FileResponse(_preview_cache[video_id], media_type="audio/mp3", filename="preview.mp3")

    def _download_preview(video_url: str) -> Optional[str]:
        tmpdir = tempfile.mkdtemp()
        tmp = Path(tmpdir)

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(tmp / "preview"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }],
            "extract_args": ["-ss", "0", "-t", "30"],
            "quiet": True,
            "no_warnings": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(video_url, download=True)

            mp3_files = list(tmp.glob("*.mp3"))
            if mp3_files:
                return str(mp3_files[0])
        except Exception:
            pass
        return None

    try:
        loop = asyncio.get_event_loop()
        audio_path = await loop.run_in_executor(_executor, _download_preview, url)

        if audio_path and os.path.exists(audio_path):
            _preview_cache[video_id] = audio_path
            return FileResponse(audio_path, media_type="audio/mp3", filename="preview.mp3")
        raise HTTPException(status_code=404, detail="Could not download preview")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _run_download(job_id: str, payload: DownloadPayload) -> None:
    _jobs[job_id] = {"status": "downloading", "message": "Downloading audio..."}
    loop = asyncio.get_event_loop()

    try:
        await loop.run_in_executor(_executor, _download_audio, payload)
        _jobs[job_id] = {"status": "done", "message": "Download complete!"}
    except Exception as e:
        _jobs[job_id] = {"status": "error", "message": str(e)}


def _download_audio(payload: DownloadPayload) -> None:
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(tmp / "%(id)s.%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }],
            "writethumbnail": True,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(payload.url, download=True)

        title = payload.title or info.get("title") or "Unknown"
        artist = payload.artist or info.get("uploader") or "Unknown"
        album = payload.album or title

        mp3_files = list(tmp.glob("*.mp3"))
        if not mp3_files:
            raise RuntimeError("No audio downloaded")

        source_mp3 = mp3_files[0]

        # Trim if needed
        if payload.start_time or payload.end_time:
            trimmed_mp3 = tmp / "trimmed.mp3"
            cmd = ["ffmpeg", "-y", "-i", str(source_mp3)]
            if payload.start_time:
                cmd += ["-ss", payload.start_time]
            if payload.end_time:
                cmd += ["-to", payload.end_time]
            cmd += ["-acodec", "libmp3lame", "-q:a", "2", str(trimmed_mp3)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg trim failed: {result.stderr}")
            source_mp3 = trimmed_mp3

        # Copy to output
        safe_title = _safe_filename(title)
        dest = output_dir / f"{safe_title}.mp3"
        counter = 1
        while dest.exists():
            dest = output_dir / f"{safe_title} ({counter}).mp3"
            counter += 1
        shutil.copy2(str(source_mp3), str(dest))

        # Tag metadata
        _tag_mp3(dest, title, artist, album, tmp, info.get("thumbnail"))


def _safe_filename(name: str) -> str:
    import re
    safe = re.sub(r'[^\w\s\-().]', '', name).strip()
    safe = re.sub(r'\s+', ' ', safe)
    return safe or "audio"


def _tag_mp3(path: Path, title: str, artist: str, album: str, tmpdir: Path, thumbnail_url: Optional[str]) -> None:
    try:
        from mutagen.id3 import APIC, ID3, TALB, TIT2, TPE1
        from mutagen.mp3 import MP3

        audio = MP3(str(path), ID3=ID3)
        if audio.tags is None:
            audio.add_tags()

        audio.tags["TIT2"] = TIT2(encoding=3, text=title)
        audio.tags["TPE1"] = TPE1(encoding=3, text=artist)
        audio.tags["TALB"] = TALB(encoding=3, text=album)

        # Find cover art
        for ext, mime in [("jpg", "image/jpeg"), ("jpeg", "image/jpeg"), ("png", "image/png")]:
            files = list(tmpdir.glob(f"*.{ext}"))
            if files:
                audio.tags["APIC"] = APIC(encoding=0, mime=mime, type=3, desc="Cover", data=files[0].read_bytes())
                break
        else:
            if thumbnail_url:
                import requests
                try:
                    resp = requests.get(thumbnail_url, timeout=10)
                    if resp.ok:
                        audio.tags["APIC"] = APIC(encoding=0, mime="image/jpeg", type=3, desc="Cover", data=resp.content)
                except Exception:
                    pass

        audio.save()
    except Exception:
        pass  # Tagging is optional


_STATIC_DIR = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=str(_STATIC_DIR), html=True), name="static")
