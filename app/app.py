import asyncio

from fastapi import FastAPI

from app.lifespan import lifespan


app = FastAPI(
    title="Autocare bot ML Service",
    version="0.0.1",
    lifespan=lifespan,
)
