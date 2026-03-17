import re
from datetime import datetime, timezone
from pathlib import Path
from pydantic import BaseModel, Field, field_validator

class ExportArtifact(BaseModel):
    id: str
    job_id: str
    filename: str
    format: str = 'mp3'
    size_bytes: int
    duration_seconds: float
    storage_path: str
    download_token: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator('size_bytes')
    @classmethod
    def positive_size(cls, value: int) -> int:
        if value < 1:
            raise ValueError('size_bytes must be >= 1')
        return value


def sanitize_filename(name: str) -> str:
    base = re.sub(r'[^\w\s\-().]', '', name).strip()
    return re.sub(r'\s+', ' ', base) or 'audio'


def resolve_collision(output_dir: Path, filename: str) -> Path:
    candidate = output_dir / filename
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    n = 1
    while candidate.exists():
        candidate = output_dir / f'{stem} ({n}){suffix}'
        n += 1
    return candidate
