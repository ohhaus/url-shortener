from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.sessions import get_async_session
from app.shortener.dependencies import get_short_url_by_code
from app.shortener.exceptions import ShortCodeAlreadyExists
from app.shortener.models import ShortURL
from app.shortener.schemas import (
    ShortURLCreate,
    ShortURLDeleteResponse,
    ShortURLResponse,
)
from app.shortener.services import ShortURLService


router = APIRouter(prefix='/shorten', tags=['Shorten'])


@router.post('/', response_model=ShortURLResponse)
async def create_short_url(
    data: ShortURLCreate, session: AsyncSession = Depends(get_async_session)
):
    """Создает новую короткую ссылку."""
    try:
        short_url = await ShortURLService.create_short_url(
            session=session,
            original_url=data.original_url,
            short_code=data.short_code,
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
    await ShortURLService.increment_clicks(session, short_url)
    return RedirectResponse(url=short_url.original_url)


@router.get('/{short_code}/info', response_model=ShortURLResponse)
async def get_short_url_info(
    short_url: ShortURL = Depends(get_short_url_by_code),
):
    """Возвращает информацию о короткой ссылке."""
    return ShortURLResponse.model_validate(short_url)


@router.delete('/{short_code}', response_model=ShortURLDeleteResponse)
async def deactivate_short_url(
    short_url: ShortURL = Depends(get_short_url_by_code),
    session: AsyncSession = Depends(get_async_session),
):
    """Удаляет короткую ссылку."""
    await ShortURLService.delete_short_url(session, short_url)
    return ShortURLDeleteResponse(short_code=short_url.short_code)
