from __future__ import annotations

from functools import lru_cache

from app.config.universe import Universe, load_universe
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
def get_market_service() -> MarketService:
    return MarketService(YFinanceMarketDataProvider(), get_repository(), get_universe())
