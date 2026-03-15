from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from src.shortener.exceptions import ShortCodeAlreadyExists, ShortURLNotFound
from src.shortener.services import ShortURLService


class TestShortURLServiceCreate:
    async def test_create_returns_short_url(self, db_session, mock_cache):
        service = ShortURLService(db_session, mock_cache)
        short_url = await service.create("https://example.com", deduplicate=False)
        assert short_url.original_url == "https://example.com"
        assert len(short_url.short_code) == 6
        assert short_url.clicks == 0

    async def test_create_caches_url(self, db_session, mock_cache):
        service = ShortURLService(db_session, mock_cache)
        short_url = await service.create("https://cached-on-create.com", deduplicate=False)
        cached = await mock_cache.get_cached_redirect_url(short_url.short_code)
        assert cached == "https://cached-on-create.com"

    async def test_create_retries_on_collision(self, db_session, mock_cache):
        service = ShortURLService(db_session, mock_cache)
        commit_calls = 0
        original_commit = db_session.commit

        async def flaky_commit():
            nonlocal commit_calls
            commit_calls += 1
            if commit_calls == 1:
                raise IntegrityError(None, None, None)
            return await original_commit()

        with patch.object(db_session, "commit", flaky_commit):
            short_url = await service.create("https://retry.com", deduplicate=False)

        assert short_url is not None
        assert commit_calls == 2

    async def test_create_raises_after_max_attempts(self, db_session, mock_cache):
        service = ShortURLService(db_session, mock_cache)
        with patch.object(
            db_session,
            "commit",
            AsyncMock(side_effect=IntegrityError(None, None, None)),
        ):
            with pytest.raises(ShortCodeAlreadyExists):
                await service.create("https://exhausted.com", deduplicate=False)


class TestShortURLServiceDeduplicate:
    async def test_deduplicate_default_is_true(self, db_session, mock_cache, url_factory):
        existing = await url_factory(
            short_code="dedup03",
            original_url="https://dedup-default.com",
        )
        service = ShortURLService(db_session, mock_cache)
        # Вызов без явного deduplicate — должен вернуть существующий
        result = await service.create("https://dedup-default.com")
        assert result.short_code == existing.short_code

    async def test_deduplicate_true_returns_existing(
        self, db_session, mock_cache, url_factory
    ):
        existing = await url_factory(
            short_code="dedup01",
            original_url="https://dedup.com",
        )
        service = ShortURLService(db_session, mock_cache)
        result = await service.create("https://dedup.com", deduplicate=True)
        assert result.short_code == existing.short_code

    async def test_deduplicate_true_creates_new_if_not_exists(self, db_session, mock_cache):
        service = ShortURLService(db_session, mock_cache)
        result = await service.create("https://new-dedup.com", deduplicate=True)
        assert result is not None
        assert len(result.short_code) == 6

    async def test_deduplicate_false_creates_new_code(
        self, db_session, mock_cache, url_factory
    ):
        await url_factory(short_code="dedup02", original_url="https://no-dedup.com")
        service = ShortURLService(db_session, mock_cache)
        result = await service.create("https://no-dedup.com", deduplicate=False)
        assert result.short_code != "dedup02"


class TestShortURLServiceGetOriginalUrl:
    async def test_cache_hit_skips_db(self, db_session, mock_cache):
        await mock_cache.cache_redirect_url("cached1", "https://from-cache.com")
        service = ShortURLService(db_session, mock_cache)
        url = await service.get_original_url("cached1")
        assert url == "https://from-cache.com"

    async def test_cache_miss_fetches_from_db(self, db_session, mock_cache, url_factory):
        await url_factory(short_code="dbonly1", original_url="https://from-db.com")
        service = ShortURLService(db_session, mock_cache)
        url = await service.get_original_url("dbonly1")
        assert url == "https://from-db.com"

    async def test_cache_miss_populates_cache(self, db_session, mock_cache, url_factory):
        await url_factory(short_code="dbonly2", original_url="https://populate.com")
        service = ShortURLService(db_session, mock_cache)
        await service.get_original_url("dbonly2")
        cached = await mock_cache.get_cached_redirect_url("dbonly2")
        assert cached == "https://populate.com"

    async def test_not_found_raises(self, db_session, mock_cache):
        service = ShortURLService(db_session, mock_cache)
        with pytest.raises(ShortURLNotFound):
            await service.get_original_url("missing0")


class TestShortURLServiceGetByCode:
    async def test_get_existing(self, db_session, mock_cache, url_factory):
        await url_factory(short_code="getme01")
        service = ShortURLService(db_session, mock_cache)
        result = await service.get_by_code("getme01")
        assert result.short_code == "getme01"

    async def test_get_not_found(self, db_session, mock_cache):
        service = ShortURLService(db_session, mock_cache)
        with pytest.raises(ShortURLNotFound):
            await service.get_by_code("nope0000")


class TestShortURLServiceDelete:
    async def test_delete_removes_from_db(self, db_session, mock_cache, url_factory):
        short_url = await url_factory(short_code="del0010")
        service = ShortURLService(db_session, mock_cache)
        await service.delete(short_url)
        with pytest.raises(ShortURLNotFound):
            await service.get_by_code("del0010")

    async def test_delete_invalidates_cache(self, db_session, mock_cache, url_factory):
        short_url = await url_factory(short_code="del0011", original_url="https://del.com")
        await mock_cache.cache_redirect_url("del0011", "https://del.com")
        service = ShortURLService(db_session, mock_cache)
        await service.delete(short_url)
        assert await mock_cache.get_cached_redirect_url("del0011") is None


class TestShortURLServiceIncrementClicks:
    async def test_enqueues_click(self, db_session, mock_cache):
        service = ShortURLService(db_session, mock_cache)
        with patch(
            "src.worker.client.arq_client.enqueue_click",
            AsyncMock(return_value="job-id"),
        ) as mock_enqueue:
            await service.increment_clicks("abc123")
            mock_enqueue.assert_called_once_with("abc123")


class TestGenerateCode:
    def test_generate_code_length(self):
        code = ShortURLService._generate_code()
        assert len(code) == 6

    def test_generate_code_charset(self):
        import string

        allowed = set(string.ascii_letters + string.digits)
        for _ in range(20):
            code = ShortURLService._generate_code()
            assert all(c in allowed for c in code)
