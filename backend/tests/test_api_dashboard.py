from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
from fastapi.testclient import TestClient

from app.config.universe import load_universe
from app.deps import get_market_service, get_universe
from app.main import app
from app.services.market_service import MarketService
from app.storage.duckdb_repository import DuckDBRepository


class _NoOpProvider:
    def get_history(self, symbols, start, end, interval):
        raise NotImplementedError

    def get_latest(self, symbols):
        raise NotImplementedError


def _seeded_service() -> MarketService:
    universe = load_universe()
    repo = DuckDBRepository(":memory:")
    end = pd.Timestamp.now().normalize()
    for instrument in universe.instruments:
        closes = [100.0 + i for i in range(25)]
        timestamps = pd.date_range(end=end, periods=len(closes), freq="D")
        df = pd.DataFrame(
            {
                "symbol": instrument.symbol,
                "timestamp": timestamps,
                "open": closes,
                "high": closes,
                "low": closes,
                "close": closes,
                "volume": [1_000.0] * len(closes),
            }
        )
        repo.upsert_prices(df, interval="1d", provider="test", retrieved_at=datetime.now(UTC))
    return MarketService(_NoOpProvider(), repo, universe)


def test_dashboard_endpoint_returns_valid_response_shape():
    app.dependency_overrides[get_market_service] = _seeded_service
    app.dependency_overrides[get_universe] = load_universe
    client = TestClient(app)

    response = client.get("/api/dashboard")

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "yfinance"
    assert len(body["sectors"]) == 11
    assert "regime" in body and body["regime"]["name"]
    assert isinstance(body["warnings"], list)
    assert "rsp_spy" in body["ratios"]
    assert "hyg_lqd" in body["ratios"]

    app.dependency_overrides.clear()


def test_dashboard_endpoint_exposes_freshness_metadata():
    """PRD section 13: data_timestamp, retrieved_at and provider must all be
    reachable through the API, not just rendered somewhere in the UI."""
    app.dependency_overrides[get_market_service] = _seeded_service
    app.dependency_overrides[get_universe] = load_universe
    client = TestClient(app)

    body = client.get("/api/dashboard").json()

    assert body["provider"] == "yfinance"
    assert body["data_timestamp"] is not None
    assert body["retrieved_at"] is not None

    app.dependency_overrides.clear()


def test_dashboard_endpoint_handles_empty_cache_without_error():
    app.dependency_overrides[get_market_service] = lambda: MarketService(
        _NoOpProvider(), DuckDBRepository(":memory:"), load_universe()
    )
    app.dependency_overrides[get_universe] = load_universe
    client = TestClient(app)

    response = client.get("/api/dashboard")

    assert response.status_code == 200
    body = response.json()
    assert body["sectors"] == []
    assert body["regime"]["name"] == "MIXED"

    app.dependency_overrides.clear()
