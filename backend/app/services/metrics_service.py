"""Pure calculation functions for market-rotation metrics.

Every function documents its formula and returns None (never raises, never
silently returns NaN) when there isn't enough data to compute a result.
"""

from __future__ import annotations

from typing import NamedTuple

import pandas as pd

RETURN_PERIODS = {"return_1d": 1, "return_5d": 5, "return_20d": 20}


class BreadthResult(NamedTuple):
    positive: int
    total: int
    ratio: float | None


def compute_return(closes: pd.Series, sessions: int) -> float | None:
    """N-session return: latest_close / close_N_sessions_ago - 1.

    Uses trading-session offsets (positional), not calendar-day subtraction.
    `closes` must already be sorted ascending by timestamp.
    """
    closes = closes.dropna()
    if len(closes) <= sessions:
        return None
    latest = closes.iloc[-1]
    base = closes.iloc[-1 - sessions]
    if base == 0:
        return None
    return float(latest / base - 1)


def compute_returns_table(prices: pd.DataFrame) -> pd.DataFrame:
    """Long-format prices (symbol, timestamp, close, ...) -> one row per symbol
    with return_1d/return_5d/return_20d columns."""
    rows = []
    for symbol, group in prices.sort_values("timestamp").groupby("symbol"):
        closes = group["close"]
        row = {"symbol": symbol}
        row.update({label: compute_return(closes, n) for label, n in RETURN_PERIODS.items()})
        rows.append(row)
    return pd.DataFrame(rows, columns=["symbol", *RETURN_PERIODS])


def relative_return(
    instrument_return: float | None, benchmark_return: float | None
) -> float | None:
    """Outperformance vs a benchmark over the same period. Positive = outperformed.

    Missing data arrives here as None or as NaN (pandas promotes None to NaN
    once a column holds any float), so both are normalized before comparing --
    an unguarded NaN would propagate silently instead of returning None.
    """
    instrument_return = clean_number(instrument_return)
    benchmark_return = clean_number(benchmark_return)
    if instrument_return is None or benchmark_return is None:
        return None
    return instrument_return - benchmark_return


def sector_breadth(returns: dict[str, float | None]) -> BreadthResult:
    """Share of instruments with a positive return, ignoring missing data."""
    known = [v for v in returns.values() if v is not None]
    positive = sum(1 for v in known if v > 0)
    total = len(known)
    ratio = positive / total if total else None
    return BreadthResult(positive=positive, total=total, ratio=ratio)


def sector_dispersion(returns: dict[str, float | None]) -> float | None:
    """Cross-sectional stddev of returns. None if fewer than 2 data points."""
    known = pd.Series([v for v in returns.values() if v is not None])
    if len(known) < 2:
        return None
    return float(known.std())


def group_mean_return(returns: dict[str, float | None], members: list[str]) -> float | None:
    values = [returns[m] for m in members if returns.get(m) is not None]
    if not values:
        return None
    return sum(values) / len(values)


def defensive_cyclical_spread(
    returns_5d: dict[str, float | None], defensive: list[str], cyclical: list[str]
) -> dict[str, float | None]:
    """PRD section 24: DefensiveSpread5D = mean(defensive 5D) - mean(cyclical 5D)."""
    defensive_mean = group_mean_return(returns_5d, defensive)
    cyclical_mean = group_mean_return(returns_5d, cyclical)
    spread = relative_return(defensive_mean, cyclical_mean)
    return {"defensive_5d": defensive_mean, "cyclical_5d": cyclical_mean, "spread_5d": spread}


def compute_ratio_returns(
    prices: pd.DataFrame, numerator_symbol: str, denominator_symbol: str
) -> dict[str, float | None]:
    """RelativeRatio(t) = Price(numerator,t) / Price(denominator,t); returns of that ratio series.

    Used for RSP/SPY (equal-weight breadth proxy), HYG/LQD (credit risk proxy),
    and IVW/IVE (growth vs value style proxy).
    """
    numerator = _closes_by_timestamp(prices, numerator_symbol)
    denominator = _closes_by_timestamp(prices, denominator_symbol)
    aligned = pd.concat([numerator, denominator], axis=1, join="inner")
    if aligned.empty:
        return dict.fromkeys(RETURN_PERIODS, None)

    ratio = (aligned.iloc[:, 0] / aligned.iloc[:, 1]).reset_index(drop=True)
    return {label: compute_return(ratio, n) for label, n in RETURN_PERIODS.items()}


