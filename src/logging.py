import logging
import sys

from loguru import logger


LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan> | "
    "{message}"
    "{extra}"
)

LOG_FORMAT_EXTRA = ""


def _format(record):
    """Добавляет extra-поля в конец строки если они есть."""
    extra = record["extra"]
    skip = {"name"}
    fields = {k: v for k, v in extra.items() if k not in skip}
    if fields:
        record["extra"]["_fmt_extra"] = " | " + " ".join(f"{k}={v}" for k, v in fields.items())
    else:
        record["extra"]["_fmt_extra"] = ""

    return (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan> | "
        "{message}{extra[_fmt_extra]}\n"
    )

class InterceptHandler(logging.Handler):
    """Перехватывает все стандартные логи (uvicorn, sqlalchemy, arq) → loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).bind(name=record.name).log(
            level, record.getMessage()
        )


def setup_logging(level: str = "INFO") -> None:
    """
    Настраивает единое логирование через loguru.
    Перехватывает uvicorn, sqlalchemy, arq и все прочие логгеры.
    """
    logger.remove()

    logger.add(
        sys.stdout,
        format=_format,
        level=level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    for name in (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "gunicorn",
        "gunicorn.access",
        "gunicorn.error",
        "sqlalchemy.engine",
        "arq",
        "fastapi",
    ):
        log = logging.getLogger(name)
        log.handlers = [InterceptHandler()]
        log.propagate = False
