from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    TEST_URL: str = "sqlite+aiosqlite:///:memory:"
    POOL_TIMEOUT: int = 30
    POOL_RECYCLE: int = 1800
    POOL_SIZE: int = 20
    MAX_OVERFLOW: int = 30
    POOL_PING: bool = True
    ECHO_SQL: bool = False

    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class RedisSettings(BaseSettings):
    URL: str = "redis://localhost:6379/0"
    PASSWORD: str = "password"
    SOCKET_CONNECT_TIMEOUT: int = 5
    SOCKET_TIMEOUT: int = 5
    RETRY_ON_TIMEOUT: bool = True
    MAX_CONNECTIONS: int = 10
    REDIRECT_CACHE_TTL: int = 3600
    CLICK_CACHE_TTL: int = 300
    RATE_LIMIT_TTL: int = 60

    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class ApplicationSettings(BaseSettings):
    TITLE: str = "URL Shortener"
    DESCRIPTION: str = "Высокопроизводительный сервис сокращения URL"
    VERSION: str = "1.0.0"
    WORKERS: int = 4
    MAX_REQUESTS: int = 1000
    MAX_REQUESTS_JITTER: int = 100
    BASE_URL: str = "http://localhost:8000"
    SHORT_CODE_LENGTH: int = 6
    MAX_ATTEMPTS: int = 3

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class LoggingSettings(BaseSettings):
    LEVEL: str = "INFO"
    FORMAT: str = "json"

    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class WorkerSettings(BaseSettings):
    REDIS_DSN: str = Field(default="redis://:password@redis:6379/1")
    QUEUE_NAME: str = Field(default="click_tasks")
    MAX_JOBS: int = Field(default=10, ge=1)
    JOB_TIMEOUT: int = Field(default=30, ge=10)
    MAX_TRIES: int = Field(default=3, ge=1)

    model_config = SettingsConfigDict(
        env_prefix="WORKER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class Settings(BaseSettings):
    app: ApplicationSettings = ApplicationSettings()
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    logging: LoggingSettings = LoggingSettings()
    worker: WorkerSettings = WorkerSettings()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
