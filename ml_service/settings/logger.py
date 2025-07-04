import sys
import logging
from pathlib import Path

from loguru import logger

from ml_service.settings.config import config


class InterceptHandler(logging.Handler):
    """Intercepts logging messages and sends them to loguru logger."""

    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


if config.is_prod:
    LOG_FORMAT = (
        "{{"
        '"time": "{time:YYYY-MM-DDTHH:mm:ss.SSSZ}", '
        '"level": "{level}", '
        '"name": "{name}", '
        '"function": "{function}", '
        '"line": {line}, '
        '"message": "{message}"'
        "}}"
    )
else:
    LOG_FORMAT = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

logger.remove()
logger.add(sys.stdout, level=config.log_level, format=LOG_FORMAT, enqueue=True)

if config.log_file:
    Path(config.log_file).parent.mkdir(parents=True, exist_ok=True)
    logger.add(
        sink=config.log_file,
        level=config.log_level,
        format=LOG_FORMAT,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        enqueue=True,
    )

# intercept default logger with my custom logger
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
    log = logging.getLogger(name)
    log.handlers = [InterceptHandler()]
    log.propagate = False
