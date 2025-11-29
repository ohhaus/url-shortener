"""
Фабрики для создания тестовых данных.
"""
import random
import string
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.shortener.models import ShortURL
from app.shortener.services import ShortURLService


class ShortURLFactory:
    """Фабрика для создания тестовых коротких URL."""
    
    @staticmethod
    async def create(
        session: AsyncSession,
        short_code: Optional[str] = None,
        original_url: Optional[str] = None,
        clicks: int = 0,
        **kwargs
    ) -> ShortURL:
        """Создает тестовый ShortURL."""
        
        if short_code is None:
            short_code = await ShortURLFactory._generate_unique_code(session)
        
        if original_url is None:
            original_url = f"https://example-{random.randint(1000, 9999)}.com"
        
        short_url = ShortURL(
            short_code=short_code,
            original_url=original_url,
            clicks=clicks,
            **kwargs
        )
        
        session.add(short_url)
        await session.commit()
        await session.refresh(short_url)
        
        return short_url
    
    @staticmethod
    async def create_batch(
        session: AsyncSession,
        count: int,
        **kwargs
    ) -> list[ShortURL]:
        """Создает несколько тестовых ShortURL."""
        urls = []
        for i in range(count):
            url = await ShortURLFactory.create(
                session,
                original_url=f"https://batch-{i}.example.com",
                **kwargs
            )
            urls.append(url)
        return urls
    
    @staticmethod
    async def _generate_unique_code(session: AsyncSession, length: int = 6) -> str:
        """Генерирует уникальный код для тестов."""
        alphabet = string.ascii_letters + string.digits
        while True:
            code = ''.join(random.choices(alphabet, k=length))
            existing = await session.get(ShortURL, code)
            if not existing:
                return code


class URLDataFactory:
    """Фабрика тестовых данных для URL."""
    
    @staticmethod
    def valid_url_data() -> Dict[str, Any]:
        """Валидные данные для создания URL."""
        return {
            "original_url": f"https://test-{random.randint(1000, 9999)}.com"
        }
    
    @staticmethod
    def invalid_url_data() -> Dict[str, Any]:
        """Невалидные данные для создания URL."""
        return {
            "original_url": "not-a-valid-url"
        }
    
    @staticmethod
    def edge_case_urls() -> list[Dict[str, Any]]:
        """Крайние случаи для тестирования."""
        return [
            {"original_url": "http://localhost:3000"},  # Local URL
            {"original_url": "https://sub.domain.co.uk/path?query=param#fragment"},  # Complex URL
            {"original_url": "https://192.168.1.1:8080/api/v1"},  # IP URL
        ]
