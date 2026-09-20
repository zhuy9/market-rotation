"""Refresh SPDR sector flows into the local cache, then print them.

    uv run python scripts/spdr_flows_report.py

Fetches every sector fund, stores it in the local DuckDB cache (gitignored),
reads it back, and prints net flow over the last 1, 5, and 20 sessions. The
numbers come from the stored rows, so a clean run also proves the round trip.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime

import pandas as pd

from app.config.universe import load_universe
from app.services.flow_service import refresh_flows
from app.storage.duckdb_repository import DuckDBRepository

WINDOWS = (1, 5, 20)
_EPOCH = datetime(2000, 1, 1)


def main() -> int:
    universe = load_universe()
    sectors = [i for i in universe.instruments if i.category == "sectors"]
    symbols = [i.symbol for i in sectors]

    repository = DuckDBRepository()
    try:
        result = refresh_flows(repository, symbols)
        print(
            f"stored {result.rows:,} rows for {result.updated_symbols}/{len(symbols)} funds",
            f"(failed: {', '.join(result.failed_symbols) or 'none'})",
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
        rows.append(
            (instrument.symbol, instrument.name, *(flows.tail(w).sum() / 1e6 for w in WINDOWS))
        )
    rows.sort(key=lambda row: -row[-1])

    as_of = pd.to_datetime(stored["date"]).max().date()
    print(f"\nSPDR sector net flows  (as of {as_of})   $ millions\n")
    print(f"{'':5} {'Sector':<24} " + " ".join(f"{f'{w}D':>10}" for w in WINDOWS))
    print("-" * 63)
    for symbol, name, *values in rows:
        print(f"{symbol:5} {name:<24} " + " ".join(f"{v:>+10,.0f}" for v in values))
    print("-" * 63)
    totals = [sum(row[i] for row in rows) for i in range(2, 2 + len(WINDOWS))]
    print(f"{'':5} {'NET':<24} " + " ".join(f"{t:>+10,.0f}" for t in totals))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
