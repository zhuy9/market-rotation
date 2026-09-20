from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pandas as pd

from app.config.universe import Universe
from app.providers.base import MarketDataProvider
from app.storage.duckdb_repository import DuckDBRepository

HISTORY_DAYS = 400
DEFAULT_INTERVAL = "1d"
PROVIDER_NAME = "yfinance"
REFRESH_COOLDOWN = timedelta(seconds=60)


@dataclass(frozen=True)
class RefreshResult:
    status: str  # "success" | "partial" | "failed" | "cooldown"
    updated_symbols: int
    failed_symbols: list[str]
    as_of: datetime


class MarketService:
    """Orchestrates fetching (via MarketDataProvider) and caching (DuckDB)."""

    def __init__(
        self,
        provider: MarketDataProvider,
        repository: DuckDBRepository,
        universe: Universe,
    ) -> None:
        self._provider = provider
        self._repository = repository
        self._universe = universe
        self._last_refresh_at: datetime | None = None

    def refresh(self) -> RefreshResult:
        now = datetime.now(UTC)
        if self._last_refresh_at is not None and now - self._last_refresh_at < REFRESH_COOLDOWN:
            return RefreshResult(
                status="cooldown", updated_symbols=0, failed_symbols=[], as_of=self._last_refresh_at
            )

        start = now - timedelta(days=HISTORY_DAYS)
        symbols = self._universe.symbols
        history = self._provider.get_history(symbols, start, now, DEFAULT_INTERVAL)

        updated = set(history["symbol"].unique()) if not history.empty else set()
        failed_symbols = sorted(set(symbols) - updated)
        self._repository.upsert_prices(history, DEFAULT_INTERVAL, PROVIDER_NAME, now)
        self._last_refresh_at = now

        if not failed_symbols:
            status = "success"
        elif updated:
            status = "partial"
        else:
            status = "failed"

        return RefreshResult(
            status=status, updated_symbols=len(updated), failed_symbols=failed_symbols, as_of=now
        )

    def get_prices(
        self, symbols: list[str] | None = None, interval: str = DEFAULT_INTERVAL
    ) -> pd.DataFrame:
        symbols = symbols if symbols is not None else self._universe.symbols
        now = datetime.now(UTC)
        start = now - timedelta(days=HISTORY_DAYS)
        return self._repository.get_prices(symbols, start, now, interval)
