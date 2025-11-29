import pytest
from httpx import AsyncClient

from app.shortener.models import ShortURL


class TestShortenerAPI:

    async def test_create_short_url_success(
        self,
        async_client: AsyncClient,
        url_factory,
        assert_short_url_response
    ):
        """Тест успешного создания ссылки."""
        url_data = {'original_url': 'https://example.com/'}

        response = await async_client.post('/', json=url_data)

        assert response.status_code == 200
        data = response.json()
        assert_short_url_response(data, str(url_data['original_url']))
    
    async def test_redirect_to_original(
        self,
        async_client: AsyncClient,
        url_factory
    ):
        """Тест редиректа по короткой ссылке."""
        short_url = await url_factory(
            short_code='test123',
            original_url='https://redirect-target.com'
        )

        response = await async_client.get(
            f'/{short_url.short_code}',
            follow_redirects=False
        )
        
        assert response.status_code == 302
        assert response.headers['location'] == short_url.original_url
    
    async def test_get_short_url_info(
        self,
        async_client: AsyncClient,
        url_factory,
        assert_short_url_response
    ):
        """Тест получения информации о короткой ссылки."""
        short_url = await url_factory(clicks=5)

        response = await async_client.get(f'/{short_url.short_code}/info')

        assert response.status_code == 200
        data = response.json()
        assert_short_url_response(data, short_url.original_url)
        assert data['clicks'] == 5
    
    async def test_delete_short_url(
        self,
        async_client: AsyncClient,
        url_factory
    ):
        """Тест удаления короткой ссылки."""
        short_url = await url_factory()
        
        response = await async_client.delete(f"/{short_url.short_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"
        assert data["short_code"] == short_url.short_code
        
        get_response = await async_client.get(f"/{short_url.short_code}/info")
        assert get_response.status_code == 404


class TestShortenerEdgeCases:

    async def test_create_duplicate_url(
            self,
            async_client: AsyncClient,
            url_factory
    ):
        """Тест создания дубликата URL (должен создавать разные коды)."""
        url_data = {'original_url': 'https://duplicate.example.com'}

        response1 = await async_client.post('/', json=url_data)
        response2 = await async_client.post('/', json=url_data)

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        assert data1['short_code'] != data2['short_code']

    async def test_nonexistent_short_code(
        self,
        async_client: AsyncClient,
        validate_error_response
    ):
        """Тест обращения к несуществуюшему коду."""
        response = await async_client.get('/nonexistent')

        validate_error_response(response, 404)

    async def test_empty_request_body(
        self,
        async_client: AsyncClient,
    ):
        """Тест пустого тела запроса."""
        response = await async_client.post("/", json={})
        
        assert response.status_code == 422

    async def test_malformed_url(
        self,
        async_client: AsyncClient,
    ):
        """Тест некорректного URL."""
        response = await async_client.post("/", json={"original_url": "not-a-valid-url"})
        
        assert response.status_code == 422
