from functools import wraps
from typing import Any, Callable

from sqlalchemy.exc import IntegrityError

from src.shortener.exceptions import ShortCodeAlreadyExists


def retry_on_integrity_error(
    max_attempts: int = 3,
    exceptions: type[Exception] = IntegrityError,
):
    """Декоратор для повторных попыток при коллизии генерации короткого кода."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as err:
                    instance = args[0] if args else None
                    if instance is not None and hasattr(instance, 'session'):
                        await instance.session.rollback()

                    if attempt == max_attempts:
                        raise ShortCodeAlreadyExists from err

        return wrapper

    return decorator
