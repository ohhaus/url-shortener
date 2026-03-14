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


logger = logging.getLogger('app')


class ShortURLService:
    def __init__(self, session: AsyncSession, cache: CacheService) -> None:
        self.session = session
        self.cache = cache

    @retry_on_integrity_error(max_attempts=settings.app.MAX_ATTEMPTS)
    async def create(self, original_url: str) -> ShortURL:
        logger.info('Creating short URL', extra={'original_url': original_url})
        short_code = self._generate_code()
        short_url = ShortURL(original_url=str(original_url), short_code=short_code)
        self.session.add(short_url)
        await self.session.commit()
        await self.session.refresh(short_url)
        await self.cache.cache_redirect_url(short_code, str(original_url))
        logger.info('Short URL created', extra={'short_code': short_code})
        return short_url

    async def get_original_url(self, short_code: str) -> str:
        """Cache-first. Только для редиректов — не трогает БД при cache hit."""
        cached = await self.cache.get_cached_redirect_url(short_code)
        if cached:
            logger.debug('Cache hit on redirect', extra={'short_code': short_code})
            return cached

        logger.debug(
            'Cache miss on redirect, fetching from DB', extra={'short_code': short_code}
        )
        result = await self.session.execute(
            select(ShortURL).where(ShortURL.short_code == short_code)
        )
        short_url = result.scalar_one_or_none()
        if not short_url:
            logger.warning('Short URL not found', extra={'short_code': short_code})
            raise ShortURLNotFound(f'Short URL "{short_code}" not found')

        await self.cache.cache_redirect_url(short_code, short_url.original_url)
        return short_url.original_url

    async def get_by_code(self, short_code: str) -> ShortURL:
        """DB-first. Для /info и /delete — нужен полный объект с clicks."""
        logger.info('Fetching short URL', extra={'short_code': short_code})
        result = await self.session.execute(
            select(ShortURL).where(ShortURL.short_code == short_code)
        )
        short_url = result.scalar_one_or_none()
        if not short_url:
            logger.warning('Short URL not found', extra={'short_code': short_code})
            raise ShortURLNotFound(f'Short URL "{short_code}" not found')

        return short_url

    async def delete(self, short_url: ShortURL) -> None:
        logger.info('Deleting short URL', extra={'short_code': short_url.short_code})
        await self.cache.delete_cached_redirect(short_url.short_code)
        await self.session.delete(short_url)
        await self.session.commit()

    async def increment_clicks(self, short_code: str) -> None:
        logger.debug('Queueing click increment', extra={'short_code': short_code})
        await arq_client.enqueue_click(short_code)

    @staticmethod
    def _generate_code() -> str:
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(settings.app.SHORT_CODE_LENGTH))
