import pytest

from app.shortener.services import ShortURLService
from app.shortener.exceptions import ShortURLNotFound


class TestShortURLService:
    """Тесты сервиса коротких URL."""
    
    async def test_create_short_url_success(self, async_session):
        """Тест успешного создания короткой ссылки."""
        original_url = "https://service-test.com"
        
        short_url = await ShortURLService.create_short_url(async_session, original_url)
        
        assert short_url.original_url == original_url
        assert len(short_url.short_code) == 6
        assert short_url.clicks == 0
    
    async def test_get_by_code_success(self, async_session, url_factory):
        """Тест успешного получения ссылки по коду."""
        short_url = await url_factory(short_code="gettest")
        
        found_url = await ShortURLService.get_by_code(async_session, "gettest")
        
        assert found_url.short_code == "gettest"
        assert found_url.original_url == short_url.original_url
    
    async def test_get_by_code_not_found(self, async_session):
        """Тест поиска несуществующей ссылки."""
        with pytest.raises(ShortURLNotFound):
            await ShortURLService.get_by_code(async_session, "nonexistent")
    
    async def test_increment_clicks(self, async_session, url_factory):
        """Тест увеличения счетчика кликов."""
        short_url = await url_factory(clicks=5)
        
        await ShortURLService.increment_clicks(async_session, short_url)
        
        assert short_url.clicks == 6
    
    async def test_delete_short_url(self, async_session, url_factory):
        """Тест удаления короткой ссылки."""
        short_url = await url_factory()
        
        await ShortURLService.delete_short_url(async_session, short_url)
        
        with pytest.raises(ShortURLNotFound):
            await ShortURLService.get_by_code(async_session, short_url.short_code)
