from unittest.mock import AsyncMock, patch

from httpx import AsyncClient

from src.cache.redis import redis_manager


class TestRateLimitMiddleware:
    async def test_under_limit_passes(self, async_client: AsyncClient):
        response = await async_client.post("/", json={"original_url": "https://example.com"})
        assert response.status_code in (201, 409)

    async def test_over_limit_returns_429(self, async_client: AsyncClient):
        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=61)
        mock_redis.expire = AsyncMock()

        with patch.object(redis_manager, "redis", mock_redis):
            response = await async_client.post(
                "/", json={"original_url": "https://overlimit.com"}
            )

        assert response.status_code == 429
        assert "Too many requests" in response.json()["detail"]

    async def test_rate_limit_does_not_apply_to_get(self, async_client: AsyncClient):
        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=9999)

        with patch.object(redis_manager, "redis", mock_redis):
            response = await async_client.get("/nonexist")

        assert response.status_code == 404

    async def test_rate_limit_redis_failure_does_not_block(self, async_client: AsyncClient):
        with patch.object(redis_manager, "redis", None):
            response = await async_client.post(
                "/", json={"original_url": "https://example.com"}
            )

        assert response.status_code in (201, 409)
