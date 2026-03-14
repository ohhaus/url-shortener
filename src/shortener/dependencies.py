from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.cache.dependencies import get_cache_service
from src.cache.services import CacheService
from src.database.sessions import get_async_session
from src.shortener.exceptions import ShortURLNotFound
from src.shortener.models import ShortURL
from src.shortener.services import ShortURLService


def get_short_url_service(
    session: AsyncSession = Depends(get_async_session),
    cache: CacheService = Depends(get_cache_service),
) -> ShortURLService:
    return ShortURLService(session, cache)


async def get_short_url_by_code(
    short_code: str,
    service: ShortURLService = Depends(get_short_url_service),
) -> ShortURL:
    try:
        return await service.get_by_code(short_code)
    except ShortURLNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
