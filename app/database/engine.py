from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config import settings


def create_db_engine(connection_string: str) -> AsyncEngine:
    url = make_url(connection_string)

    timeout_kwargs = {
        'pool_timeout': settings.DATABASE_ENGINE_POOL_TIMEOUT,
        'pool_recycle': settings.DATABASE_ENGINE_POOL_RECYCLE,
        'pool_size': settings.DATABASE_ENGINE_POOL_SIZE,
        'max_overflow': settings.DATABASE_ENGINE_MAX_OVERFLOW,
        'pool_pre_ping': settings.DATABASE_ENGINE_POOL_PING,
    }

    return create_async_engine(url, **timeout_kwargs)


engine = create_db_engine(settings.SQLALCHEMY_DATABASE_URI)
