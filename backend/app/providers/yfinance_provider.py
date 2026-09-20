from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import pandas as pd
import yfinance as yf

from app.providers.base import PRICE_COLUMNS

# This is the ONLY module allowed to import yfinance. Everything else in the
# app depends on the MarketDataProvider protocol.

logger = logging.getLogger(__name__)


class YFinanceMarketDataProvider:
    """MarketDataProvider backed by Yahoo Finance via yfinance."""

    def get_history(
        self,
        symbols: list[str],
        start: datetime,
        end: datetime,
        interval: str = "1d",
    ) -> pd.DataFrame:
        if not symbols:
            return pd.DataFrame(columns=PRICE_COLUMNS)

        try:
            raw = yf.download(
                tickers=symbols,
                start=start,
                end=end,
                interval=interval,
                auto_adjust=True,
                group_by="ticker",
                threads=True,
                progress=False,
            )
        except Exception:
            # Whole-batch failure (network down, rate limited, etc.) must not
            # crash the caller — the refresh reports every symbol as failed
            # instead. Log the cause so it is recoverable rather than swallowed.
            logger.exception("Market data request failed for %d symbol(s)", len(symbols))
            return pd.DataFrame(columns=PRICE_COLUMNS)

        return _normalize(raw, symbols)

    def get_latest(self, symbols: list[str]) -> pd.DataFrame:
        end = datetime.now(UTC)
        start = end - timedelta(days=7)
        history = self.get_history(symbols, start, end, interval="1d")
        if history.empty:
            return history
        return (
            history.sort_values("timestamp")
            .groupby("symbol", as_index=False)
            .tail(1)
            .reset_index(drop=True)
        )


def _normalize(raw: pd.DataFrame, symbols: list[str]) -> pd.DataFrame:
    frames = []
    for symbol in symbols:
        if isinstance(raw.columns, pd.MultiIndex):
            if symbol not in raw.columns.get_level_values(0):
                continue
            sub = raw[symbol]
        else:
            sub = raw

        sub = sub[sub["Close"].notna()]
        if sub.empty:
            continue

        frames.append(
            pd.DataFrame(
                {
                    "symbol": symbol,
                    "timestamp": sub.index,
                    "open": sub["Open"].to_numpy(),
                    "high": sub["High"].to_numpy(),
                    "low": sub["Low"].to_numpy(),
                    "close": sub["Close"].to_numpy(),
                    "volume": sub["Volume"].to_numpy(),
                }
            )
        )

    if not frames:
        return pd.DataFrame(columns=PRICE_COLUMNS)
    return pd.concat(frames, ignore_index=True)
