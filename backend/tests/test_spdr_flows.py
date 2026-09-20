"""Flow parsing is tested against synthetic sheets only — never a live download."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO

import pandas as pd
import pytest

from app.providers import spdr_flows
from app.providers.spdr_flows import FLOW_COLUMNS, fetch_flows, parse_navhist
from app.services.flow_service import refresh_flows
from app.storage.duckdb_repository import DuckDBRepository


def build_sheet(rows: list[list], symbol: str = "XLV") -> bytes:
    """A workbook shaped like State Street's: three title rows, a header row,
    newest-first data, then a prospectus paragraph sharing the date column."""
    layout = [
        ["Fund Name:", f"Test {symbol} Fund", None, None],
        ["Ticker Symbol:", symbol, None, None],
        [None, None, None, None],
        ["Date", "NAV", "Shares Outstanding", "Total Net Assets"],
        *reversed(rows),
        [None, None, None, None],
        ["Before investing in a fund, consider its investment objectives...", None, None, None],
    ]
    buffer = BytesIO()
    pd.DataFrame(layout).to_excel(buffer, index=False, header=False)
    return buffer.getvalue()


# nav * shares matches total net assets on every row, as the real file does.
GOOD_ROWS = [
    ["14-Sep-2026", 100.0, 1_000_000, 100_000_000.0],
    ["15-Sep-2026", 101.0, 1_200_000, 121_200_000.0],
    ["16-Sep-2026", 102.0, 1_100_000, 112_200_000.0],
]


def test_flow_prices_the_share_change_at_that_days_nav():
    result = parse_navhist(build_sheet(GOOD_ROWS), "xlv")

    assert list(result.columns) == FLOW_COLUMNS
    assert result["symbol"].unique().tolist() == ["XLV"]
    # 200k shares created at 101, then 100k redeemed at 102.
    assert result["flow"].tolist()[1:] == pytest.approx([20_200_000.0, -10_200_000.0])


def test_first_row_has_no_flow_because_it_has_no_previous_day():
    result = parse_navhist(build_sheet(GOOD_ROWS), "XLV")

    assert pd.isna(result["flow"].iloc[0])


def test_rows_are_returned_oldest_first_though_the_sheet_is_newest_first():
    result = parse_navhist(build_sheet(GOOD_ROWS), "XLV")

    assert result["date"].is_monotonic_increasing
    assert result["date"].iloc[0] == pd.Timestamp("2026-09-14")


def test_title_and_prospectus_rows_are_not_mistaken_for_data():
    result = parse_navhist(build_sheet(GOOD_ROWS), "XLV")

    assert len(result) == len(GOOD_ROWS)


def test_a_row_whose_assets_contradict_nav_times_shares_is_dropped():
    """State Street's own XLV file has one such row (2014-10-07). Trusting it
    would report a fabricated flow."""
    rows = [
        ["14-Sep-2026", 100.0, 1_000_000, 100_000_000.0],
        ["15-Sep-2026", 101.0, 1_200_000, 999_999_999.0],  # contradicts itself
        ["16-Sep-2026", 102.0, 1_100_000, 112_200_000.0],
    ]

    result = parse_navhist(build_sheet(rows), "XLV")

    assert pd.Timestamp("2026-09-15") not in result["date"].tolist()
    # The next day differenced against the bad share count, so it is unknown too
    # rather than silently reporting a two-day move as one day's flow.
    assert pd.isna(result.loc[result["date"] == pd.Timestamp("2026-09-16"), "flow"].iloc[0])


def test_fetch_flows_returns_empty_instead_of_raising_when_the_download_fails(monkeypatch):
    def boom(symbol: str) -> bytes:
        raise OSError("ssga.com unreachable")

    monkeypatch.setattr(spdr_flows, "_download", boom)

    result = fetch_flows("XLV")

    assert result.empty
    assert list(result.columns) == FLOW_COLUMNS


def test_fetch_flows_returns_empty_instead_of_raising_when_the_sheet_is_unparsable(monkeypatch):
    monkeypatch.setattr(spdr_flows, "_download", lambda symbol: b"not a spreadsheet")

    assert fetch_flows("XLV").empty


def test_refresh_reports_a_failed_symbol_without_losing_the_others(monkeypatch):
    def fake_fetch(symbol: str) -> pd.DataFrame:
        if symbol == "XLE":
            return pd.DataFrame(columns=FLOW_COLUMNS)
        return parse_navhist(build_sheet(GOOD_ROWS), symbol)

    monkeypatch.setattr(spdr_flows, "fetch_flows", fake_fetch)
    repository = DuckDBRepository(":memory:")

    result = refresh_flows(repository, ["XLV", "XLE", "XLK"])

    assert result.failed_symbols == ["XLE"]
    assert result.updated_symbols == 2
    assert result.rows == 2 * len(GOOD_ROWS)
    repository.close()


def test_stored_flows_survive_a_round_trip_and_do_not_duplicate_on_rerun():
    repository = DuckDBRepository(":memory:")
    frame = parse_navhist(build_sheet(GOOD_ROWS), "XLV")
    retrieved_at = datetime(2026, 9, 17, 12, 0)

    repository.upsert_flows(frame, "ssga", retrieved_at)
    repository.upsert_flows(frame, "ssga", retrieved_at)

    stored = repository.get_flows(["XLV"], datetime(2026, 9, 1), datetime(2026, 9, 30))
    assert len(stored) == len(GOOD_ROWS)
    assert stored["flow"].tolist()[1:] == pytest.approx([20_200_000.0, -10_200_000.0])
    repository.close()


def test_get_flows_with_no_symbols_returns_an_empty_frame():
    repository = DuckDBRepository(":memory:")

    stored = repository.get_flows([], datetime(2026, 9, 1), datetime(2026, 9, 30))

    assert stored.empty
    assert list(stored.columns) == FLOW_COLUMNS
    repository.close()


def test_a_sheet_with_no_data_rows_yields_no_flows():
    """A header-only file during a publishing outage must not raise."""
    result = parse_navhist(build_sheet([]), "XLV")

    assert result.empty
    assert list(result.columns) == FLOW_COLUMNS
