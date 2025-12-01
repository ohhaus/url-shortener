import secrets
import string

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.cache.redis import get_redis
from src.cache.services import CacheService
from src.config import settings
from src.shortener.decorators import retry_on_integrity_error
from src.shortener.exceptions import ShortURLNotFound
from src.shortener.models import ShortURL


class ShortURLService:
    """Сервис для работы с короткими ссылками."""

    @staticmethod
    @retry_on_integrity_error(max_attempts=settings.app.MAX_ATTEMPTS)
    async def create_short_url(session: AsyncSession, original_url: str) -> ShortURL:
        """Создает короткую ссылку."""
        short_code = await ShortURLService._generate_unique_code(session)

        short_url = ShortURL(
            original_url=str(original_url),
            short_code=short_code,
        )

        session.add(short_url)
        await session.commit()
        await session.refresh(short_url)

        redis = await get_redis()
        cache_service = CacheService(redis)
        await cache_service.cache_redirect_url(short_code, str(original_url))

        return short_url

    @staticmethod
    async def get_by_code(session: AsyncSession, short_code: str) -> ShortURL:
        """Получает короткую ссылку по коду."""
        redis = await get_redis()
        cache_service = CacheService(redis)

        cached_url = await cache_service.get_cached_redirect_url(short_code)
        if cached_url:
            return ShortURL(short_code=short_code, original_url=cached_url, clicks=0)

        result = await session.execute(
            select(ShortURL).where(ShortURL.short_code == short_code)
        )
        short_url = result.scalar_one_or_none()

        if not short_url:
            raise ShortURLNotFound(f'Short URL with code "{short_code}" not found')

        await cache_service.cache_redirect_url(short_code, short_url.original_url)

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
        # redis = await get_redis()
        # cache_service = CacheService(redis)

        # await cache_service.increment_clicks(short_url.short_code)

        short_url.clicks += 1
        await session.commit()

    @staticmethod
    async def get_total_clicks(short_url: ShortURL) -> int:
        """Получает общее количество кликов."""
        return short_url.clicks

    @staticmethod
    async def delete_short_url(session: AsyncSession, short_url: ShortURL) -> None:
        """Удаляет короткую ссылку."""
        redis = await get_redis()
        cache_service = CacheService(redis)

        await cache_service.delete_cached_redirect(short_url.short_code)
        await cache_service.delete_cached_clicks(short_url.short_code)

        await session.delete(short_url)
        await session.commit()
