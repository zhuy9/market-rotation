"""Refresh SPDR sector flows into the local cache, then print them.

    uv run python scripts/spdr_flows_report.py

Fetches every sector fund, stores it in the local DuckDB cache (gitignored),
reads it back, and prints cumulative net flow over a ladder of trailing
horizons. The numbers come from the stored rows, so a clean run also proves the
round trip.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime

import duckdb
import pandas as pd

from app.config.universe import load_universe
from app.services.flow_service import FLOW_WINDOWS, refresh_flows
from app.storage.duckdb_repository import DuckDBRepository

# Shared with the /api/flows endpoint so the table and the dashboard cannot
# drift apart.
WINDOWS = FLOW_WINDOWS

_COL = 9
_LABELS = 30
_EPOCH = datetime(2000, 1, 1)


def main() -> int:
    sectors = [i for i in load_universe().instruments if i.category == "sectors"]
    symbols = [i.symbol for i in sectors]

    try:
        repository = DuckDBRepository()
    except duckdb.IOException:
        # DuckDB allows a single writer, and the API server holds the same file.
        print(
            "Could not open the local cache — the backend is probably running.\n"
            "Stop `uvicorn app.main:app --reload` and try again.",
            file=sys.stderr,
        )
        return 1

    try:
        result = refresh_flows(repository, symbols)
        failed = ", ".join(result.failed_symbols) or "none"
        print(
            f"stored {result.rows:,} rows for "
            f"{result.updated_symbols}/{len(symbols)} funds (failed: {failed})"
        )
        stored = repository.get_flows(symbols, _EPOCH, datetime.now(UTC).replace(tzinfo=None))
    finally:
        repository.close()

    if stored.empty:
        print("no flows stored — is the source reachable?", file=sys.stderr)
        return 1

    rows = []
    for instrument in sectors:
        flows = stored.loc[stored["symbol"] == instrument.symbol, "flow"]
        if flows.empty:
            continue
        totals = (flows.tail(w).sum() / 1e6 for w in WINDOWS)
        rows.append((instrument.symbol, instrument.name, *totals))
    rows.sort(key=lambda row: -row[-1])

    as_of = pd.to_datetime(stored["date"]).max().date()
    width = _LABELS + _COL * len(WINDOWS)
    print(f"\nSPDR sector cumulative net flows  (as of {as_of})   $ millions\n")
    print(f"{'':5}{'Sector':<25}" + "".join(f"{f'{w}D':>{_COL}}" for w in WINDOWS))
    print("-" * width)
    for symbol, name, *values in rows:
        print(f"{symbol:5}{name:<25}" + "".join(f"{v:>+{_COL},.0f}" for v in values))
    print("-" * width)
    totals = (sum(row[i] for row in rows) for i in range(2, 2 + len(WINDOWS)))
    print(f"{'':5}{'NET':<25}" + "".join(f"{t:>+{_COL},.0f}" for t in totals))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
