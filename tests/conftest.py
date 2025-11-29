import sys
import os
import asyncio
import time
from typing import AsyncGenerator, Generator, Dict, Any

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, Limits
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import inspect

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from app.config import settings
    from app.database.base import Base
    from app.database.sessions import get_async_session
    from app.main import app
except ImportError as e:
    print(f'Import error: {e}')
    print(f'Current Python path: {sys.path}')
    raise


TEST_DATABASE_URL = 'sqlite+aiosqlite:///:memory'

@pytest.fixture(scope='session')
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Глобальная фикстура event loop с оптимизацией """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope='session')
async def test_engine():
    engine  = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={'check_same_thread': False}
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.connect() as conn:
        transaction = await conn.begin()

        TestingSessionLocal = sessionmaker(
            bind=conn,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

        async with TestingSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()
        
        await transaction.rollback()


@pytest.fixture
def override_get_async_session(async_session: AsyncSession):
    """Инверсия зависимости для инъекции в приложение."""
    async def _override_get_async_session():
        yield async_session
    
    return _override_get_async_session


@pytest.fixture 
def sync_client(override_get_async_session) -> Generator[TestClient, None, None]:
    """Синхронный клиент для обычных тестов."""
    app.dependency_overrides[get_async_session] = override_get_async_session

    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(override_get_async_session) -> AsyncGenerator[AsyncClient, None]:
    """Асинхронный клиент для асинхронных тестов."""
    app.dependency_overrides[get_async_session] = override_get_async_session

    async with AsyncClient(
        app=app,
        base_url='http://test',
        limits=Limits(max_connections=1000, max_keepalive_connections=100)
    ) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def load_test_client(override_get_async_session) -> AsyncGenerator[AsyncClient, None]:
    """Клиент для нагрузочного тестирования."""
    app.dependency_overrides[get_async_session] = override_get_async_session
    async with AsyncClient(
        app=app,
        base_url="http://test",
        timeout=30.0,
        limits=Limits(max_connections=1000, max_keepalive_connections=100)
    ) as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def url_factory(async_session: AsyncSession):
    """Фабрика для создания тестовых URL."""
    from app.shortener.models import ShortURL
    from tests.utils.factories import ShortURLFactory

    created_urls = []

    async def _factory(**kwargs) -> ShortURL:
        url = await ShortURLFactory.create(async_session, **kwargs)
        created_urls.append(url)
        return url

    yield _factory

    for url in created_urls:
        await async_session.delete(url)
    await async_session.commit()


@pytest.fixture
def benchmark():
    """Контекст для бенчмаркинга."""
    class Benchmark:
        def __init__(self):
            self.times = []
        
        def __call__(self, func):
            def wrapper(*args, **kwargs):
                start = time.perf_counter()
                result = func(*args, **kwargs)
                end = time.perf_counter()
                self.times.append(end - start)
                return result
            return wrapper
        
        def get_stats(self) -> Dict[str, float]:
            if not self.times:
                return {}
            return {
                'min': min(self.times),
                'max': max(self.times),
                'avg': sum(self.times) / len(self.times),
                'total': sum(self.times),
                'count': len(self.times)
            }
    
    return Benchmark()


def pytest_configure(config):
    """Регистрация кастомных маркеров."""
    config.addinivalue_line(
        "markers", "slow: медленные тесты (миграции, производительность)"
    )
    config.addinivalue_line(
        "markers", "migrations: тесты миграций базы данных"
    )
    config.addinivalue_line(
        "markers", "performance: тесты производительности"
    )
    config.addinivalue_line(
        "markers", "security: тесты безопасности"
    )
    config.addinivalue_line(
        "markers", "integration: интеграционные тесты"
    )
    config.addinivalue_line(
        "markers", "load: нагрузочные тесты"
    )


@pytest.fixture
def assert_short_url_response():
    """Утилита для валидации ответов API."""
    def _assert_response(response_data: Dict[str, Any], expected_original_url: str = None):
        assert "short_code" in response_data
        assert "original_url" in response_data  
        assert "clicks" in response_data
        
        assert isinstance(response_data["short_code"], str)
        assert len(response_data["short_code"]) == settings.app.SHORT_CODE_LENGTH
        assert isinstance(response_data["clicks"], int)
        assert response_data["clicks"] >= 0
        
        if expected_original_url:
            assert response_data["original_url"] == expected_original_url
        
        assert response_data["short_code"].isalnum()
    
    return _assert_response

@pytest.fixture
def validate_error_response():
    """Утилита для валидации ошибок API."""
    def _validate(response, expected_status: int, expected_detail: str = None):
        assert response.status_code == expected_status
        
        data = response.json()
        assert "detail" in data
        
        if expected_detail:
            assert data["detail"] == expected_detail
        
        return data
    
    return _validate


@pytest.fixture
def sync_inspector(async_session: AsyncSession):
    def _get_inspector():
        return inspect(async_session.get_bind())
    return _get_inspector
