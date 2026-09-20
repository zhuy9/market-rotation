from fastapi import FastAPI

from app.api import health

app = FastAPI(title="Market Rotation Dashboard API")

app.include_router(health.router, prefix="/api")
