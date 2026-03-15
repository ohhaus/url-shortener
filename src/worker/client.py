from arq import create_pool
from arq.connections import RedisSettings
from loguru import logger

from src.config import settings


class ARQClient:
    """Клиент для постановки задач в очередь ARQ."""

    def __init__(self) -> None:
        self.pool = None

    async def connect(self) -> None:
        logger.info("Connecting to ARQ Redis...")
        self.pool = await create_pool(RedisSettings.from_dsn(settings.worker.REDIS_DSN))
        logger.info("ARQ Redis connected")

    async def enqueue_click(self, short_code: str) -> str | None:
        """Ставит задачу записи клика в очередь."""
        if not self.pool:
            logger.warning(
                "ARQ pool not initialized, skipping click enqueue",
                extra={"short_code": short_code},
            )
            return None

        job = await self.pool.enqueue_job("record_click", short_code)
        if job:
            logger.debug(
                "Click enqueued", extra={"short_code": short_code, "job_id": job.job_id}
            )
            return job.job_id

        logger.warning("Failed to enqueue click job", extra={"short_code": short_code})
        return None

    async def close(self) -> None:
        if self.pool:
            logger.info("Closing ARQ Redis connection...")
            await self.pool.close()
            logger.info("ARQ Redis closed")


arq_client = ARQClient()
