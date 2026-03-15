
from src.cache.redis import redis_manager
from src.cache.services import CacheService


async def get_cache_service() -> CacheService:
    redis = redis_manager.get()
    return CacheService(redis)
