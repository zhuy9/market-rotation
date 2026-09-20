"""Refreshes SPDR sector ETF flows into the local cache."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pandas as pd

from app.providers import spdr_flows
from app.storage.duckdb_repository import DuckDBRepository

PROVIDER_NAME = "ssga"


@dataclass(frozen=True)
class FlowRefreshResult:
    updated_symbols: int
    failed_symbols: list[str]
    rows: int
    as_of: datetime


def refresh_flows(repository: DuckDBRepository, symbols: list[str]) -> FlowRefreshResult:
    """Fetch every symbol's flow history and cache it.

    A symbol whose download or parse fails is reported in `failed_symbols`
    rather than aborting the run, so one delisted or renamed fund cannot take
    the whole refresh down with it.
    """
    now = datetime.now(UTC)
    frames: list[pd.DataFrame] = []
    failed: list[str] = []

    for symbol in symbols:
        frame = spdr_flows.fetch_flows(symbol)
        if frame.empty:
            failed.append(symbol)
            continue
        frames.append(frame)

    rows = 0
    if frames:
        combined = pd.concat(frames, ignore_index=True)
        rows = repository.upsert_flows(combined, PROVIDER_NAME, now)

    return FlowRefreshResult(
        updated_symbols=len(frames), failed_symbols=failed, rows=rows, as_of=now
    )
