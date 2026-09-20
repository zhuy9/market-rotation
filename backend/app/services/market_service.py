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
# Re-request a few sessions behind the cached edge so late corrections and
# split adjustments land. INSERT OR REPLACE makes the overlap idempotent.
REFRESH_OVERLAP = timedelta(days=5)
# Long weekend or holiday, plus a day of buffer. Used both to decide whether
# startup needs to top the cache up and to label the dashboard STALE DATA.
STALE_AFTER = timedelta(days=4)


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

        symbols = self._universe.symbols
        history = self._provider.get_history(
            symbols, self._history_start(now), now, DEFAULT_INTERVAL
        )

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

    def refresh_if_stale(self) -> RefreshResult | None:
        """Startup path (PRD section 12): top the cache up when it is empty or
        older than expected, so the first dashboard request has data to serve.
        Returns None when the cache is already current and nothing was fetched.
        """
        newest = self._newest_cached()
        if newest is not None and datetime.now(UTC) - newest <= STALE_AFTER:
            return None
        return self.refresh()

    def _history_start(self, now: datetime) -> datetime:
        """PRD section 12: request only the missing data instead of
        re-downloading the whole window. Falls back to a full backfill while
        any configured symbol has no cached data at all, so a new ticker is
        still filled in with real history.
        """
        full_start = now - timedelta(days=HISTORY_DAYS)
        cached = self._repository.latest_timestamps(self._universe.symbols, DEFAULT_INTERVAL)
        if len(cached) < len(self._universe.symbols):
            return full_start
        oldest = _as_utc(min(cached.values()))
        return max(full_start, oldest - REFRESH_OVERLAP)

    def _newest_cached(self) -> datetime | None:
        cached = self._repository.latest_timestamps(self._universe.symbols, DEFAULT_INTERVAL)
        if len(cached) < len(self._universe.symbols):
            return None  # a missing symbol counts as "not current"
        return _as_utc(max(cached.values()))

    def latest_retrieved_at(self) -> datetime | None:
        """When a provider last wrote to the cache (PRD section 13)."""
        return self._repository.latest_retrieved_at(DEFAULT_INTERVAL)

    def get_prices(
        self, symbols: list[str] | None = None, interval: str = DEFAULT_INTERVAL
    ) -> pd.DataFrame:
        symbols = symbols if symbols is not None else self._universe.symbols
        now = datetime.now(UTC)
        start = now - timedelta(days=HISTORY_DAYS)
        return self._repository.get_prices(symbols, start, now, interval)


def _as_utc(timestamp: datetime) -> datetime:
    """Bar timestamps come back from DuckDB as naive trading dates. Treat them
    as UTC so they can be compared against `datetime.now(UTC)`.
    """
    return timestamp if timestamp.tzinfo is not None else timestamp.replace(tzinfo=UTC)
