from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from ml_service.lifespan import lifespan


app = FastAPI(
    title="ML Service for Autocare Telegram Bot",
    version="0.0.1",
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app)
