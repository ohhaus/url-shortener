from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.cache.dependencies import get_cache_service
from src.database.sessions import get_async_session
from src.shortener.dependencies import get_short_url_by_code
from src.shortener.exceptions import ShortCodeAlreadyExists
from src.shortener.models import ShortURL
from src.shortener.schemas import (
    ShortURLCreate,
    ShortURLDeleteResponse,
    ShortURLResponse,
)
from src.shortener.services import ShortURLService


router = APIRouter()


@router.post('/', response_model=ShortURLResponse)
async def create_short_url(
    data: ShortURLCreate,
    session: AsyncSession = Depends(get_async_session),
    cache=Depends(get_cache_service),
):
    """Создает новую короткую ссылку."""
    try:
        short_url = await ShortURLService.create_short_url(
            session=session,
            cache=cache,
            original_url=data.original_url,
        )
        return ShortURLResponse.model_validate(short_url)

    except ShortCodeAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.get('/{short_code}')
async def redirect_to_original(
    short_url: ShortURL = Depends(get_short_url_by_code),
    session: AsyncSession = Depends(get_async_session),
):
    """Перенаправляет по короткой ссылке."""
    await ShortURLService.increment_clicks(short_url.short_code)
    return RedirectResponse(url=short_url.original_url, status_code=status.HTTP_302_FOUND)


@router.get('/{short_code}/info', response_model=ShortURLResponse)
async def get_short_url_info(
    short_url: ShortURL = Depends(get_short_url_by_code),
):
    """Возвращает информацию о короткой ссылке."""
    return ShortURLResponse(
        short_code=short_url.short_code,
        original_url=short_url.original_url,
        clicks=short_url.clicks,
    )


@router.delete('/{short_code}', response_model=ShortURLDeleteResponse)
async def delete_short_url(
    short_url: ShortURL = Depends(get_short_url_by_code),
    session: AsyncSession = Depends(get_async_session),
    cache=Depends(get_cache_service),
):
    """Удаляет короткую ссылку."""
    await ShortURLService.delete_short_url(session, short_url)
    return ShortURLDeleteResponse(short_code=short_url.short_code)
