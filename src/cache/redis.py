from loguru import logger
from redis.asyncio import Redis

from src.config import settings


class RedisManager:
    def __init__(self):
        self.redis: Redis | None = None

    async def init(self):
        logger.info("Connecting to Redis...")
        self.redis = Redis.from_url(
            settings.redis.URL,
            password=settings.redis.PASSWORD,
            decode_responses=True,
            max_connections=settings.redis.MAX_CONNECTIONS,
        )
        await self.redis.ping()
        logger.info("Redis connected")

    async def close(self):
        if self.redis:
            logger.info("Closing Redis...")
            await self.redis.close()
            logger.info("Redis closed")

    def get(self) -> Redis:
        if not self.redis:
            raise RuntimeError("Redis not initialized")
        return self.redis


redis_manager = RedisManager()
