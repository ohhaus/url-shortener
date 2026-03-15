from arq.connections import RedisSettings
from loguru import logger
from sqlalchemy import update

from src.config import settings
from src.database.sessions import AsyncSessionLocal
from src.shortener.models import ShortURL


async def record_click(ctx, short_code: str) -> bool:
    logger.info("Recording click", extra={"short_code": short_code})
    async with AsyncSessionLocal() as session:
        stmt = (
            update(ShortURL)
            .where(ShortURL.short_code == short_code)
            .values(clicks=ShortURL.clicks + 1)
        )
        await session.execute(stmt)
        await session.commit()

    logger.info("Click recorded", extra={"short_code": short_code})
    return True


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(settings.worker.REDIS_DSN)
    functions = [record_click]
    job_timeout = 30
    max_jobs = 10
    max_tries = 3
