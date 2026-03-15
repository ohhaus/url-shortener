from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from src.api import main_router
from src.cache.redis import redis_manager
from src.config import settings
from src.logging import setup_logging
from src.middleware import RateLimitMiddleware
from src.worker.client import arq_client


setup_logging(level=settings.logging.LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    await redis_manager.init()
    await arq_client.connect()
    logger.info("Startup complete")
    try:
        yield
    finally:
        logger.info("Shutting down...")
        await arq_client.close()
        await redis_manager.close()
        logger.info("Shutdown complete")


app = FastAPI(
    title=settings.app.TITLE,
    description=settings.app.DESCRIPTION,
    version=settings.app.VERSION,
    lifespan=lifespan,
)

app.add_middleware(RateLimitMiddleware)
app.include_router(main_router)
