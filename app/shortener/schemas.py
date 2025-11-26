from pydantic import BaseModel, HttpUrl

class ShortURLCreate(BaseModel):
    """Схема для создания короткой ссылки."""

    original_url: HttpUrl


class ShortURLResponse(BaseModel):
    short_code: str
    original_url: str
    clicks: int

    class Config:
        from_attributes = True


class ShortURLDeleteResponse(BaseModel):
    status: str = "deleted"
    short_code: str
