from __future__ import annotations

import statistics

import pandas as pd
import pytest

from app.services.metrics_service import (
    classify_quadrant,
    compute_ratio_returns,
    compute_return,
    compute_returns_table,
    compute_sector_table,
    defensive_cyclical_spread,
    group_mean_return,
    relative_return,
    sector_breadth,
    sector_dispersion,
)

# 25 sessions, closes 100..124. Known exact returns:
#   1D  = 124/123 - 1
#   5D  = 124/119 - 1
#   20D = 124/104 - 1
RAMP = [float(v) for v in range(100, 125)]


def _price_frame(symbol: str, closes: list[float], start: str = "2026-01-01") -> pd.DataFrame:
    timestamps = pd.date_range(start, periods=len(closes), freq="D")
    return pd.DataFrame({"symbol": symbol, "timestamp": timestamps, "close": closes})


# --- compute_return -----------------------------------------------------


def test_compute_return_matches_expected_value():
    closes = pd.Series(RAMP)

    assert compute_return(closes, 1) == pytest.approx(124 / 123 - 1)
    assert compute_return(closes, 5) == pytest.approx(124 / 119 - 1)
    assert compute_return(closes, 20) == pytest.approx(124 / 104 - 1)


def test_compute_return_none_when_insufficient_history():
    closes = pd.Series([100.0, 101.0, 102.0])

    assert compute_return(closes, 20) is None


def test_compute_return_none_for_zero_base():
    closes = pd.Series([0.0, 100.0])

    assert compute_return(closes, 1) is None


def test_returns_use_trading_sessions_not_calendar_days():
    """A 3x-wider calendar gap between sessions must not change the N-session return."""
    regular = _price_frame("XLE", RAMP, start="2026-01-01")
    irregular_dates = [pd.Timestamp("2026-01-01") + pd.Timedelta(days=3 * i) for i in range(25)]
    irregular = pd.DataFrame({"symbol": "XLE", "timestamp": irregular_dates, "close": RAMP})

    regular_row = compute_returns_table(regular).iloc[0]
    irregular_row = compute_returns_table(irregular).iloc[0]

    assert regular_row["return_1d"] == pytest.approx(irregular_row["return_1d"])
    assert regular_row["return_5d"] == pytest.approx(irregular_row["return_5d"])
    assert regular_row["return_20d"] == pytest.approx(irregular_row["return_20d"])
    assert regular_row["return_20d"] == pytest.approx(124 / 104 - 1)


def test_compute_returns_table_handles_multiple_symbols():
    prices = pd.concat(
        [_price_frame("SPY", RAMP), _price_frame("XLE", [c * 1.1 for c in RAMP])],
        ignore_index=True,
    )

    table = compute_returns_table(prices).set_index("symbol")

    assert set(table.index) == {"SPY", "XLE"}
    assert table.loc["SPY", "return_1d"] == pytest.approx(124 / 123 - 1)
    # Scaling every close by a constant factor doesn't change the return.
    assert table.loc["XLE", "return_1d"] == pytest.approx(124 / 123 - 1)


# --- relative_return / breadth / dispersion ------------------------------


def test_relative_return_is_outperformance_vs_benchmark():
    assert relative_return(0.05, 0.02) == pytest.approx(0.03)


def test_relative_return_none_when_either_side_missing():
    assert relative_return(None, 0.02) is None
    assert relative_return(0.05, None) is None


def test_sector_breadth_counts_positive_over_available():
    returns = {f"S{i}": 0.01 for i in range(7)} | {f"S{i}": -0.01 for i in range(7, 11)}

    result = sector_breadth(returns)

    assert result == (7, 11, pytest.approx(7 / 11))


def test_sector_breadth_ignores_missing_data_in_denominator():
    returns = {"A": 0.01, "B": -0.01, "C": None}

    result = sector_breadth(returns)

    assert result.positive == 1
    assert result.total == 2
    assert result.ratio == pytest.approx(0.5)


def test_sector_breadth_ratio_none_when_nothing_available():
    result = sector_breadth({"A": None, "B": None})

    assert result.ratio is None


def test_sector_dispersion_matches_stdlib_stdev():
    returns = {"A": 0.01, "B": 0.02, "C": 0.03, "D": 0.04}

    result = sector_dispersion(returns)

    assert result == pytest.approx(statistics.stdev([0.01, 0.02, 0.03, 0.04]))


