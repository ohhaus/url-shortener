from datetime import datetime

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ShortURL(Base):
    """Модель короткой ссылки."""

    __auto_timestamps__ = True
    __repr_attrs__ = ['short_code', 'clicks', 'is_active']

    original_url: Mapped[str] = mapped_column(Text, nullable=False)
    short_code: Mapped[str] = mapped_column(
        String(10), unique=True, index=True, nullable=False
    )
    clicks: Mapped[int] = mapped_column(default=0)

    @property
    def is_expired(self) -> bool:
        """Проверяет, истекла ли ссылка."""
        return datetime.utcnow() > self.expired_at

    @property
    def can_be_used(self) -> bool:
        """Проверяет, можно ли использовать ссылку."""
        if not self.is_active:
            return False
        if self.is_expired:
            return False
        return True

    @property
    def status(self) -> str:
        """Возвращает статус ссылки для отладки."""
        if not self.is_active:
            return 'deactivated'
        if self.is_expired:
            return 'expired'
        return 'active'
