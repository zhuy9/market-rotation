from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient

from app.config.universe import Instrument, Universe
from app.deps import get_market_service, get_universe
from app.main import app
from app.services.market_service import RefreshResult


class FakeMarketService:
    def refresh(self) -> RefreshResult:
        return RefreshResult(
            status="success", updated_symbols=2, failed_symbols=[], as_of=datetime(2026, 1, 1)
        )


def _fake_universe() -> Universe:
    return Universe([Instrument(symbol="AAA", name="Alpha", category="sectors")])


def test_get_universe_returns_configured_instruments():
    app.dependency_overrides[get_universe] = _fake_universe
    client = TestClient(app)

    response = client.get("/api/universe")

    assert response.status_code == 200
    assert response.json() == [{"symbol": "AAA", "name": "Alpha", "category": "sectors"}]

    app.dependency_overrides.clear()


def test_refresh_endpoint_returns_result_shape():
    app.dependency_overrides[get_market_service] = lambda: FakeMarketService()
    client = TestClient(app)

    response = client.post("/api/data/refresh")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["updated_symbols"] == 2
    assert body["failed_symbols"] == []

    app.dependency_overrides.clear()


# --- startup refresh wiring (PRD section 12) -------------------------------


def test_startup_tops_up_the_cache_before_serving(monkeypatch):
    calls: list[str] = []

    class _StartupService:
        def refresh_if_stale(self) -> RefreshResult:
            calls.append("refreshed")
            return RefreshResult(
                status="success", updated_symbols=2, failed_symbols=[], as_of=datetime(2026, 1, 1)
            )

    monkeypatch.setattr("app.main.get_market_service", _StartupService)

    with TestClient(app):
        pass

    assert calls == ["refreshed"]


def test_startup_survives_a_provider_outage(monkeypatch):
    """A dead provider at boot must not stop the API from starting — the
    dashboard degrades to cached data plus a warning instead."""

    class _BrokenService:
        def refresh_if_stale(self) -> RefreshResult:
            raise RuntimeError("network unavailable")

    monkeypatch.setattr("app.main.get_market_service", _BrokenService)

    with TestClient(app) as client:
        assert client.get("/api/health").status_code == 200
