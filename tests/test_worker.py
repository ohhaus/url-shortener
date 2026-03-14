import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.worker.client import ARQClient


class TestARQClient:
    async def test_connect_initializes_pool(self):
        client = ARQClient()
        mock_pool = AsyncMock()
        with patch('src.worker.client.create_pool', AsyncMock(return_value=mock_pool)):
            await client.connect()
        assert client.pool is mock_pool

    async def test_enqueue_click_success(self):
        client = ARQClient()
        mock_job = MagicMock()
        mock_job.job_id = 'test-job-id'
        mock_pool = AsyncMock()
        mock_pool.enqueue_job.return_value = mock_job
        client.pool = mock_pool

        result = await client.enqueue_click('abc123')

        assert result == 'test-job-id'
        mock_pool.enqueue_job.assert_called_once_with('record_click', 'abc123')

    async def test_enqueue_click_returns_none_when_job_is_none(self):
        client = ARQClient()
        mock_pool = AsyncMock()
        mock_pool.enqueue_job.return_value = None
        client.pool = mock_pool

        result = await client.enqueue_click('abc123')
        assert result is None

    async def test_enqueue_click_no_pool_logs_warning(self):
        client = ARQClient()
        assert client.pool is None
        result = await client.enqueue_click('abc123')
        assert result is None

    async def test_close_closes_pool(self):
        client = ARQClient()
        mock_pool = AsyncMock()
        client.pool = mock_pool

        await client.close()
        mock_pool.close.assert_called_once()

    async def test_close_no_pool_does_nothing(self):
        client = ARQClient()
        await client.close()  # не должен упасть


class TestRecordClick:
    async def test_record_click_success(self, db_session, url_factory):
        from src.worker.tasks import record_click

        await url_factory(short_code='clk0001', clicks=3)

        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=db_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch('src.worker.tasks.AsyncSessionLocal', mock_factory):
            result = await record_click({}, 'clk0001')

        assert result is True

    async def test_record_click_updates_counter(self, db_session, url_factory):
        from sqlalchemy import select
        from src.shortener.models import ShortURL
        from src.worker.tasks import record_click

        await url_factory(short_code='clk0002', clicks=0)

        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=db_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch('src.worker.tasks.AsyncSessionLocal', mock_factory):
            await record_click({}, 'clk0002')

        result = await db_session.execute(
            select(ShortURL).where(ShortURL.short_code == 'clk0002')
        )
        updated = result.scalar_one()
        assert updated.clicks == 1
