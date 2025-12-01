from redis.asyncio import Redis

from src.cache.keys import RedisKeys
from src.config import settings


class CacheService:
    """Сервис для работы с кэшем."""

    def __init__(self, redis: Redis):
        self.redis = redis

    async def cache_redirect_url(self, short_code: str, original_url: str) -> None:
        """Кэширует URL для редиректа."""
        await self.redis.setex(
            RedisKeys.redirect_key(short_code), settings.redis.REDIRECT_CACHE_TTL, original_url
        )

    async def get_cached_redirect_url(self, short_code: str) -> str | None:
        """Получает закэшированный URL для редиректа."""
        return await self.redis.get(RedisKeys.redirect_key(short_code))

    async def delete_cached_redirect(self, short_code: str) -> None:
        """Удаляет закэшированный редирект."""
        await self.redis.delete(RedisKeys.redirect_key(short_code))

    async def increment_clicks(self, short_code: str) -> int:
        """Инкрементит счетчик кликов в кэше."""
        key = RedisKeys.click_key(short_code)
        clicks = await self.redis.incr(key)
        await self.redis.expire(key, settings.redis.CLICK_CACHE_TTL)
        return clicks

    async def get_cached_clicks(self, short_code: str) -> int:
        """Получает количество кликов из кэша."""
        clicks = await self.redis.get(RedisKeys.click_key(short_code))
        return int(clicks) if clicks else 0

    async def delete_cached_clicks(self, short_code: str) -> None:
        """Удаляет счетчик кликов из кэша."""
        await self.redis.delete(RedisKeys.click_key(short_code))
