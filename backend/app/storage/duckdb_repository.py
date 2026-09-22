from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from threading import Lock

import duckdb
import pandas as pd

from app.providers.base import PRICE_COLUMNS
from app.providers.spdr_flows import FLOW_COLUMNS

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

_FLOW_SCHEMA = """
CREATE TABLE IF NOT EXISTS fund_flows (
    symbol VARCHAR NOT NULL,
    date DATE NOT NULL,
    nav DOUBLE,
    shares DOUBLE,
    flow DOUBLE,
    provider VARCHAR NOT NULL,
    retrieved_at TIMESTAMP NOT NULL,
    PRIMARY KEY (symbol, date)
)
"""

_FLOW_STORED_COLUMNS = ["symbol", "date", "nav", "shares", "flow", "provider", "retrieved_at"]

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
    """Local cache of OHLCV bars. Never committed to git — see .gitignore.

    FastAPI runs this app's sync endpoints in a threadpool, so several requests
    can reach one repository instance at once. A DuckDB connection is not
    thread-safe: sharing it returns None from concurrent reads and can deadlock
    a read/write mix. So every statement runs on its own `cursor()` (DuckDB's
    documented way to use one database from several threads), and writes take a
    lock because concurrent writers raise a transaction conflict instead.
    """

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        if str(db_path) != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = duckdb.connect(str(db_path))
        self._conn.execute(_SCHEMA)
        self._conn.execute(_FLOW_SCHEMA)
        self._write_lock = Lock()

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
        to_insert["retrieved_at"] = _to_utc_naive(retrieved_at)
        to_insert = to_insert[_STORED_COLUMNS]

        with self._write_lock:
            cursor = self._conn.cursor()
            cursor.register("to_insert", to_insert)
            try:
                cursor.execute("INSERT OR REPLACE INTO market_prices SELECT * FROM to_insert")
            finally:
                cursor.unregister("to_insert")
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
        return self._conn.cursor().execute(query, [*symbols, interval, start, end]).fetch_df()

    def latest_timestamps(self, symbols: list[str], interval: str) -> dict[str, datetime]:
        """Most recent cached bar per symbol. Symbols with no cached data at all
        are absent from the result, which is how callers spot that a full
        backfill is still needed rather than an incremental top-up.
        """
        if not symbols:
            return {}

        placeholders = ",".join("?" * len(symbols))
        query = f"""
            SELECT symbol, max(timestamp) FROM market_prices
            WHERE symbol IN ({placeholders}) AND interval = ?
            GROUP BY symbol
        """
        rows = self._conn.cursor().execute(query, [*symbols, interval]).fetchall()
        return {symbol: latest for symbol, latest in rows if latest is not None}

    def latest_retrieved_at(self, interval: str) -> datetime | None:
        """When a provider last wrote to the cache (PRD section 13's `retrieved_at`)."""
        row = (
            self._conn.cursor()
            .execute("SELECT max(retrieved_at) FROM market_prices WHERE interval = ?", [interval])
            .fetchone()
        )
        return row[0].replace(tzinfo=UTC) if row and row[0] is not None else None

    def upsert_flows(self, df: pd.DataFrame, provider: str, retrieved_at: datetime) -> int:
        """Insert/update daily fund flows. Re-running with the same data does not
        duplicate rows."""
        if df.empty:
            return 0

        to_insert = df.copy()
        to_insert["provider"] = provider
        to_insert["retrieved_at"] = _to_utc_naive(retrieved_at)
        to_insert = to_insert[_FLOW_STORED_COLUMNS]

        with self._write_lock:
            cursor = self._conn.cursor()
            cursor.register("to_insert", to_insert)
            try:
                cursor.execute("INSERT OR REPLACE INTO fund_flows SELECT * FROM to_insert")
            finally:
                cursor.unregister("to_insert")
        return len(to_insert)

    def get_flows(self, symbols: list[str], start: datetime, end: datetime) -> pd.DataFrame:
        if not symbols:
            return pd.DataFrame(columns=FLOW_COLUMNS)

        placeholders = ",".join("?" * len(symbols))
        query = f"""
            SELECT symbol, date, nav, shares, flow
            FROM fund_flows
            WHERE symbol IN ({placeholders}) AND date BETWEEN ? AND ?
            ORDER BY symbol, date
        """
        return self._conn.cursor().execute(query, [*symbols, start, end]).fetch_df()

    def close(self) -> None:
        self._conn.close()


def _to_utc_naive(moment: datetime) -> datetime:
    """`retrieved_at` columns are zone-less TIMESTAMPs holding UTC. DuckDB would
    otherwise store an aware value in the server's local time, and the API would
    send it on as a zone-less string the browser reads as its own local time.
    Naive input is taken to be UTC already.
    """
    if moment.tzinfo is None:
        return moment
    return moment.astimezone(UTC).replace(tzinfo=None)
