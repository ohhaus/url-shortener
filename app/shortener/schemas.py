from pydantic import BaseModel, computed_field, field_validator

from app.config import settings


class ShortURLCreate(BaseModel):
    """Схема для создания короткой ссылки."""

    original_url: str
    short_code: str | None = None

    @field_validator('short_code')
    @classmethod
    def validate_short_code(cls, v):
        if v is not None:
            if len(v) != 6:
                raise ValueError('Short code must be exactly 6 characters long')
            if not v.isalnum():
                raise ValueError('Short code can only contain letters and numbers')
        return v

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
