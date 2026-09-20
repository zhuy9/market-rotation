import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import dashboard, health, refresh, universe
from app.deps import get_market_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """PRD section 12: top the local cache up before serving, so a fresh clone
    shows data on first load instead of an empty dashboard. Only fetches when
    the cache is empty or stale, and a provider outage must never stop the API
    from starting — the dashboard degrades to cached data plus a warning.
    """
    try:
        result = get_market_service().refresh_if_stale()
        if result is not None:
            logger.info(
                "Startup refresh: %s (%d symbols updated, %d failed)",
                result.status,
                result.updated_symbols,
                len(result.failed_symbols),
            )
    except Exception:
        logger.exception("Startup refresh failed; serving cached data only")
    yield


app = FastAPI(title="Market Rotation Dashboard API", lifespan=lifespan)

# The frontend is always served from a localhost port, but not always 5173 --
# Vite moves to 5174+ when the default is taken, and pinning one port made the
# dashboard fail with nothing but a CORS error in the browser console. Match any
# localhost port instead. This stays a local-only tool: the API is
# unauthenticated and serves public market data, and a remote origin such as
# https://evil.example still does not match.
LOCAL_ORIGIN_PATTERN = r"http://(localhost|127\.0\.0\.1)(:\d+)?$"

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=LOCAL_ORIGIN_PATTERN,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(universe.router, prefix="/api")
app.include_router(refresh.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
