from httpx import AsyncClient


class TestShortenerAPI:
    async def test_create_short_url(self, async_client: AsyncClient):
        response = await async_client.post("/", json={"original_url": "https://example.com"})
        assert response.status_code == 201
        data = response.json()
        assert "short_code" in data
        assert "example.com" in data["original_url"]
        assert data["clicks"] == 0

    async def test_create_short_url_invalid_url(self, async_client: AsyncClient):
        response = await async_client.post("/", json={"original_url": "invalid-url"})
        assert response.status_code == 422

    async def test_create_short_url_empty_body(self, async_client: AsyncClient):
        response = await async_client.post("/", json={})
        assert response.status_code == 422

    async def test_redirect_to_original(self, async_client: AsyncClient, url_factory):
        short_url = await url_factory(
            short_code="redir01",
            original_url="https://redirect-target.com",
        )
        response = await async_client.get(f"/{short_url.short_code}", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == short_url.original_url

    async def test_redirect_not_found(self, async_client: AsyncClient):
        response = await async_client.get("/nonexist", follow_redirects=False)
        assert response.status_code == 404

    async def test_get_short_url_info(self, async_client: AsyncClient, url_factory):
        short_url = await url_factory(short_code="info001", clicks=5)
        response = await async_client.get(f"/{short_url.short_code}/info")
        assert response.status_code == 200
        data = response.json()
        assert data["short_code"] == short_url.short_code
        assert data["clicks"] == 5

    async def test_get_short_url_info_not_found(self, async_client: AsyncClient):
        response = await async_client.get("/missing0/info")
        assert response.status_code == 404

    async def test_delete_short_url(self, async_client: AsyncClient, url_factory):
        short_url = await url_factory(short_code="del0001")
        response = await async_client.delete(f"/{short_url.short_code}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"
        assert data["short_code"] == short_url.short_code

    async def test_delete_removes_url(self, async_client: AsyncClient, url_factory):
        short_url = await url_factory(short_code="del0002")
        await async_client.delete(f"/{short_url.short_code}")
        response = await async_client.get(f"/{short_url.short_code}/info")
        assert response.status_code == 404

    async def test_delete_not_found(self, async_client: AsyncClient):
        response = await async_client.delete("/missing0")
        assert response.status_code == 404


class TestShortenerEdgeCases:
    async def test_duplicate_original_url_gets_same_code_by_default(
        self, async_client: AsyncClient
    ):
        url_data = {"original_url": "https://duplicate.example.com"}
        response1 = await async_client.post("/", json=url_data)
        response2 = await async_client.post("/", json=url_data)
        assert response1.status_code == 201
        assert response2.status_code == 201
        # По умолчанию deduplicate=True — одинаковый код
        assert response1.json()["short_code"] == response2.json()["short_code"]

    async def test_no_deduplicate_creates_different_codes(self, async_client: AsyncClient):
        url_data = {"original_url": "https://no-dedup.example.com"}
        response1 = await async_client.post("/?deduplicate=false", json=url_data)
        response2 = await async_client.post("/?deduplicate=false", json=url_data)
        assert response1.status_code == 201
        assert response2.status_code == 201
        # При deduplicate=False — всегда новый код
        assert response1.json()["short_code"] != response2.json()["short_code"]

    async def test_deduplicate_true_returns_same_code(self, async_client: AsyncClient):
        url_data = {"original_url": "https://dedup.example.com"}
        response1 = await async_client.post("/?deduplicate=true", json=url_data)
        response2 = await async_client.post("/?deduplicate=true", json=url_data)
        assert response1.status_code == 201
        assert response2.status_code == 201
        assert response1.json()["short_code"] == response2.json()["short_code"]

    async def test_redirect_uses_cache(
        self, async_client: AsyncClient, url_factory, mock_cache
    ):
        short_url = await url_factory(
            short_code="cache01",
            original_url="https://original.com",
        )
        await mock_cache.cache_redirect_url("cache01", "https://original.com")
        response = await async_client.get(f"/{short_url.short_code}", follow_redirects=False)
        assert response.status_code == 302
