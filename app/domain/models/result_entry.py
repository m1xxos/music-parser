from datetime import datetime, timezone
from pydantic import BaseModel, Field, model_validator

class ResultEntry(BaseModel):
    job_id: str
    status: str
    summary: str
    artifact_id: str | None = None
    last_viewed_at: datetime | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode='after')
    def check_artifact_requirement(self):
        if self.status == 'completed' and not self.artifact_id:
            raise ValueError('artifact_id required for completed status')
        if self.status == 'failed' and not self.summary.strip():
            raise ValueError('failed summary required')
        return self
