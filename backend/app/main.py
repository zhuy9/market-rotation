from fastapi import FastAPI

from app.api import health, refresh, universe

app = FastAPI(title="Market Rotation Dashboard API")

app.include_router(health.router, prefix="/api")
app.include_router(universe.router, prefix="/api")
app.include_router(refresh.router, prefix="/api")
