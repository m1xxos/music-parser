from datetime import datetime, timezone
from pydantic import BaseModel, Field, HttpUrl, field_validator
from app.domain.constants import JOB_STATUSES, TERMINAL_STATUSES

_ALLOWED = {
    'queued': {'fetching', 'failed', 'canceled'},
    'fetching': {'processing', 'failed', 'canceled'},
    'processing': {'tagging', 'failed', 'canceled'},
    'tagging': {'completed', 'failed', 'canceled'},
    'completed': set(),
    'failed': set(),
    'canceled': set(),
}

class SourceJob(BaseModel):
    id: str
    source_url: HttpUrl
    source_platform: str
    status: str = 'queued'
    progress_percent: int = 0
    status_message: str = 'Queued'
    error_code: str | None = None
    error_detail: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None

    @field_validator('status')
    @classmethod
    def status_known(cls, value: str) -> str:
        if value not in JOB_STATUSES:
            raise ValueError('unknown status')
        return value

    def transition(self, new_status: str, progress_percent: int, message: str) -> 'SourceJob':
        if new_status not in _ALLOWED[self.status]:
            raise ValueError(f'invalid transition {self.status} -> {new_status}')
        if progress_percent < self.progress_percent and new_status not in ('failed', 'canceled'):
            raise ValueError('progress must be monotonic')
        self.status = new_status
        self.progress_percent = progress_percent
        self.status_message = message
        self.updated_at = datetime.now(timezone.utc)
        if new_status in TERMINAL_STATUSES:
            self.completed_at = datetime.now(timezone.utc)
        return self
