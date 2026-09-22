from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from app.storage.duckdb_repository import DuckDBRepository


def _bars() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "symbol": ["AAA", "AAA"],
            "timestamp": [datetime(2026, 1, 1), datetime(2026, 1, 2)],
            "open": [10.0, 11.0],
            "high": [10.5, 11.5],
            "low": [9.5, 10.5],
            "close": [10.2, 11.2],
            "volume": [1000.0, 1100.0],
        }
    )


@pytest.fixture
def repository():
    repo = DuckDBRepository(":memory:")
    yield repo
    repo.close()


def test_upsert_then_get_prices_round_trips(repository):
    retrieved_at = datetime.now(UTC)
    repository.upsert_prices(_bars(), interval="1d", provider="yfinance", retrieved_at=retrieved_at)

    result = repository.get_prices(
        ["AAA"], datetime(2025, 1, 1), datetime(2027, 1, 1), interval="1d"
    )

    assert len(result) == 2
    assert result.iloc[0]["close"] == 10.2


def test_reupserting_same_rows_does_not_duplicate(repository):
    retrieved_at = datetime.now(UTC)
    repository.upsert_prices(_bars(), interval="1d", provider="yfinance", retrieved_at=retrieved_at)
    repository.upsert_prices(_bars(), interval="1d", provider="yfinance", retrieved_at=retrieved_at)

    result = repository.get_prices(
        ["AAA"], datetime(2025, 1, 1), datetime(2027, 1, 1), interval="1d"
    )

    assert len(result) == 2


def test_latest_timestamps_reflect_most_recent_bar_per_symbol(repository):
    repository.upsert_prices(
        _bars(), interval="1d", provider="yfinance", retrieved_at=datetime.now(UTC)
    )

    latest = repository.latest_timestamps(["AAA"], "1d")

    assert latest == {"AAA": datetime(2026, 1, 2)}


def test_latest_timestamps_omits_symbols_with_no_cached_data(repository):
    """An absent symbol is the signal that a full backfill is still needed."""
    repository.upsert_prices(
        _bars(), interval="1d", provider="yfinance", retrieved_at=datetime.now(UTC)
    )

    latest = repository.latest_timestamps(["AAA", "ZZZ"], "1d")

    assert set(latest) == {"AAA"}
    assert repository.latest_timestamps([], "1d") == {}


def test_latest_retrieved_at_reports_when_the_cache_was_last_written(repository):
    # A non-UTC input: the stored moment must not depend on either timezone.
    retrieved_at = datetime(2026, 1, 3, 7, 30, tzinfo=ZoneInfo("America/New_York"))
    repository.upsert_prices(
        _bars(), interval="1d", provider="yfinance", retrieved_at=retrieved_at
    )

    latest = repository.latest_retrieved_at("1d")
    assert latest == retrieved_at
    assert latest.tzinfo == UTC
    assert repository.latest_retrieved_at("1h") is None


def test_concurrent_reads_return_complete_frames(repository):
    """FastAPI serves this app's sync endpoints from a threadpool, so one
    repository is read by several threads at once. Sharing a single DuckDB
    connection made concurrent reads return None; each statement now runs on
    its own cursor.
    """
    repository.upsert_prices(
        _bars(), interval="1d", provider="yfinance", retrieved_at=datetime.now(UTC)
    )

    def read(_: int) -> int:
        frame = repository.get_prices(
            ["AAA"], datetime(2025, 1, 1), datetime(2027, 1, 1), interval="1d"
        )
        return len(frame)

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(read, range(40)))

    assert results == [2] * 40
