from fastapi import APIRouter, Depends, status
from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.cache.redis import redis_manager
from src.database.sessions import get_async_session


router = APIRouter()


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check",
)
async def health(session: AsyncSession = Depends(get_async_session)) -> dict:
    checks: dict[str, str] = {}

    try:
        await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        logger.error("Health check: database failed", extra={"error": str(e)})
        checks["database"] = "unavailable"

    try:
        await redis_manager.get().ping()
        checks["redis"] = "ok"
    except Exception as e:
        logger.error("Health check: redis failed", extra={"error": str(e)})
        checks["redis"] = "unavailable"

    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks}
