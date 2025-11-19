from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.database.engine import engine


AsyncSessionLocal = async_sessionmaker(bind=engine, cls_=AsyncSession)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Генератор асинхронных сессий для работы с БД.

    Yields:
        Асинхронная сессия SQLAlchemy.
    """
    async with AsyncSessionLocal() as async_session:
        try:
            yield async_session
        finally:
            await async_session.close()
