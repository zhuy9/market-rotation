"""Refreshes SPDR sector ETF flows into the local cache."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pandas as pd

from app.config.universe import Universe
from app.models.schemas import FlowsResponse, SectorFlowOut
from app.providers import spdr_flows
from app.services.metrics_service import clean_number
from app.storage.duckdb_repository import DuckDBRepository

PROVIDER_NAME = "ssga"

# Trailing-session horizons. Spaced tighter at the short end because adjacent
# cumulative windows differ by exactly one session, so a full 1..20 ladder would
# be twenty near-identical columns.
FLOW_WINDOWS = (1, 2, 3, 5, 10, 15, 20)

_EPOCH = datetime(2000, 1, 1)


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


def build_flows(repository: DuckDBRepository, universe: Universe) -> FlowsResponse:
    """Cumulative net flow per sector over each trailing window."""
    sectors = [i for i in universe.instruments if i.category == "sectors"]
    stored = repository.get_flows([i.symbol for i in sectors], _EPOCH, datetime.now(UTC))

    if stored.empty:
        return FlowsResponse(as_of=None, windows=list(FLOW_WINDOWS), sectors=[])

    rows = []
    for instrument in sectors:
        flows = stored.loc[stored["symbol"] == instrument.symbol, "flow"]
        if flows.empty:
            continue
        rows.append(
            SectorFlowOut(
                symbol=instrument.symbol,
                name=instrument.name,
                # min_count keeps an all-unknown window as None instead of
                # reporting a fabricated zero.
                flows={
                    f"{w}D": clean_number(flows.tail(w).sum(min_count=1)) for w in FLOW_WINDOWS
                },
            )
        )

    return FlowsResponse(
        as_of=pd.to_datetime(stored["date"]).max(),
        windows=list(FLOW_WINDOWS),
        sectors=rows,
    )