def classify_quadrant(x: float | None, y: float | None) -> str | None:
    """PRD section 17. x = 20D relative return vs SPY, y = 5D relative return vs SPY.

    Returns None for missing coordinates. NaN is normalized first: every
    comparison against NaN is False, so an unguarded NaN would fall through
    to the final `return "LAGGING"` and label unknown data as the worst quadrant.
    """
    x = clean_number(x)
    y = clean_number(y)
    if x is None or y is None:
        return None
    if x > 0 and y > 0:
        return "LEADING"
    if x <= 0 and y > 0:
        return "IMPROVING"
    if x > 0 and y <= 0:
        return "WEAKENING"
    return "LAGGING"


def compute_sector_table(
    prices: pd.DataFrame, sector_symbols: list[str], benchmark_symbol: str
) -> pd.DataFrame:
    """Per-sector returns, relative performance vs SPY, and rotation-chart coordinates."""
    returns = compute_returns_table(prices).set_index("symbol")
    benchmark = returns.loc[benchmark_symbol] if benchmark_symbol in returns.index else None

    rows = []
    for symbol in sector_symbols:
        r = returns.loc[symbol] if symbol in returns.index else dict.fromkeys(RETURN_PERIODS, None)
        bench_5d = benchmark["return_5d"] if benchmark is not None else None
        bench_20d = benchmark["return_20d"] if benchmark is not None else None
        vs_spy_5d = relative_return(r["return_5d"], bench_5d)
        vs_spy_20d = relative_return(r["return_20d"], bench_20d)

        rows.append(
            {
                "symbol": symbol,
                "return_1d": r["return_1d"],
                "return_5d": r["return_5d"],
                "return_20d": r["return_20d"],
                "vs_spy_5d": vs_spy_5d,
                "vs_spy_20d": vs_spy_20d,
                "quadrant": classify_quadrant(vs_spy_20d, vs_spy_5d),
            }
        )
    return pd.DataFrame(rows)


def compute_rotation_trail(
    prices: pd.DataFrame,
    sector_symbols: list[str],
    benchmark_symbol: str,
    trail_length: int = 5,
) -> dict[str, list[dict[str, float | None]]]:
    """Rotation coordinates for the `trail_length` sessions before the latest one,
    oldest first, per sector. Pair with compute_sector_table's current x/y to draw
    a fading trail ending at today's position (PRD section 17, optional trail).
    """
    # Narrow the frame once. compute_sector_table only reads the sectors and the
    # benchmark, but recomputes returns for every symbol it is handed -- and it
    # runs once per trail point, so the whole universe would otherwise be
    # recomputed `trail_length` times over.
    prices = prices[prices["symbol"].isin([*sector_symbols, benchmark_symbol])]
    timestamps = sorted(prices["timestamp"].unique())
    trail: dict[str, list[dict[str, float | None]]] = {symbol: [] for symbol in sector_symbols}

    for offset in range(trail_length, 0, -1):
        cutoff_index = len(timestamps) - 1 - offset
        if cutoff_index < 0:
            for symbol in sector_symbols:
                trail[symbol].append({"x": None, "y": None})
            continue

        window = prices[prices["timestamp"] <= timestamps[cutoff_index]]
        table = compute_sector_table(window, sector_symbols, benchmark_symbol).set_index("symbol")
        for symbol in sector_symbols:
            if symbol in table.index:
                point = {
                    "x": clean_number(table.loc[symbol, "vs_spy_20d"]),
                    "y": clean_number(table.loc[symbol, "vs_spy_5d"]),
                }
            else:
                point = {"x": None, "y": None}
            trail[symbol].append(point)

    return trail


def clean_number(value: object) -> float | None:
    """Normalize a possibly-NaN/None/pandas scalar into a JSON-safe float or None."""
    if value is None:
        return None
    if pd.isna(value):
        return None
    return float(value)


def _closes_by_timestamp(prices: pd.DataFrame, symbol: str) -> pd.Series:
    subset = prices[prices["symbol"] == symbol].sort_values("timestamp")
    return subset.set_index("timestamp")["close"]
