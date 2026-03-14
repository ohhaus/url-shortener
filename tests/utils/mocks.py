class MockCacheService:
    """In-memory реализация CacheService для тестов."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def cache_redirect_url(self, short_code: str, original_url: str) -> None:
        self._store[short_code] = original_url

    async def get_cached_redirect_url(self, short_code: str) -> str | None:
        return self._store.get(short_code)

    async def delete_cached_redirect(self, short_code: str) -> None:
        self._store.pop(short_code, None)
