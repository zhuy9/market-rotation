"""Canary: fails if State Street changes the NAV history URL, format, or cadence.

Run on a schedule by .github/workflows/spdr-canary.yml. It downloads every
sector fund's sheet and checks it still parses into usable flows. Nothing is
stored and nothing is committed — this only reports that the source is intact.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta

from app.config.universe import load_universe
from app.providers.spdr_flows import fetch_flows

# Each fund has ~5,000 sessions of history. Anything near zero means the sheet
# parsed but produced nothing usable, which is a format change in disguise.
MIN_ROWS = 100

# The sheets already lag the session by a couple of days, and the canary only
# runs weekly, so a 7-day window would false-alarm over a holiday week. A feed
# that has genuinely stopped keeps aging past this on every later run.
MAX_STALENESS = timedelta(days=10)


def main() -> int:
    symbols = [i.symbol for i in load_universe().instruments if i.category == "sectors"]
    today = datetime.now(UTC).date()
    failures: list[str] = []

    for symbol in symbols:
        frame = fetch_flows(symbol)
        if len(frame) < MIN_ROWS:
            failures.append(f"{symbol}: {len(frame)} rows parsed (expected >= {MIN_ROWS})")
            continue

        latest = frame["date"].max().date()
        flows = int(frame["flow"].notna().sum())
        age = today - latest
        print(f"{symbol:5} {len(frame):5} rows  latest {latest}  {flows:5} flows  age {age.days}d")

        if flows < MIN_ROWS:
            failures.append(f"{symbol}: only {flows} usable flows")
        if age > MAX_STALENESS:
            failures.append(f"{symbol}: latest row is {age.days} days old ({latest})")

    if failures:
        print("\nSPDR source check FAILED:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    print(f"\nAll {len(symbols)} sector funds parsed cleanly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
