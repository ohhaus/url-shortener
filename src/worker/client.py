from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings

from src.config import settings


class ARQClient:
    """Простой клиент для работы с ARQ."""

    def __init__(self):
        self.pool = None

    async def connect(self):
        """Подключение к Redis для ARQ."""
        try:
            self.pool = await create_pool(RedisSettings.from_dsn(settings.worker.REDIS_DSN))
            return True
        except Exception as e:
            print(f'Failed to connect to ARQ Redis: {e}')
            return False

    async def enqueue_click(self, short_code: str) -> str | None:
        """Добавляет задачу записи клика."""
        if not self.pool:
            success = await self.connect()
            if not success:
                return None

        try:
            job = await self.pool.enqueue_job('record_click', short_code)
            return job.job_id if job else None
        except Exception as e:
            print(f'Failed to enqueue click: {e}')
            return None

    async def close(self):
        """Закрытие соединения."""
        if self.pool:
            await self.pool.close()


arq_client = ARQClient()


@asynccontextmanager
async def get_arq_client():
    """Контекстный менеджер для ARQ клиента."""
    client = ARQClient()
    await client.connect()
    try:
        yield client
    finally:
        await client.close()
