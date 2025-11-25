"""
Кастомные исключения для модуля сокращения URL.
"""

class ShortURLError(Exception):
    """Базовое исключение."""
    pass


class ShortURLNotFound(ShortURLError):
    """Ссылка не найдена."""
    pass


class ShortCodeAlreadyExists(ShortURLError):
    """Код уже существует."""
