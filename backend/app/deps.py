from __future__ import annotations

from functools import lru_cache

from app.config.universe import Universe, load_universe
from app.providers.base import MarketDataProvider
from app.providers.yfinance_provider import YFinanceMarketDataProvider
from app.services.market_service import MarketService
from app.storage.duckdb_repository import DuckDBRepository


@lru_cache
def get_universe() -> Universe:
    return load_universe()


@lru_cache
def get_repository() -> DuckDBRepository:
    return DuckDBRepository()


@lru_cache
def get_provider() -> MarketDataProvider:
    return YFinanceMarketDataProvider()


@lru_cache
def get_market_service() -> MarketService:
    return MarketService(get_provider(), get_repository(), get_universe())
