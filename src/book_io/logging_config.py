"""Package-scoped logging with rotation and predictable handler lifecycle."""

import logging
from logging.handlers import RotatingFileHandler

from book_io.exceptions import ConfigurationError
from book_io.models import LoggingConfig


def configure_logging(config: LoggingConfig) -> None:
    logger = logging.getLogger("book_io")
    logger.setLevel(config.level)
    logger.propagate = False
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()
    try:
        config.path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            config.path,
            maxBytes=config.max_bytes,
            backupCount=config.backups,
            encoding="utf-8",
        )
    except OSError as error:
        raise ConfigurationError("Cannot create application log") from error
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    for handler in (file_handler, logging.StreamHandler()):
        handler.setFormatter(formatter)
        logger.addHandler(handler)
