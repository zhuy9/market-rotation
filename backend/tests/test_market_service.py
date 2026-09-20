from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pandas as pd

from app.config.universe import Instrument, Universe
from app.providers.base import PRICE_COLUMNS
from app.services.market_service import HISTORY_DAYS, MarketService
from app.storage.duckdb_repository import DuckDBRepository


class FakeProvider:
    """Test double for MarketDataProvider: returns canned history, no network."""

    def __init__(self, history: pd.DataFrame) -> None:
        self._history = history
        self.calls = 0
        self.starts: list[datetime] = []

    def get_history(self, symbols, start, end, interval):
        self.calls += 1
        self.starts.append(start)
        if self._history.empty:
            return self._history
        return self._history[self._history["symbol"].isin(symbols)]

    def get_latest(self, symbols):
        raise NotImplementedError


def _universe() -> Universe:
    return Universe(
        [
            Instrument(symbol="AAA", name="Alpha", category="sectors"),
            Instrument(symbol="BBB", name="Beta", category="sectors"),
        ]
    )


def _history_for(symbols: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "symbol": symbol,
                "timestamp": datetime(2026, 1, 1),
                "open": 10.0,
                "high": 10.5,
                "low": 9.5,
                "close": 10.2,
                "volume": 1000.0,
            }
            for symbol in symbols
        ]
    )


def test_refresh_reports_success_when_all_symbols_return_data():
    provider = FakeProvider(_history_for(["AAA", "BBB"]))
    service = MarketService(provider, DuckDBRepository(":memory:"), _universe())

    result = service.refresh()

    assert result.status == "success"
    assert result.updated_symbols == 2
    assert result.failed_symbols == []


def test_refresh_reports_partial_and_keeps_good_data_when_one_symbol_fails():
    repo = DuckDBRepository(":memory:")
    service = MarketService(FakeProvider(_history_for(["AAA"])), repo, _universe())

    result = service.refresh()

    assert result.status == "partial"
    assert result.updated_symbols == 1
    assert result.failed_symbols == ["BBB"]

    prices = repo.get_prices(["AAA"], datetime(2025, 1, 1), datetime(2027, 1, 1), "1d")
    assert len(prices) == 1


def test_refresh_reports_failed_when_provider_returns_nothing():
    empty = pd.DataFrame(columns=PRICE_COLUMNS)
    service = MarketService(FakeProvider(empty), DuckDBRepository(":memory:"), _universe())

    result = service.refresh()

    assert result.status == "failed"
    assert result.updated_symbols == 0
    assert sorted(result.failed_symbols) == ["AAA", "BBB"]


def test_refresh_enforces_cooldown():
    provider = FakeProvider(_history_for(["AAA", "BBB"]))
    service = MarketService(provider, DuckDBRepository(":memory:"), _universe())

    service.refresh()
    second = service.refresh()

    assert second.status == "cooldown"
    assert provider.calls == 1


# --- incremental refresh window (PRD section 12) ---------------------------


def _seed(repo: DuckDBRepository, symbols: list[str], newest: datetime) -> None:
    """Give each symbol two cached daily bars ending at `newest`."""
    timestamps = [newest - timedelta(days=1), newest]
    frame = pd.DataFrame(
        [
            {
                "symbol": symbol,
                "timestamp": timestamp,
                "open": 10.0,
                "high": 10.5,
                "low": 9.5,
                "close": 10.2,
                "volume": 1000.0,
            }
            for symbol in symbols
            for timestamp in timestamps
        ]
    )
    repo.upsert_prices(frame, "1d", "test", datetime.now(UTC))


def test_refresh_requests_full_history_when_cache_is_empty():
    provider = FakeProvider(_history_for(["AAA", "BBB"]))
    service = MarketService(provider, DuckDBRepository(":memory:"), _universe())

    service.refresh()

    requested_days = (datetime.now(UTC) - provider.starts[0]).days
    assert requested_days >= HISTORY_DAYS - 1


def test_refresh_only_requests_missing_data_when_cache_is_current():
    """The whole point of PRD section 12: top up from the cached edge instead
    of re-downloading 400 days on every refresh."""
    repo = DuckDBRepository(":memory:")
    _seed(repo, ["AAA", "BBB"], datetime.now(UTC).replace(tzinfo=None))
    provider = FakeProvider(_history_for(["AAA", "BBB"]))
    service = MarketService(provider, repo, _universe())

    service.refresh()

    requested_days = (datetime.now(UTC) - provider.starts[0]).days
    assert requested_days < 10


def test_refresh_backfills_full_history_when_one_symbol_has_no_cached_data():
    """A newly added ticker must get real history, not just the recent window."""
    repo = DuckDBRepository(":memory:")
    _seed(repo, ["AAA"], datetime.now(UTC).replace(tzinfo=None))  # BBB never cached
    provider = FakeProvider(_history_for(["AAA", "BBB"]))
    service = MarketService(provider, repo, _universe())

    service.refresh()

    requested_days = (datetime.now(UTC) - provider.starts[0]).days
    assert requested_days >= HISTORY_DAYS - 1


# --- startup refresh (PRD section 12) --------------------------------------


def test_refresh_if_stale_fetches_when_cache_is_empty():
    provider = FakeProvider(_history_for(["AAA", "BBB"]))
    service = MarketService(provider, DuckDBRepository(":memory:"), _universe())

    result = service.refresh_if_stale()

    assert result is not None
    assert provider.calls == 1


def test_refresh_if_stale_does_nothing_when_cache_is_current():
    repo = DuckDBRepository(":memory:")
    _seed(repo, ["AAA", "BBB"], datetime.now(UTC).replace(tzinfo=None))
    provider = FakeProvider(_history_for(["AAA", "BBB"]))
    service = MarketService(provider, repo, _universe())

    assert service.refresh_if_stale() is None
    assert provider.calls == 0


def test_refresh_if_stale_fetches_when_cached_data_is_old():
    repo = DuckDBRepository(":memory:")
    _seed(repo, ["AAA", "BBB"], datetime.now(UTC).replace(tzinfo=None) - timedelta(days=10))
    provider = FakeProvider(_history_for(["AAA", "BBB"]))
    service = MarketService(provider, repo, _universe())

    assert service.refresh_if_stale() is not None
    assert provider.calls == 1
