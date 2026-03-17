from datetime import datetime, timezone
from pydantic import BaseModel, Field

class PresetProfile(BaseModel):
    id: str
    name: str
    trim_start_seconds: float = 0
    trim_end_seconds: float | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
