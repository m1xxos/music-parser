from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import ensure_directories, load_settings
from app.models import ApiError, DownloadRequest, JobCreateResponse, JobStatusResponse, MetadataPreview, MetadataRequest
from app.services.downloader import DownloadError, DownloadService
from app.services.jobs import JobManager


settings = load_settings()
ensure_directories(settings)

static_dir = Path(__file__).parent / "static"
downloader = DownloadService(settings)
job_manager = JobManager(downloader)

app = FastAPI(
    title="Navidrome Music Downloader",
    version="0.1.0",
    description="Download and tag audio from YouTube, RuTube, SoundCloud and VK Video for Navidrome.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    job_manager.start()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/metadata", response_model=MetadataPreview, responses={400: {"model": ApiError}})
def metadata_preview(request: MetadataRequest) -> MetadataPreview:
    try:
        return downloader.extract_metadata(str(request.url))
    except DownloadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/jobs", response_model=JobCreateResponse, responses={400: {"model": ApiError}})
def create_job(request: DownloadRequest) -> JobCreateResponse:
    try:
        return job_manager.create_job(request)
    except DownloadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/jobs", response_model=list[JobStatusResponse])
def list_jobs() -> list[JobStatusResponse]:
    return job_manager.list_jobs()


@app.get("/api/jobs/{job_id}", response_model=JobStatusResponse, responses={404: {"model": ApiError}})
def get_job(job_id: str) -> JobStatusResponse:
    status = job_manager.get_job(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return status


app.mount("/media", StaticFiles(directory=str(settings.output_root)), name="media")
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", include_in_schema=False)
def root() -> FileResponse:
    return FileResponse(static_dir / "index.html")
