from datetime import datetime

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
            if len(v) < 3:
                raise ValueError('Short code must be at least 3 characters long')
            if not v.isalnum():
                raise ValueError('Short code can only contain letters and numbers')
            if len(v) > 10:
                raise ValueError('Short code must be at most 10 characters long')
        return v


class ShortURLBase(BaseModel):
    """Базовая схема для коротких ссылок."""

    id: int
    short_code: str
    original_url: str
    clicks: int
    created_at: datetime
    expired_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class ShortURLComputedFields(ShortURLBase):
    @computed_field
    @property
    def short_url(self) -> str:
        return f'{settings.app.BASE_URL}/{self.short_code}'

    @computed_field
    @property
    def is_expired(self) -> bool:
        from datetime import datetime

        return datetime.utcnow() > self.expired_at


class ShortURLResponse(ShortURLComputedFields):
    """Схема ответа с информацией о короткой ссылке."""


class ShortURLStatsResponse(ShortURLComputedFields):
    """Схема для статистики по короткой ссылке."""


class ShortURLDeactivateResponse(BaseModel):
    """Схема ответа при деактивации ссылки."""

    status: str
    message: str
    short_code: str
