import random
import secrets
import string

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shortener.exceptions import (
    ShortCodeAlreadyExists,
    ShortURLNotFound,
)
from app.shortener.models import ShortURL
from app.config import settings


class ShortURLService:
    """Сервис для работы с короткими ссылками."""

    @staticmethod
    async def create_short_url(
        session: AsyncSession, original_url: str, short_code: str | None = None
    ) -> ShortURL:
        """Создает короткую ссылку."""
        if short_code:
            if await ShortURLService._is_code_exists(session, short_code):
                raise ShortCodeAlreadyExists(f'Short code "{short_code}" already exists')
        else:
            short_code = await ShortURLService._generate_unique_code(session)

        short_url = ShortURL(
            original_url=str(original_url),
            short_code=short_code,
        )

        session.add(short_url)
        await session.commit()
        await session.refresh(short_url)

        return short_url

    @staticmethod
    async def get_by_code(session: AsyncSession, short_code: str) -> ShortURL:
        """Получает короткую ссылку по коду."""
        result = await session.execute(
            select(ShortURL).where(ShortURL.short_code == short_code)
        )
        short_url = result.scalar_one_or_none()

        if not short_url:
            raise ShortURLNotFound(f'Short URL with code "{short_code}" not found')

        return short_url

    @staticmethod
    async def _is_code_exists(session: AsyncSession, code: str) -> bool:
        """Проверяет, существует ли уже такой код."""
        result = await session.execute(select(ShortURL).where(ShortURL.short_code == code))
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def _generate_unique_code(session: AsyncSession) -> str:
        """Генерирует уникальный короткий код."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(settings.app.SHORT_CODE_LENGTH))


    @staticmethod
    async def increment_clicks(session: AsyncSession, short_url: ShortURL) -> None:
        """Увеличивает счетчик кликов."""
        short_url.clicks += 1
        await session.commit()
    
    @staticmethod
    async def delete_short_url(session: AsyncSession, short_url: ShortURL) -> None:
        await session.delete(short_url)
        await session.commit()

        return short_url
