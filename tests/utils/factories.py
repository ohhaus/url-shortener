import random
import string

from sqlalchemy.ext.asyncio import AsyncSession

from src.shortener.models import ShortURL


class ShortURLFactory:
    @staticmethod
    async def create(
        session: AsyncSession,
        short_code: str = None,
        original_url: str = None,
        clicks: int = 0,
    ) -> ShortURL:
        if short_code is None:
            short_code = await ShortURLFactory._generate_unique_code(session)

        if original_url is None:
            original_url = f"https://example-{random.randint(1000, 9999)}.com"

        short_url = ShortURL(
            short_code=short_code,
            original_url=original_url,
            clicks=clicks,
        )

        session.add(short_url)
        await session.commit()
        await session.refresh(short_url)

        return short_url

    @staticmethod
    async def _generate_unique_code(session: AsyncSession, length: int = 6) -> str:
        alphabet = string.ascii_letters + string.digits
        while True:
            code = ''.join(random.choices(alphabet, k=length))
            existing = await session.get(ShortURL, code)
            if not existing:
                return code


class URLDataFactory:
    @staticmethod
    def valid_url_data() -> dict:
        return {"original_url": f"https://test-{random.randint(1000, 9999)}.com"}

    @staticmethod
    def invalid_url_data() -> dict:
        return {"original_url": "not-a-valid-url"}
