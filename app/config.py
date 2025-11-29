from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Настройки базы данных."""

    URL: str = 'postgresql+asyncpg://postgres:postgres@localhost:5432/postgres'
    TEST_URL: str = 'sqlite+aiosqlite:///./test.db'
    POOL_TIMEOUT: int = 30
    POOL_RECYCLE: int = 1800
    POOL_SIZE: int = 20
    MAX_OVERFLOW: int = 30
    POOL_PING: bool = True
    ECHO_SQL: bool = False

    model_config = SettingsConfigDict(
        env_prefix = 'DATABASE_',
        env_file = '.env',
        env_file_encoding = 'utf-8',
    )


class ApplicationSettings(BaseSettings):
    """Настройки приложения."""

    TITLE: str = 'URL Shortener'
    DESCRIPTION: str = 'Высокопрозводительный сервис сокращения URL'
    VERSION: str = '1.0.0'
    DEBUG: bool = False
    ENVIRONMENT: str = 'development'

    WORKERS: int = 4
    MAX_REQUESTS: int = 1000
    MAX_REQUESTS_JITTER: int = 100

    BASE_URL: str = 'http://localhost:8000'
    SHORT_CODE_LENGTH: int = 6
    MAX_ATTEMPTS: int = 3

    @field_validator('ENVIRONMENT')
    def validate_environment(cls, v):
        allowed = ['development', 'staging', 'production']
        if v not in allowed:
            raise ValueError(f'ENVIRONMENT должен быть одним из: {allowed}')
        return v

    model_config = SettingsConfigDict(
        env_prefix = 'APP_',
        env_file = '.env',
        env_file_encoding = 'utf-8',
    )


class LoggingSettings(BaseSettings):
    """Настройки логирования."""

    LEVEL: str = 'INFO'
    FORMAT: str = 'json'

    model_config = SettingsConfigDict(
        env_prefix = 'LOG_',
        env_file = '.env',
        env_file_encoding = 'utf-8',
    )


class Settings(BaseSettings):
    """Корневой класс настроек."""

    app: ApplicationSettings = ApplicationSettings()
    database: DatabaseSettings = DatabaseSettings()
    logging: LoggingSettings = LoggingSettings()

    model_config = SettingsConfigDict(
        env_file = '.env',
        env_file_encoding = 'utf-8',
        case_sensitive = False,
    )


settings = Settings()
