from pydantic import BaseModel, computed_field

from app.config import settings


class ShortURLCreate(BaseModel):
    """Схема для создания короткой ссылки."""

    original_url: str


class ShortURLResponse(BaseModel):
    short_code: str
    original_url: str
    clicks: int

    class Config:
        from_attributes = True
    
    @computed_field
    @property
    def short_url(self) -> str:
        return f'{settings.app.BASE_URL}/{self.short_code}'


class ShortURLDeleteResponse(BaseModel):
    status: str = "deleted"
    short_code: str
