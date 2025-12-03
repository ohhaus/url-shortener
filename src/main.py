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
        await redis_manager.get_client().ping()
        print('Redis connection established')
        yield
    finally:
        await arq_client.close()
        await redis_manager.close()



app = FastAPI(title='Shortener Service', lifespan=lifespan)


@app.get('/health')
async def health_check():
    """Health check эндпоинт с проверкой Redis."""
    try:
        redis_ok = await redis_manager.get_client().ping()

        return {
            'status': 'healthy',
            'redis': 'connected' if redis_ok else 'disconnected',
            'version': '1.0.0',
        }
    except Exception as e:
        return {'status': 'unhealthy', 'redis': 'disconnected', 'error': str(e)}


app.include_router(main_router)
