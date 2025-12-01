from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.sessions import get_async_session
from src.shortener.exceptions import ShortURLNotFound
from src.shortener.services import ShortURLService


async def get_short_url_by_code(
    short_code: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Получает короткую ссылку по коду."""
    try:
        return await ShortURLService.get_by_code(session, short_code)
    except ShortURLNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        ) from e
