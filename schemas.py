from datetime import datetime

from pydantic import BaseModel, HttpUrl, Field, field_validator

#input schema
class BlogCreate(BaseModel):
    title :str 
    content :str
    summary: str | None = Field(default=None, max_length=500)
    image_url: str | None = None

    source_url: str | None = None

    @field_validator("image_url", "source_url")
    @classmethod
    def validate_image_url(cls, value):
        if value is None or not value.strip():
            return None
        return str(HttpUrl(value.strip()))

class BlogResponse(BaseModel):
    id : int
    title : str
    content : str
    summary: str | None = None
    image_url: str | None = None

    source_url: str | None = None
    published_at: datetime | None = None

    class Config:
        from_attributes = True