import logging
import sys


def setup_logging():
    log_format = (
        "%(levelname)s:     %(asctime)s | %(name)s | %(message)s"
    )

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )

    return logging.getLogger("app")
