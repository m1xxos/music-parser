from datetime import datetime, timezone
from pydantic import BaseModel, HttpUrl, Field, field_validator

class MediaDescriptor(BaseModel):
    job_id: str
    source_media_id: str
    title: str
    creator: str | None = None
    duration_seconds: int
    thumbnail_url: HttpUrl | None = None
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator('duration_seconds')
    @classmethod
    def duration_must_be_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError('duration_seconds must be > 0')
        return value
