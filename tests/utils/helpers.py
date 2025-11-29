"""
Вспомогательные функции для тестов.
"""
import asyncio
from typing import List, Callable, Any
from contextlib import contextmanager
import time


@contextmanager
def timer(description: str = "Operation"):
    """Контекстный менеджер для измерения времени."""
    start = time.perf_counter()
    yield
    end = time.perf_counter()
    print(f"⏱️  {description} took {end - start:.4f} seconds")


async def run_concurrently(
    tasks: List[Callable],
    max_concurrent: int = 100
) -> List[Any]:
    """Запускает задачи конкурентно с ограничением."""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def run_with_semaphore(task):
        async with semaphore:
            return await task
    
    return await asyncio.gather(*[run_with_semaphore(task) for task in tasks])


def assert_redis_connectivity():
    """Проверяет доступность Redis (для будущего кеширования)."""
    pass


class ValidationHelpers:
    """Хелперы для валидации данных."""
    
    @staticmethod
    def is_valid_short_code(code: str) -> bool:
        """Проверяет валидность короткого кода."""
        return (
            isinstance(code, str) and
            len(code) == 6 and
            code.isalnum()
        )
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Проверяет валидность URL."""
        return (
            isinstance(url, str) and
            (url.startswith('http://') or url.startswith('https://'))
        )
