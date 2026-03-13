import asyncio
import os
import sys
from typing import AsyncGenerator, Generator

from fakeredis.aioredis import FakeRedis
from fastapi.testclient import TestClient
from httpx import AsyncClient
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import settings
from src.database.base import Base
from src.database.sessions import get_async_session
from src.main import app
from src.cache.dependencies import get_cache_service
from src.cache.services import CacheService
from src.cache.redis import redis_manager


# ---------------------------
# GLOBAL EVENT LOOP (pytest)
# ---------------------------
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Создаём event loop для pytest-asyncio (scope=session)."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------
# DB ENGINE
# ---------------------------
@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Создаёт in-memory SQLite и прогоняет миграции."""
    engine = create_async_engine(
        settings.database.TEST_URL,
        echo=False,
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()


# ---------------------------
# DB SESSION
# ---------------------------
@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Откатывает транзакции после каждого теста."""
    async with test_engine.connect() as conn:
        trans = await conn.begin()

        Session = sessionmaker(
            bind=conn,
            class_=AsyncSession,
            expire_on_commit=False
        )

        async with Session() as session:
            yield session

        await trans.rollback()


# ---------------------------
# FAKE REDIS
# ---------------------------
@pytest_asyncio.fixture
async def fake_redis_async():

    redis = FakeRedis()
    redis_manager.redis = redis

    yield redis

    redis_manager.redis = None



# ---------------------------
# SYNC TEST CLIENT (если нужен)
# ---------------------------
@pytest.fixture
def client(db_session: AsyncSession):
    """Sync TestClient для единичных sync-тестов."""
    def override_get_session():
        yield db_session

    app.dependency_overrides[get_async_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ---------------------------
# ASYNC TEST CLIENT
# ---------------------------
@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession, fake_redis_async) -> AsyncGenerator[AsyncClient, None]:
    """Правильный AsyncClient с подменой DB и Redis."""

    def override_get_session():
        yield db_session

    async def override_cache():
        return CacheService(redis_manager.redis)

    app.dependency_overrides[get_async_session] = override_get_session
    app.dependency_overrides[get_cache_service] = override_cache

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# ---------------------------
# FACTORY
# ---------------------------
@pytest_asyncio.fixture
async def url_factory(db_session: AsyncSession):
    from tests.utils.factories import ShortURLFactory

    async def _factory(**kwargs):
        return await ShortURLFactory.create(db_session, **kwargs)

    return _factory


# ---------------------------
# PYTEST MARKERS
# ---------------------------
def pytest_configure(config):
    config.addinivalue_line("markers", "security: тесты безопасности")
