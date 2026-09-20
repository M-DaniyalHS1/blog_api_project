from datetime import datetime

from pydantic import BaseModel, HttpUrl, Field, field_validator

class UserPublic(BaseModel):
    id: int
    username: str

    model_config = {"from_attributes": True}


class ProfilePublic(UserPublic):
    display_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=80)
    bio: str | None = Field(default=None, max_length=1000)
    avatar_url: str | None = Field(default=None, max_length=2048)
    model_config = {"extra": "forbid"}

    @field_validator("display_name", "bio", "avatar_url")
    @classmethod
    def clean_text(cls, value):
        return value.strip() or None if value is not None else None

    @field_validator("avatar_url")
    @classmethod
    def check_avatar(cls, value):
        return str(HttpUrl(value)) if value else None


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[a-z0-9_]+$")
    password: str = Field(min_length=8, max_length=128)

    model_config = {"extra": "forbid"}

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


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

    author_id: int | None = None
    author: ProfilePublic | None = None

    class Config:
        from_attributes = True