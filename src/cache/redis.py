from redis.asyncio import Redis

from src.config import settings


class RedisManager:
    """Менеджер для работы с Redis."""

    def __init__(self):
        self.redis: Redis | None = None

    async def init(self):
        """Инициализация подключения к Redis."""
        self.redis = Redis.from_url(
            settings.redis.URL,
            password=settings.redis.PASSWORD,
            socket_connect_timeout=settings.redis.SOCKET_CONNECT_TIMEOUT,
            socket_timeout=settings.redis.SOCKET_TIMEOUT,
            retry_on_timeout=settings.redis.RETRY_ON_TIMEOUT,
            max_connections=settings.redis.MAX_CONNECTIONS,
            decode_responses=True,
        )

        await self.redis.ping()

    async def close(self):
        """Закрытие подключения."""
        if self.redis:
            await self.redis.close()

    def get_client(self) -> Redis:
        """Получение клиента Redis."""
        if not self.redis:
            raise RuntimeError('Redis client not initialized')
        return self.redis


redis_manager = RedisManager()


async def get_redis() -> Redis:
    return redis_manager.get_client()
