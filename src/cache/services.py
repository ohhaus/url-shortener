import logging

from redis.asyncio import Redis

from src.cache.keys import RedisKeys
from src.config import settings


logger = logging.getLogger(__name__)


class CacheService:
    """Сервис для кэширования redirect URL."""

    def __init__(self, redis: Redis):
        self.redis = redis

    async def cache_redirect_url(self, short_code: str, original_url: str):
        logger.info("Caching redirect", extra={"short_code": short_code})
        await self.redis.setex(
            RedisKeys.redirect_key(short_code),
            settings.redis.REDIRECT_CACHE_TTL,
            original_url,
        )

    async def get_cached_redirect_url(self, short_code: str) -> str | None:
        url = await self.redis.get(RedisKeys.redirect_key(short_code))
        logger.info("Cache hit" if url else "Cache miss",
                    extra={"short_code": short_code})
        return url

    async def delete_cached_redirect(self, short_code: str):
        logger.info("Deleting cached redirect", extra={"short_code": short_code})
        await self.redis.delete(RedisKeys.redirect_key(short_code))
