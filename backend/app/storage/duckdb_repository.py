from __future__ import annotations

from datetime import datetime
from pathlib import Path

import duckdb
import pandas as pd

from app.providers.base import PRICE_COLUMNS

DEFAULT_DB_PATH = Path(__file__).parents[2] / "data" / "market.duckdb"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS market_prices (
    symbol VARCHAR NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    interval VARCHAR NOT NULL,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume DOUBLE,
    provider VARCHAR NOT NULL,
    retrieved_at TIMESTAMP NOT NULL,
    PRIMARY KEY (symbol, timestamp, interval)
)
"""

_STORED_COLUMNS = [
    "symbol",
    "timestamp",
    "interval",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "provider",
    "retrieved_at",
]


class DuckDBRepository:
    """Local cache of OHLCV bars. Never committed to git — see .gitignore."""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        if str(db_path) != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = duckdb.connect(str(db_path))
        self._conn.execute(_SCHEMA)

    def upsert_prices(
        self,
        df: pd.DataFrame,
        interval: str,
        provider: str,
        retrieved_at: datetime,
    ) -> int:
        """Insert/update bars. Re-running with the same data does not duplicate rows."""
        if df.empty:
            return 0

        to_insert = df.copy()
        to_insert["interval"] = interval
        to_insert["provider"] = provider
        to_insert["retrieved_at"] = retrieved_at
        to_insert = to_insert[_STORED_COLUMNS]

        self._conn.register("to_insert", to_insert)
        try:
            self._conn.execute("INSERT OR REPLACE INTO market_prices SELECT * FROM to_insert")
        finally:
            self._conn.unregister("to_insert")
        return len(to_insert)

    def get_prices(
        self,
        symbols: list[str],
        start: datetime,
        end: datetime,
        interval: str,
    ) -> pd.DataFrame:
        if not symbols:
            return pd.DataFrame(columns=PRICE_COLUMNS)

        placeholders = ",".join("?" * len(symbols))
        query = f"""
            SELECT symbol, timestamp, open, high, low, close, volume
            FROM market_prices
            WHERE symbol IN ({placeholders}) AND interval = ? AND timestamp BETWEEN ? AND ?
            ORDER BY symbol, timestamp
        """
        return self._conn.execute(query, [*symbols, interval, start, end]).fetch_df()

    def latest_timestamp(self, symbol: str, interval: str) -> datetime | None:
        row = self._conn.execute(
            "SELECT max(timestamp) FROM market_prices WHERE symbol = ? AND interval = ?",
            [symbol, interval],
        ).fetchone()
        return row[0] if row and row[0] is not None else None

    def close(self) -> None:
        self._conn.close()
