"""The flows endpoint reports an empty list rather than an error when nothing is
cached, so the dashboard can omit the panel instead of showing a failure."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
from fastapi.testclient import TestClient

from app.config.universe import load_universe
from app.deps import get_repository, get_universe
from app.main import app
from app.services.flow_service import FLOW_WINDOWS
from app.storage.duckdb_repository import DuckDBRepository


def _client(repository: DuckDBRepository) -> TestClient:
    app.dependency_overrides[get_repository] = lambda: repository
    app.dependency_overrides[get_universe] = load_universe
    return TestClient(app)


def _seeded_repository(symbols: list[str], sessions: int = 25) -> DuckDBRepository:
    repository = DuckDBRepository(":memory:")
    dates = pd.date_range(end=pd.Timestamp("2026-09-17"), periods=sessions, freq="D")
    frames = [
        pd.DataFrame(
            {
                "symbol": symbol,
                "date": dates,
                "nav": 100.0,
                "shares": 1_000_000.0,
                # A steady +1M per session, so every window is a round number.
                "flow": 1_000_000.0,
            }
        )
        for symbol in symbols
    ]
    repository.upsert_flows(pd.concat(frames, ignore_index=True), "ssga", datetime(2026, 9, 17))
    return repository


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_empty_cache_returns_no_sectors_instead_of_an_error():
    repository = DuckDBRepository(":memory:")

    response = _client(repository).get("/api/flows")

    assert response.status_code == 200
    body = response.json()
    assert body["sectors"] == []
    assert body["as_of"] is None
    assert body["windows"] == list(FLOW_WINDOWS)
    repository.close()


def test_cached_flows_are_summed_over_each_window():
    sectors = [i.symbol for i in load_universe().instruments if i.category == "sectors"]
    repository = _seeded_repository(sectors)

    body = _client(repository).get("/api/flows").json()

    assert len(body["sectors"]) == len(sectors)
    row = body["sectors"][0]
    assert row["symbol"] in sectors
    # 1m per session accumulates linearly across the ladder.
    assert row["flows"]["1D"] == 1_000_000.0
    assert row["flows"]["5D"] == 5_000_000.0
    assert row["flows"]["20D"] == 20_000_000.0
    repository.close()


def test_a_window_longer_than_the_history_sums_what_exists():
    sectors = [i.symbol for i in load_universe().instruments if i.category == "sectors"]
    repository = _seeded_repository(sectors, sessions=3)

    body = _client(repository).get("/api/flows").json()

    assert body["sectors"][0]["flows"]["20D"] == 3_000_000.0
    repository.close()


def test_a_sector_with_no_cached_rows_is_omitted():
    sectors = [i.symbol for i in load_universe().instruments if i.category == "sectors"]
    repository = _seeded_repository(sectors[:2])

    body = _client(repository).get("/api/flows").json()

    assert [row["symbol"] for row in body["sectors"]] == sectors[:2]
    repository.close()


def test_an_all_unknown_window_reports_none_rather_than_zero():
    """Unknown flows follow a dropped bad row. Reporting 0 would read as
    'no money moved', which is a different claim."""
    repository = DuckDBRepository(":memory:")
    frame = pd.DataFrame(
        {
            "symbol": "XLK",
            "date": pd.date_range(end=pd.Timestamp("2026-09-17"), periods=3, freq="D"),
            "nav": 100.0,
            "shares": 1_000_000.0,
            "flow": [float("nan")] * 3,
        }
    )
    repository.upsert_flows(frame, "ssga", datetime(2026, 9, 17))

    body = _client(repository).get("/api/flows").json()

    assert body["sectors"][0]["flows"]["1D"] is None
    repository.close()
