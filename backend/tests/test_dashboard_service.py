from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from app.config.universe import load_universe
from app.services.dashboard_service import build_dashboard
from app.services.market_service import MarketService
from app.storage.duckdb_repository import DuckDBRepository


class _NoOpProvider:
    """MarketService requires a provider, but build_dashboard only reads cached data."""

    def get_history(self, symbols, start, end, interval):
        raise NotImplementedError

    def get_latest(self, symbols):
        raise NotImplementedError


def _seed(repo: DuckDBRepository, symbol: str, closes: list[float], end: pd.Timestamp) -> None:
    timestamps = pd.date_range(end=end, periods=len(closes), freq="D")
    df = pd.DataFrame(
        {
            "symbol": symbol,
            "timestamp": timestamps,
            "open": closes,
            "high": closes,
            "low": closes,
            "close": closes,
            "volume": [1_000.0] * len(closes),
        }
    )
    repo.upsert_prices(df, interval="1d", provider="test", retrieved_at=datetime.now(UTC))


def _ramp(step: float, sessions: int = 25) -> list[float]:
    return [100.0 + step * i for i in range(sessions)]


def _seed_broad_risk_on_universe(repo: DuckDBRepository, end: pd.Timestamp) -> None:
    """Every sector, RSP, and HYG grow faster than SPY/LQD; everything else is flat."""
    universe = load_universe()
    steps = {
        "SPY": 1.0,
        "RSP": 1.5,
        "HYG": 1.0,
        "LQD": 0.0,
    }
    for instrument in universe.instruments:
        if instrument.category == "sectors":
            step = 2.0
        else:
            step = steps.get(instrument.symbol, 0.0)
        _seed(repo, instrument.symbol, _ramp(step), end)


def test_build_dashboard_end_to_end_matches_broad_risk_on():
    universe = load_universe()
    repo = DuckDBRepository(":memory:")
    _seed_broad_risk_on_universe(repo, pd.Timestamp.now().normalize())
    service = MarketService(_NoOpProvider(), repo, universe)

    result = build_dashboard(service, universe)

    assert result.provider == "yfinance"
    assert result.is_stale is False
    assert result.warnings == []
    assert len(result.sectors) == 11
    assert len(result.cross_asset) == len(universe.symbols) - 11
    assert result.regime.name == "BROAD_RISK_ON"
    assert result.breadth_5d.positive == 11


def test_build_dashboard_reports_missing_symbol_as_warning():
    universe = load_universe()
    repo = DuckDBRepository(":memory:")
    end = pd.Timestamp.now().normalize()
    for instrument in universe.instruments:
        if instrument.symbol == "USO":
            continue
        _seed(repo, instrument.symbol, _ramp(0.5), end)
    service = MarketService(_NoOpProvider(), repo, universe)

    result = build_dashboard(service, universe)

    assert "USO data is unavailable." in result.warnings


def test_build_dashboard_flags_stale_data():
    universe = load_universe()
    repo = DuckDBRepository(":memory:")
    old_end = pd.Timestamp.now().normalize() - pd.Timedelta(days=10)
    for instrument in universe.instruments:
        _seed(repo, instrument.symbol, _ramp(0.5), old_end)
    service = MarketService(_NoOpProvider(), repo, universe)

    result = build_dashboard(service, universe)

    assert result.is_stale is True
    assert any("STALE DATA" in w for w in result.warnings)


def test_build_dashboard_handles_completely_empty_cache():
    universe = load_universe()
    repo = DuckDBRepository(":memory:")
    service = MarketService(_NoOpProvider(), repo, universe)

    result = build_dashboard(service, universe)

    assert result.sectors == []
    assert result.cross_asset == []
    assert result.regime.name == "MIXED"
    assert result.data_timestamp is None
    assert result.is_stale is True
    assert result.warnings == ["No cached market data available. Trigger a refresh."]
