from functools import wraps
from typing import Type, Callable, Any

from sqlalchemy.exc import IntegrityError

from app.shortener.exceptions import ShortCodeAlreadyExists


def retry_on_integrity_error(
    max_attempts: int = 3,
    exceptions: Type[Exception] = IntegrityError
):
    """Декоратор для повторных попыток генерации."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except:
                    if attempt == max_attempts:
                        raise ShortCodeAlreadyExists
            return None
        return wrapper
    return decorator
