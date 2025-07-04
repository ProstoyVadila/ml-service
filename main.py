import uvicorn

from ml_service.settings.logger import logger
from ml_service.settings.config import config


def main():
    logger.info("Hello from autocare-ml-service!")


if __name__ == "__main__":
    logger.warning(config)
    uvicorn.run(
        "ml_service.app:app",
        host=config.app.host,
        port=config.app.port,
        workers=config.app.workers,
        reload=config.reload,
        log_config=None,  # Disable Uvicorn's default logging config to use our custom logger
    )
