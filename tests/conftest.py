import asyncio
import os
import sys
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cache.dependencies import get_cache_service
from src.database.base import Base
from src.database.sessions import get_async_session
from src.main import app
from tests.utils.mocks import MockCacheService


@pytest.fixture(scope='session')
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope='session')
async def test_engine():
    engine = create_async_engine(
        'sqlite+aiosqlite:///:memory:',
        echo=False,
        poolclass=StaticPool,
        connect_args={'check_same_thread': False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.connect() as conn:
        transaction = await conn.begin()
        Session = async_sessionmaker(bind=conn, class_=AsyncSession, expire_on_commit=False)
        async with Session() as session:
            yield session
        await transaction.rollback()


@pytest.fixture
def mock_cache() -> MockCacheService:
    return MockCacheService()


@pytest_asyncio.fixture
async def async_client(
    db_session: AsyncSession,
    mock_cache: MockCacheService,
) -> AsyncGenerator[AsyncClient, None]:
    def override_get_session():
        yield db_session

    def override_get_cache():
        return mock_cache

    app.dependency_overrides[get_async_session] = override_get_session
    app.dependency_overrides[get_cache_service] = override_get_cache

    with (
        patch('src.cache.redis.redis_manager.init', AsyncMock()),
        patch('src.cache.redis.redis_manager.close', AsyncMock()),
        patch('src.worker.client.arq_client.connect', AsyncMock()),
        patch('src.worker.client.arq_client.close', AsyncMock()),
        patch('src.worker.client.arq_client.enqueue_click', AsyncMock(return_value='job-id')),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url='http://test'
        ) as client:
            yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def url_factory(db_session: AsyncSession):
    from tests.utils.factories import ShortURLFactory

    async def _factory(**kwargs) -> ShortURLFactory:
        return await ShortURLFactory.create(db_session, **kwargs)

    return _factory


def pytest_configure(config):
    config.addinivalue_line('markers', 'security: тесты безопасности')
