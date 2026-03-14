import pytest


@pytest.mark.security
class TestSecurity:
    async def test_sql_injection_prevention(self, async_client):
        for attempt in [
            'abc123',  # валидный формат, но несуществующий
            'abc1230',
        ]:
            response = await async_client.get(f'/{attempt}')
            assert response.status_code == 404

    async def test_xss_in_url_rejected(self, async_client):
        for url in [
            "javascript:alert('xss')",
            'data:text/html,<script>alert(1)</script>',
        ]:
            response = await async_client.post('/', json={'original_url': url})
            assert response.status_code == 422

    async def test_nonexistent_code_returns_404(self, async_client):
        response = await async_client.get('/aaaaaa')
        assert response.status_code == 404

    async def test_invalid_url_schema_rejected(self, async_client):
        response = await async_client.post('/', json={'original_url': 'ftp://bad-schema.com'})
        assert response.status_code == 422
