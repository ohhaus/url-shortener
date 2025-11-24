from fastapi import FastAPI

from app.api import main_router


app = FastAPI(
    title='Shortener Service',
)


app.include_router(main_router)
