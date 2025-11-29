import pytest
from httpx import AsyncClient


class TestShortenerAPI:
    async def test_create_short_url(self, async_client: AsyncClient):
        response = await async_client.post("/", json={"original_url": "https://example.com"})
        assert response.status_code == 200
        
        data = response.json()
        assert "short_code" in data
        assert data["original_url"] == "https://example.com/"
        assert data["clicks"] == 0
    
    async def test_redirect_to_original(self, async_client: AsyncClient, url_factory):
        short_url = await url_factory(
            short_code="test123",
            original_url="https://redirect-target.com"
        )
        
        response = await async_client.get(f"/{short_url.short_code}", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == short_url.original_url
    
    async def test_get_short_url_info(self, async_client: AsyncClient, url_factory):
        short_url = await url_factory(clicks=5)
        
        response = await async_client.get(f"/{short_url.short_code}/info")
        assert response.status_code == 200
        
        data = response.json()
        assert data["short_code"] == short_url.short_code
        assert data["clicks"] == 5
    
    async def test_delete_short_url(self, async_client: AsyncClient, url_factory):
        short_url = await url_factory()
        
        response = await async_client.delete(f"/{short_url.short_code}")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"
        
        response = await async_client.get(f"/{short_url.short_code}/info")
        assert response.status_code == 404


class TestShortenerEdgeCases:
    async def test_create_duplicate_original_url(self, async_client: AsyncClient):
        url_data = {"original_url": "https://duplicate.example.com"}
        
        response1 = await async_client.post("/", json=url_data)
        response2 = await async_client.post("/", json=url_data)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        assert data1["short_code"] != data2["short_code"]
    
    async def test_nonexistent_short_code(self, async_client: AsyncClient):
        response = await async_client.get("/nonexistent")
        assert response.status_code == 404
    
    async def test_invalid_url(self, async_client: AsyncClient):
        response = await async_client.post("/", json={"original_url": "invalid-url"})
        assert response.status_code == 422
    
    async def test_empty_request_body(self, async_client: AsyncClient):
        response = await async_client.post("/", json={})
        assert response.status_code == 422
