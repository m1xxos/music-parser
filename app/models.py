from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class SourcePlatform(str, Enum):
    youtube = "youtube"
    rutube = "rutube"
    soundcloud = "soundcloud"
    vk = "vk"
    unknown = "unknown"


class AudioFormat(str, Enum):
    mp3 = "mp3"
    m4a = "m4a"
    flac = "flac"


class JobState(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class MetadataRequest(BaseModel):
    url: HttpUrl


class MetadataPreview(BaseModel):
    source: SourcePlatform
    url: HttpUrl
    source_id: str | None = None
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    year: int | None = None
    track: int | None = None
    genre: str | None = None
    comment: str | None = None
    duration_seconds: int | None = None
    upload_date: str | None = None
    thumbnail_url: str | None = None
    description: str | None = None


class MetadataOverrides(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    artist: str | None = Field(default=None, max_length=200)
    album: str | None = Field(default=None, max_length=200)
    year: int | None = Field(default=None, ge=1900, le=2200)
    track: int | None = Field(default=None, ge=1, le=999)
    genre: str | None = Field(default=None, max_length=100)
    comment: str | None = Field(default=None, max_length=10000)


class DownloadRequest(BaseModel):
    url: HttpUrl
    output_format: AudioFormat = AudioFormat.mp3
    quality: str = Field(default="320", pattern=r"^(128|192|256|320)$")
    auto_scan_navidrome: bool = True
    metadata: MetadataOverrides = Field(default_factory=MetadataOverrides)


class JobCreateResponse(BaseModel):
    job_id: str
    state: JobState


class DownloadResult(BaseModel):
    source: SourcePlatform
    file_path: str
    download_url: str
    metadata: MetadataPreview
    tagged: bool = True
    navidrome_scan_triggered: bool = False


class JobStatusResponse(BaseModel):
    job_id: str
    state: JobState
    progress: int = Field(ge=0, le=100)
    message: str
    created_at: datetime
    updated_at: datetime
    error: str | None = None
    result: DownloadResult | None = None


class ApiError(BaseModel):
    detail: str


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
