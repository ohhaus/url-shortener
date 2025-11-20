"""
Кастомные исключения для модуля сокращения URL.
"""

class ShortURLError(Exception):
    """Базовое исключение для всех ошибок модуля коротких ссылок."""

    def __init__(self, message: str, code: str | None = None):
        self.message = message
        self.code = code or 'SHORT_URL_ERROR'
        super().__init__(self.message)


class ShortURLNotFound(ShortURLError):
    """Исключение, когда короткая ссылка не найдена."""

    def __init__(self, message: str):
        super().__init__(message, 'SHORT_URL_NOT_FOUND')


class ShortCodeAlreadyExists(ShortURLError):
    """Исключение, когда запрашиваемый короткий код уже занят."""

    def __init__(self, message: str):
        super().__init__(message, 'SHORT_CODE_ALREADY_EXISTS')


class ShortURLExpired(ShortURLError):
    """Исключение, когда срок действия короткой ссылки истек."""

    def __init__(self, message: str):
        super().__init__(message, 'SHORT_URL_EXPIRED')


class ShortURLInactive(ShortURLError):
    """Исключение, когда короткая ссылка деактивирована."""

    def __init__(self, message: str):
        super().__init__(message, 'SHORT_URL_INACTIVE')
