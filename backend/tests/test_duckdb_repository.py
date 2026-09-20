from __future__ import annotations

from datetime import UTC, datetime

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


def test_latest_timestamp_reflects_most_recent_bar(repository):
    repository.upsert_prices(
        _bars(), interval="1d", provider="yfinance", retrieved_at=datetime.now(UTC)
    )

    latest = repository.latest_timestamp("AAA", "1d")

    assert latest == datetime(2026, 1, 2)


def test_latest_timestamp_is_none_when_symbol_unknown(repository):
    assert repository.latest_timestamp("ZZZ", "1d") is None
