from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api import main_router
from src.cache.redis import redis_manager
from src.worker.client import arq_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_manager.init()
    await arq_client.connect()
    try:
        yield
    finally:
        await arq_client.close()
        await redis_manager.close()


app = FastAPI(title="Shortener Service", lifespan=lifespan)

app.include_router(main_router)

