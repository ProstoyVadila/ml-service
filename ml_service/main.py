import uvicorn

from ml_service.settings.logger import logger


def main():
    logger.info("Hello from autocare-ml-service!")


if __name__ == "__main__":
    uvicorn.run(
        "ml_service.app:app",
        host="0.0.0.0",
        port=8000,
        # reload=not IS_PROD,
        reload=True,
        log_config=None,  # Disable Uvicorn's default logging config to use our custom logger
    )
