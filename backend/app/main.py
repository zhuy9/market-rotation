from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import dashboard, health, refresh, universe

app = FastAPI(title="Market Rotation Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(universe.router, prefix="/api")
app.include_router(refresh.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
