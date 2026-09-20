from __future__ import annotations

from datetime import datetime

import pandas as pd

from app.config.universe import Instrument, Universe
from app.providers.base import PRICE_COLUMNS
from app.services.market_service import MarketService
from app.storage.duckdb_repository import DuckDBRepository


class FakeProvider:
    """Test double for MarketDataProvider: returns canned history, no network."""

    def __init__(self, history: pd.DataFrame) -> None:
        self._history = history
        self.calls = 0

    def get_history(self, symbols, start, end, interval):
        self.calls += 1
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
