from pydantic import BaseModel, HttpUrl, Field, field_validator

class BatchRequest(BaseModel):
    urls: list[HttpUrl] = Field(min_length=1, max_length=20)

    @field_validator('urls')
    @classmethod
    def unique_urls(cls, values):
        if len(set(map(str, values))) != len(values):
            raise ValueError('urls must be unique')
        return values
