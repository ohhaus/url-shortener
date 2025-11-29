import pytest

from app.shortener.exceptions import ShortURLNotFound
from app.shortener.services import ShortURLService


class TestShortURLService:
    async def test_create_short_url(self, db_session):
        original_url = "https://service-test.com"

        short_url = await ShortURLService.create_short_url(db_session, original_url)

        assert short_url.original_url == original_url
        assert len(short_url.short_code) == 6
        assert short_url.clicks == 0

    async def test_get_by_code(self, db_session, url_factory):
        short_url = await url_factory(short_code="test123")

        found = await ShortURLService.get_by_code(db_session, "test123")
        assert found.short_code == "test123"

    async def test_get_by_code_not_found(self, db_session):
        with pytest.raises(ShortURLNotFound):
            await ShortURLService.get_by_code(db_session, "nonexistent")

    async def test_increment_clicks(self, db_session, url_factory):
        short_url = await url_factory(clicks=5)

        await ShortURLService.increment_clicks(db_session, short_url)
        assert short_url.clicks == 6

    async def test_delete_short_url(self, db_session, url_factory):
        short_url = await url_factory()

        await ShortURLService.delete_short_url(db_session, short_url)

        with pytest.raises(ShortURLNotFound):
            await ShortURLService.get_by_code(db_session, short_url.short_code)
