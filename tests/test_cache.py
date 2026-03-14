import pytest
from unittest.mock import AsyncMock

from src.cache.keys import RedisKeys
from src.cache.redis import RedisManager
from src.cache.services import CacheService


class TestRedisKeys:
    def test_redirect_key(self):
        assert RedisKeys.redirect_key('abc123') == 'redirect:abc123'

    def test_click_key(self):
        assert RedisKeys.click_key('abc123') == 'clicks:abc123'

    def test_rate_limit_key(self):
        assert RedisKeys.rate_limit_key('127.0.0.1') == 'rate_limit:127.0.0.1'

    def test_real_time_stats(self):
        assert RedisKeys.real_time_stats() == 'real_time:stats'


class TestCacheService:
    @pytest.fixture
    def redis(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, redis):
        return CacheService(redis)

    async def test_cache_redirect_url(self, service, redis):
        await service.cache_redirect_url('abc123', 'https://example.com')
        redis.setex.assert_called_once()
        args = redis.setex.call_args[0]
        assert args[0] == 'redirect:abc123'
        assert args[2] == 'https://example.com'

    async def test_get_cached_redirect_url_hit(self, service, redis):
        redis.get.return_value = 'https://example.com'
        result = await service.get_cached_redirect_url('abc123')
        assert result == 'https://example.com'
        redis.get.assert_called_once_with('redirect:abc123')

    async def test_get_cached_redirect_url_miss(self, service, redis):
        redis.get.return_value = None
        result = await service.get_cached_redirect_url('abc123')
        assert result is None

    async def test_delete_cached_redirect(self, service, redis):
        await service.delete_cached_redirect('abc123')
        redis.delete.assert_called_once_with('redirect:abc123')


class TestRedisManager:
    async def test_get_raises_if_not_initialized(self):
        manager = RedisManager()
        with pytest.raises(RuntimeError, match='Redis not initialized'):
            manager.get()

    async def test_close_does_nothing_if_not_initialized(self):
        manager = RedisManager()
        await manager.close()

    async def test_init_and_get(self):
        from unittest.mock import patch, MagicMock

        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()

        with patch('src.cache.redis.Redis.from_url', return_value=mock_redis):
            manager = RedisManager()
            await manager.init()
            redis = manager.get()
            assert redis is mock_redis

    async def test_close_after_init(self):
        from unittest.mock import patch

        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()

        with patch('src.cache.redis.Redis.from_url', return_value=mock_redis):
            manager = RedisManager()
            await manager.init()
            await manager.close()
            mock_redis.close.assert_called_once()
