from fastapi import FastAPI

from ml_service.lifespan import lifespan


app = FastAPI(
    title="Autocare bot ML Service",
    version="0.0.1",
    lifespan=lifespan,
)
