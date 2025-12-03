import logging

from arq.connections import RedisSettings
from sqlalchemy import update

from src.config import settings
from src.database.sessions import AsyncSessionLocal
from src.shortener.models import ShortURL


logger = logging.getLogger(__name__)

async def record_click(ctx, short_code: str) -> bool:
    logger.info(f'Recording click for short_code: {short_code}')
    try:
        async with AsyncSessionLocal() as session:
            stmt = (
                update(ShortURL)
                .where(ShortURL.short_code == short_code)
                .values(clicks=ShortURL.clicks + 1)
            )
            await session.execute(stmt)
            await session.commit()
        return True
    except Exception as e:
        logger.error(f'Failed to record click: {e}')
        return False


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(settings.worker.REDIS_DSN)
    functions = [record_click]
    job_timeout = 30
    max_jobs = 10
    max_tries = 3
