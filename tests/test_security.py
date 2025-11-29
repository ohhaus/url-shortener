import pytest


@pytest.mark.security
class TestSecurity:
    """Тесты безопасности."""
    
    async def test_sql_injection_prevention(
        self,
        async_client,
    ):
        """Защита от SQL инъекций через short_code."""
        injection_attempts = [
            "abc123; DROP TABLE short_url;--",
            "abc' OR '1'='1",
            'abc123"; DELETE FROM short_url; --',
            "'; EXEC xp_cmdshell('del *.*');--",
            "` OR 1=1--",
            "UNION SELECT * FROM users--",
        ]
        
        for attempt in injection_attempts:
            response = await async_client.get(f"/{attempt}")
            assert response.status_code == 404
            if response.status_code != 404:
                response_text = response.text.lower()
                assert "sql" not in response_text
                assert "syntax" not in response_text

    async def test_xss_prevention(
        self,
        async_client,
    ):
        """Защита от XSS в URL."""
        xss_attempts = [
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "vbscript:msgbox('xss')",
            "jAvaScRiPt:alert('xss')",
            "&#106;&#97;&#118;&#97;&#115;&#99;&#114;&#105;&#112;&#116;:alert('xss')",  # encoded
        ]
        
        for attempt in xss_attempts:
            response = await async_client.post("/", json={"original_url": attempt})
            assert response.status_code in [422, 400]

    async def test_url_length_limits(
        self,
        async_client,
    ):
        """Ограничения длины URL."""
        test_cases = [
            ("https://normal.com", 200),
            ("https://example.com/" + "a" * 100, 200),
            ("https://example.com/" + "a" * 10000, 422),
        ]
        
        for url, expected_status in test_cases:
            response = await async_client.post("/", json={"original_url": url})
            assert response.status_code == expected_status, f"URL: {url}"

    async def test_path_traversal_prevention(
        self,
        async_client,
    ):
        """Защита от path traversal атак."""
        traversal_attempts = [
            "../../etc/passwd",
            "..\\..\\windows\\system32\\config",
            "%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//etc/passwd",
        ]
        
        for attempt in traversal_attempts:
            response = await async_client.get(f"/{attempt}")
            assert response.status_code == 404

    async def test_protocol_validation(
        self,
        async_client,
    ):
        """Валидация протоколов URL."""
        dangerous_protocols = [
            "ftp://example.com",
            "file:///etc/passwd",
            "gopher://example.com",
            "telnet://example.com",
        ]
        
        for protocol_url in dangerous_protocols:
            response = await async_client.post("/", json={"original_url": protocol_url})
            assert response.status_code in [422, 400]

    async def test_malformed_requests(
        self,
        async_client,
    ):
        """Обработка некорректных запросов."""
        response = await async_client.post(
            "/", 
            content="{ invalid json }",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]
        
        response = await async_client.post(
            "/",
            content='{"original_url": "https://example.com"}',
            headers={"Content-Type": "text/plain"}
        )
        assert response.status_code in [400, 415, 422]
