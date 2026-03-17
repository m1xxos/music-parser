from pydantic import BaseModel, Field, field_validator

class EditProfile(BaseModel):
    job_id: str
    trim_start_seconds: float = 0
    trim_end_seconds: float | None = None
    title_override: str | None = None
    artist_override: str | None = None
    album_override: str | None = None
    extra_tags: dict[str, str] = Field(default_factory=dict)

    @field_validator('trim_start_seconds', mode='before')
    @classmethod
    def start_default(cls, value):
        if value is None:
            return 0
        return value

    @field_validator('trim_start_seconds')
    @classmethod
    def start_non_negative(cls, value: float) -> float:
        if value < 0:
            raise ValueError('trim_start_seconds must be >= 0')
        return value

    @field_validator('trim_end_seconds')
    @classmethod
    def end_valid(cls, value: float | None, info):
        if value is None:
            return value
        start = info.data.get('trim_start_seconds', 0)
        if value <= start:
            raise ValueError('trim_end_seconds must be > trim_start_seconds')
        return value
