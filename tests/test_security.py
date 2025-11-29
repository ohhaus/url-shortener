import pytest


@pytest.mark.security
class TestSecurity:
    async def test_sql_injection_prevention(self, async_client):
        injection_attempts = [
            "abc123; DROP TABLE short_url;--",
            "abc' OR '1'='1",
            "'; DROP TABLE short_url; --",
        ]

        for attempt in injection_attempts:
            response = await async_client.get(f"/{attempt}")
            assert response.status_code == 404

    async def test_xss_prevention(self, async_client):
        xss_urls = [
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
        ]

        for url in xss_urls:
            response = await async_client.post("/", json={"original_url": url})
            assert response.status_code in [400, 422]

    async def test_path_traversal_prevention(self, async_client):
        traversal_attempts = [
            "../../etc/passwd",
            "..\\..\\windows\\system32\\config",
        ]

        for attempt in traversal_attempts:
            response = await async_client.get(f"/{attempt}")
            assert response.status_code == 404
