from unittest.mock import AsyncMock, patch

from src.cache.redis import redis_manager


class TestHealthCheck:
    async def test_health_all_ok(self, async_client):
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()

        with patch.object(redis_manager, "redis", mock_redis):
            response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["checks"]["database"] == "ok"
        assert data["checks"]["redis"] == "ok"

    async def test_health_db_unavailable(self, async_client):
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()

        with patch.object(redis_manager, "redis", mock_redis):
            with patch(
                "src.health.AsyncSession.execute", AsyncMock(side_effect=Exception("DB down"))
            ):
                response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["checks"]["database"] == "unavailable"
        assert data["status"] == "degraded"

    async def test_health_redis_unavailable(self, async_client):
        # redis=None → get() кинет RuntimeError → health поймает → "unavailable"
        with patch.object(redis_manager, "redis", None):
            response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["checks"]["redis"] == "unavailable"
        assert data["status"] == "degraded"
