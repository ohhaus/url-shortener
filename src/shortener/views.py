import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

from src.shortener.dependencies import get_short_url_by_code, get_short_url_service
from src.shortener.exceptions import ShortCodeAlreadyExists, ShortURLNotFound
from src.shortener.models import ShortURL
from src.shortener.schemas import ShortURLCreate, ShortURLDeleteResponse, ShortURLResponse
from src.shortener.services import ShortURLService


logger = logging.getLogger('app')

router = APIRouter()


@router.post('/', response_model=ShortURLResponse, status_code=status.HTTP_201_CREATED)
async def create_short_url(
    data: ShortURLCreate,
    service: ShortURLService = Depends(get_short_url_service),
) -> ShortURLResponse:
    try:
        short_url = await service.create(original_url=str(data.original_url))
    except ShortCodeAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    return ShortURLResponse.model_validate(short_url)


@router.get('/{short_code}', status_code=status.HTTP_302_FOUND)
async def redirect_to_original(
    short_code: str,
    service: ShortURLService = Depends(get_short_url_service),
) -> RedirectResponse:
    try:
        original_url = await service.get_original_url(short_code)
    except ShortURLNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    await service.increment_clicks(short_code)
    return RedirectResponse(url=original_url, status_code=status.HTTP_302_FOUND)


@router.get('/{short_code}/info', response_model=ShortURLResponse)
async def get_short_url_info(
    short_url: ShortURL = Depends(get_short_url_by_code),
) -> ShortURLResponse:
    return ShortURLResponse.model_validate(short_url)


@router.delete('/{short_code}', response_model=ShortURLDeleteResponse)
async def delete_short_url(
    short_url: ShortURL = Depends(get_short_url_by_code),
    service: ShortURLService = Depends(get_short_url_service),
) -> ShortURLDeleteResponse:
    await service.delete(short_url)
    return ShortURLDeleteResponse(short_code=short_url.short_code)
