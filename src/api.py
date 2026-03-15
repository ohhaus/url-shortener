from fastapi import APIRouter

from src.health import router as health_router
from src.shortener import shorten_router


main_router = APIRouter()

main_router.include_router(health_router, tags=["Health"])
main_router.include_router(shorten_router, tags=["Shortener"])
