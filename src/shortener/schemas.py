from pydantic import BaseModel, ConfigDict, HttpUrl


class ShortURLCreate(BaseModel):
    """Схема для создания короткой ссылки."""

    original_url: HttpUrl


class ShortURLResponse(BaseModel):
    short_code: str
    original_url: str
    clicks: int

    model_config = ConfigDict(
        from_attributes = True,
    )


class ShortURLDeleteResponse(BaseModel):
    status: str = "deleted"
    short_code: str
