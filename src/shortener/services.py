import logging
import secrets
import string

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.cache.services import CacheService
from src.config import settings
from src.shortener.decorators import retry_on_integrity_error
from src.shortener.exceptions import ShortURLNotFound
from src.shortener.models import ShortURL
from src.worker.client import arq_client


logger = logging.getLogger("app")


class ShortURLService:
    """Сервис для работы с короткими ссылками."""

    @staticmethod
    @retry_on_integrity_error(max_attempts=settings.app.MAX_ATTEMPTS)
    async def create_short_url(
        session: AsyncSession, cache: CacheService, original_url: str
    ) -> ShortURL:
        """Создает короткую ссылку."""
        logger.info('Creating short URL', extra={'original_url': original_url})

        short_code = await ShortURLService._generate_unique_code()

        short_url = ShortURL(
            original_url=str(original_url),
            short_code=short_code,
        )

        session.add(short_url)
        await session.commit()
        await session.refresh(short_url)

        await cache.cache_redirect_url(short_code, str(original_url))

        logger.info('Short URL created', extra={'short_code': short_code})
        return short_url

    @staticmethod
    async def get_by_code(
        session: AsyncSession, cache: CacheService, short_code: str
    ) -> ShortURL:
        """Получает короткую ссылку по коду."""
        logger.info('Fetching short URL', extra={'short_code': short_code})

        cached_url = await cache.get_cached_redirect_url(short_code)

        result = await session.execute(
            select(ShortURL).where(ShortURL.short_code == short_code)
        )
        db_short_url = result.scalar_one_or_none()

        if not db_short_url:
            logger.warning('Short URL not found', extra={'short_code': short_code})
            raise ShortURLNotFound(f'Short URL "{short_code}" not found')
        if cached_url:
            db_short_url.original_url = cached_url
            logger.info('Using cached URL', extra={'short_code': short_code})
        else:
            await cache.cache_redirect_url(short_code, db_short_url.original_url)
            logger.info('Cached URL from DB', extra={'short_code': short_code})

        return db_short_url

    @staticmethod
    async def _generate_unique_code() -> str:
        """Генерирует уникальный короткий код."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(settings.app.SHORT_CODE_LENGTH))

    @staticmethod
    async def increment_clicks(short_code: str) -> None:
        """Увеличивает счетчик кликов."""
        logger.debug('Queueing click increment', extra={'short_code': short_code})
        return await arq_client.enqueue_click(short_code)

    @staticmethod
    async def delete_short_url(
        session: AsyncSession, cache: CacheService, short_url: ShortURL
    ) -> None:
        """Удаляет короткую ссылку."""
        await cache.delete_cached_redirect(short_url.short_code)

        await session.delete(short_url)
        await session.commit()
