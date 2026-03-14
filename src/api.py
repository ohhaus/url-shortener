from fastapi import APIRouter

from src.shortener import shorten_router


main_router = APIRouter()

main_router.include_router(shorten_router, tags=['Shortener'])
