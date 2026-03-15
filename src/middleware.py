from fastapi import Request, status
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from src.cache.keys import RedisKeys
from src.cache.redis import redis_manager
from src.config import settings


RATE_LIMITED_PATHS = {"/"}
RATE_LIMIT = 60
WINDOW = settings.redis.RATE_LIMIT_TTL


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Ограничивает количество POST-запросов на создание ссылок по IP."""

    async def dispatch(self, request: Request, call_next):
        if request.method != "POST" or request.url.path not in RATE_LIMITED_PATHS:
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        key = RedisKeys.rate_limit_key(ip)

        try:
            redis = redis_manager.get()
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, WINDOW)

            if count > RATE_LIMIT:
                logger.warning(
                    "Rate limit exceeded",
                    extra={"ip": ip, "count": count},
                )
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": f"Too many requests. Limit: {RATE_LIMIT} per {WINDOW}s."
                    },
                )
        except Exception as e:
            logger.error("Rate limit check failed", extra={"error": str(e)})

        return await call_next(request)
