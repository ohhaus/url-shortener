from pydantic import BaseSettings, PostgresDsn, field_validator


class DatabaseSettings(BaseSettings):
    """Настройки базы данных."""

    URL: str = 'sqlite+aiosqlite:///./url_shorter.db'  # поменять на PostgresDsn
    POOL_TIMEOUT: int = 30
    POOL_RECYCLE: int = 1800
    POOL_SIZE: int = 20
    MAX_OVERFLOW: int = 30
    POOL_PING: bool = True
    ECHO_SQL: bool = False

    class Config:
        env_prefix = 'DATABASE_'
        env_file = '.env'
        env_file_encoding = 'utf-8'


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

    @field_validator('ENVIRONMENT')
    def validate_environment(cls, v):
        allowed = ['development', 'staging', 'production']
        if v not in allowed:
            raise ValueError(f'ENVIRONMENT должен быть одним из: {allowed}')
        return v

    class Config:
        env_prefix = 'APP_'
        env_file = '.env'
        env_file_encoding = 'utf-8'


class LoggingSettings(BaseSettings):
    """Настройки логирования."""

    LEVEL: str = 'INFO'
    FORMAT: str = 'json'

    class Config:
        env_prefix = 'LOG_'
        env_file = '.env'
        env_file_encoding = 'utf-8'


class Settings(BaseSettings):
    """Корневой класс настроек."""

    app: ApplicationSettings = ApplicationSettings()
    database: DatabaseSettings = DatabaseSettings()
    logging: LoggingSettings = LoggingSettings()

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = False


settings = Settings()
