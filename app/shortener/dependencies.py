from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.sessions import get_async_session
from app.shortener.exceptions import ShortURLExpired, ShortURLInactive, ShortURLNotFound
from app.shortener.services import ShortURLService


async def get_short_url_by_code(
    short_code: str, session: AsyncSession = Depends(get_async_session)
):
    """Dependency для получения активной короткой ссылки по коду."""
    try:
        return await ShortURLService.get_by_code(session, short_code)
    except ShortURLNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except (ShortURLExpired, ShortURLInactive) as e:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=str(e),
        ) from e
