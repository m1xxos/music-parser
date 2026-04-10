from pydantic import BaseModel, HttpUrl, Field, field_validator

class BatchTrim(BaseModel):
    startSeconds: float | None = None
    endSeconds: float | None = None


class BatchMetadata(BaseModel):
    artist: str | None = None
    album: str | None = None


class BatchRequest(BaseModel):
    urls: list[HttpUrl] = Field(min_length=1, max_length=20)
    trim: BatchTrim | None = None
    metadata: BatchMetadata | None = None

    @field_validator('urls')
    @classmethod
    def unique_urls(cls, values):
        if len(set(map(str, values))) != len(values):
            raise ValueError('urls must be unique')
        return values
