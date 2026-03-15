import asyncio
import ipaddress
import os
import socket
import sys
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cache.dependencies import get_cache_service
from src.cache.redis import redis_manager
from src.database.base import Base
from src.database.sessions import get_async_session
from src.main import app
from tests.utils.mocks import MockCacheService


_real_getaddrinfo = socket.getaddrinfo


def _mock_getaddrinfo(host, port, *args, **kwargs):
    try:
        ipaddress.ip_address(host)
        return _real_getaddrinfo(host, port, *args, **kwargs)
    except ValueError:
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port or 0))]


@pytest.fixture(scope="session", autouse=True)
def mock_dns():
    with patch("socket.getaddrinfo", side_effect=_mock_getaddrinfo):
        yield


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
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


@pytest.fixture
def mock_redis() -> AsyncMock:
    """Мок Redis для middleware и health."""
    redis = AsyncMock()
    redis.ping = AsyncMock()
    redis.incr = AsyncMock(return_value=1)
    redis.expire = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    redis.delete = AsyncMock()
    return redis


@pytest_asyncio.fixture
async def async_client(
    db_session: AsyncSession,
    mock_cache: MockCacheService,
    mock_redis: AsyncMock,
) -> AsyncGenerator[AsyncClient, None]:
    def override_get_session():
        yield db_session

    def override_get_cache():
        return mock_cache

    app.dependency_overrides[get_async_session] = override_get_session
    app.dependency_overrides[get_cache_service] = override_get_cache

    with (
        patch.object(redis_manager, "redis", mock_redis),
        patch("src.cache.redis.redis_manager.init", AsyncMock()),
        patch("src.cache.redis.redis_manager.close", AsyncMock()),
        patch("src.worker.client.arq_client.connect", AsyncMock()),
        patch("src.worker.client.arq_client.close", AsyncMock()),
        patch("src.worker.client.arq_client.enqueue_click", AsyncMock(return_value="job-id")),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def url_factory(db_session: AsyncSession):
    from tests.utils.factories import ShortURLFactory

    async def _factory(**kwargs):
        return await ShortURLFactory.create(db_session, **kwargs)

    return _factory


def pytest_configure(config):
    config.addinivalue_line("markers", "security: тесты безопасности")
