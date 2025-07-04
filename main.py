import uvicorn

from ml_service.settings.logger import logger
from ml_service.settings.config import config


def main():
    logger.info("Hello from autocare-ml-service!")


if __name__ == "__main__":
    logger.warning(config)
    uvicorn.run(
        "ml_service.app:app",
        host="0.0.0.0",
        port=8000,
        workers=1,
        reload=not config.is_prod,
        log_config=None,  # Disable Uvicorn's default logging config to use our custom logger
    )
