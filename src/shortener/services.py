import secrets
import string

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.cache.services import CacheService
from src.config import settings
from src.shortener.decorators import retry_on_integrity_error
from src.shortener.exceptions import ShortURLNotFound
from src.shortener.models import ShortURL
from src.worker.client import arq_client


class ShortURLService:
    def __init__(self, session: AsyncSession, cache: CacheService) -> None:
        self.session = session
        self.cache = cache

    @retry_on_integrity_error(max_attempts=settings.app.MAX_ATTEMPTS)
    async def create(
        self,
        original_url: str,
        deduplicate: bool = True,
    ) -> ShortURL:
        if deduplicate:
            existing = await self._find_by_original_url(original_url)
            if existing:
                logger.info(
                    "Returning existing short URL (deduplicate=True)",
                    extra={"short_code": existing.short_code},
                )
                return existing

        logger.info("Creating short URL", extra={"original_url": original_url})
        short_code = self._generate_code()
        short_url = ShortURL(original_url=str(original_url), short_code=short_code)
        self.session.add(short_url)
        await self.session.commit()
        await self.session.refresh(short_url)
        await self.cache.cache_redirect_url(short_code, str(original_url))
        logger.info("Short URL created", extra={"short_code": short_code})
        return short_url

    async def get_original_url(self, short_code: str) -> str:
        """Cache-first. Только для редиректов."""
        cached = await self.cache.get_cached_redirect_url(short_code)
        if cached:
            logger.debug("Cache hit on redirect", extra={"short_code": short_code})
            return cached

        logger.debug(
            "Cache miss on redirect, fetching from DB", extra={"short_code": short_code}
        )
        short_url = await self._get_or_raise(short_code)
        await self.cache.cache_redirect_url(short_code, short_url.original_url)
        return short_url.original_url

    async def get_by_code(self, short_code: str) -> ShortURL:
        """DB-first. Для /info и /delete."""
        logger.info("Fetching short URL", extra={"short_code": short_code})
        return await self._get_or_raise(short_code)

    async def delete(self, short_url: ShortURL) -> None:
        logger.info("Deleting short URL", extra={"short_code": short_url.short_code})
        await self.cache.delete_cached_redirect(short_url.short_code)
        await self.session.delete(short_url)
        await self.session.commit()

    async def increment_clicks(self, short_code: str) -> None:
        logger.debug("Queueing click increment", extra={"short_code": short_code})
        await arq_client.enqueue_click(short_code)

    async def _get_or_raise(self, short_code: str) -> ShortURL:
        result = await self.session.execute(
            select(ShortURL).where(ShortURL.short_code == short_code)
        )
        short_url = result.scalar_one_or_none()
        if not short_url:
            logger.warning("Short URL not found", extra={"short_code": short_code})
            raise ShortURLNotFound(f'Short URL "{short_code}" not found')
        return short_url

    async def _find_by_original_url(self, original_url: str) -> ShortURL | None:
        result = await self.session.execute(
            select(ShortURL).where(ShortURL.original_url == original_url)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _generate_code() -> str:
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(settings.app.SHORT_CODE_LENGTH))
