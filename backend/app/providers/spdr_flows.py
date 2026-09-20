"""Daily creation/redemption flows for the SPDR sector ETFs.

ETF shares are not created or destroyed when investors trade with each other.
They change only when an authorized participant creates or redeems them, so a
rise in shares outstanding is money entering the fund and a fall is money
leaving. Pricing that day-over-day change at the day's NAV gives the net dollar
flow, which is measured creation/redemption activity rather than a price-based
inference.

This is the ONLY module that knows about ssga.com URLs or xlsx parsing.
"""

from __future__ import annotations

import logging
import urllib.request
from io import BytesIO

import pandas as pd

NAVHIST_URL = (
    "https://www.ssga.com/us/en/intermediary/library-content/products/fund-data/etfs/us/"
    "navhist-us-en-{symbol}.xlsx"
)
REQUEST_TIMEOUT = 60

# Long-format schema: one row per (symbol, date).
FLOW_COLUMNS = ["symbol", "date", "nav", "shares", "flow"]

# The sheet carries three title rows above the header, and trailing prospectus
# text in the same columns. Coercing then dropping nulls removes both.
_SKIPROWS = 3
_DATE_FORMAT = "%d-%b-%Y"

# NAV * shares outstanding must equal the published total net assets. One XLV row
# (2014-10-07) contradicts itself by 39% in State Street's own file, and a wrong
# share count silently corrupts two days of flow, so such rows are not trusted.
_TNA_TOLERANCE = 1e-4

logger = logging.getLogger(__name__)


def fetch_flows(symbol: str) -> pd.DataFrame:
    """Download and parse one fund's flow history.

    Returns an empty frame instead of raising, so one unavailable ticker
    degrades to a warning rather than failing the whole refresh.
    """
    try:
        content = _download(symbol)
    except Exception:
        logger.exception("SPDR NAV history download failed for %s", symbol)
        return pd.DataFrame(columns=FLOW_COLUMNS)

    try:
        return parse_navhist(content, symbol)
    except Exception:
        logger.exception("SPDR NAV history parse failed for %s", symbol)
        return pd.DataFrame(columns=FLOW_COLUMNS)


def _download(symbol: str) -> bytes:
    url = NAVHIST_URL.format(symbol=symbol.lower())
    with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT) as response:  # noqa: S310
        return response.read()


def parse_navhist(content: bytes, symbol: str) -> pd.DataFrame:
    """Turn one published NAV history sheet into daily flows."""
    frame = pd.read_excel(
        BytesIO(content),
        skiprows=_SKIPROWS,
        usecols=[0, 1, 2, 3],
        names=["date", "nav", "shares", "tna"],
        header=0,
    )
    frame["date"] = pd.to_datetime(frame["date"], format=_DATE_FORMAT, errors="coerce")
    for column in ("nav", "shares", "tna"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    # The sheet is published newest-first; flows need oldest-first to difference.
    frame = frame.dropna().sort_values("date").reset_index(drop=True)
    if frame.empty:
        return pd.DataFrame(columns=FLOW_COLUMNS)

    trusted = (frame["nav"] * frame["shares"] - frame["tna"]).abs() / frame["tna"] <= _TNA_TOLERANCE

    frame["flow"] = frame["shares"].diff() * frame["nav"]
    # An untrusted row poisons its own flow and the next day's difference. Both
    # become unknown; the surrounding good rows are kept.
    frame.loc[~trusted | ~trusted.shift(fill_value=False), "flow"] = float("nan")
    frame = frame[trusted]

    frame["symbol"] = symbol.upper()
    return frame[FLOW_COLUMNS].reset_index(drop=True)