def test_sector_dispersion_none_with_fewer_than_two_values():
    assert sector_dispersion({"A": 0.01}) is None
    assert sector_dispersion({"A": None, "B": None}) is None


# --- defensive/cyclical spread -------------------------------------------


def test_group_mean_return_ignores_missing_and_unknown_members():
    returns = {"XLV": 0.02, "XLP": 0.04, "XLU": None}

    assert group_mean_return(returns, ["XLV", "XLP", "XLU", "NOTLISTED"]) == pytest.approx(0.03)


def test_defensive_cyclical_spread_positive_when_defensive_outperforms():
    returns_5d = {"XLV": 0.03, "XLP": 0.03, "XLU": 0.03, "XLK": -0.01, "XLY": -0.01}

    result = defensive_cyclical_spread(returns_5d, ["XLV", "XLP", "XLU"], ["XLK", "XLY"])

    assert result["defensive_5d"] == pytest.approx(0.03)
    assert result["cyclical_5d"] == pytest.approx(-0.01)
    assert result["spread_5d"] == pytest.approx(0.04)


def test_defensive_cyclical_spread_none_when_a_group_has_no_data():
    result = defensive_cyclical_spread({"XLV": 0.03}, ["XLV"], ["XLK"])

    assert result["cyclical_5d"] is None
    assert result["spread_5d"] is None


# --- ratio returns (RSP/SPY, HYG/LQD) -------------------------------------


def test_compute_ratio_returns_matches_manual_ratio_calculation():
    # SPY flat at 100 so RSP/SPY ratio == RSP/100, same shape as the RAMP test.
    prices = pd.concat(
        [_price_frame("RSP", RAMP), _price_frame("SPY", [100.0] * len(RAMP))],
        ignore_index=True,
    )

    result = compute_ratio_returns(prices, "RSP", "SPY")

    assert result["return_1d"] == pytest.approx(124 / 123 - 1)
    assert result["return_5d"] == pytest.approx(124 / 119 - 1)
    assert result["return_20d"] == pytest.approx(124 / 104 - 1)


def test_compute_ratio_returns_all_none_when_symbol_missing():
    prices = _price_frame("SPY", RAMP)

    result = compute_ratio_returns(prices, "RSP", "SPY")

    assert result == {"return_1d": None, "return_5d": None, "return_20d": None}


# --- rotation quadrants ----------------------------------------------------


@pytest.mark.parametrize(
    "x,y,expected",
    [
        (0.01, 0.01, "LEADING"),
        (-0.01, 0.01, "IMPROVING"),
        (0.0, 0.01, "IMPROVING"),
        (0.01, -0.01, "WEAKENING"),
        (0.01, 0.0, "WEAKENING"),
        (-0.01, -0.01, "LAGGING"),
        (0.0, 0.0, "LAGGING"),
    ],
)
def test_classify_quadrant(x, y, expected):
    assert classify_quadrant(x, y) == expected


def test_classify_quadrant_none_when_data_missing():
    assert classify_quadrant(None, 0.01) is None
    assert classify_quadrant(0.01, None) is None


# --- sector table (integration of the above) ------------------------------


def test_compute_sector_table_shape_and_quadrants():
    # Scaling by a constant leaves % returns unchanged, so these use a steeper/
    # shallower daily step than SPY's RAMP to produce genuine out/underperformance.
    xle_closes = [100.0 + 2 * i for i in range(25)]
    xlu_closes = [100.0 + 0.5 * i for i in range(25)]
    prices = pd.concat(
        [
            _price_frame("SPY", RAMP),
            _price_frame("XLE", xle_closes),  # steeper than SPY: outperforms
            _price_frame("XLU", xlu_closes),  # shallower than SPY: underperforms
        ],
        ignore_index=True,
    )

    table = compute_sector_table(prices, ["XLE", "XLU", "XLRE"], "SPY").set_index("symbol")

    assert table.loc["XLE", "vs_spy_5d"] > 0
    assert table.loc["XLE", "quadrant"] == "LEADING"
    assert table.loc["XLU", "vs_spy_5d"] < 0
    assert table.loc["XLU", "quadrant"] == "LAGGING"
    # XLRE has no price data at all: controlled missing result, not a crash.
    # (pandas promotes a column's None entries to NaN once mixed with values.)
    assert pd.isna(table.loc["XLRE", "return_1d"])
    assert pd.isna(table.loc["XLRE", "quadrant"])
