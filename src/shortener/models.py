from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import Base


class ShortURL(Base):
    """Модель короткой ссылки."""

    __tablename__ = 'short_url'

    short_code: Mapped[str] = mapped_column(
        String(6), primary_key=True, nullable=False
    )
    original_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, default=0, server_default='0')


