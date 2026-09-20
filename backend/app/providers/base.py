from __future__ import annotations

from datetime import datetime
from typing import Protocol

import pandas as pd

# Long-format schema returned by every provider: one row per (symbol, timestamp).
PRICE_COLUMNS = ["symbol", "timestamp", "open", "high", "low", "close", "volume"]


class MarketDataProvider(Protocol):
    """Interface all market-data sources must implement.

    Business logic and the API layer depend only on this protocol, never on a
    concrete data vendor. Implementations must not raise for an individual bad
    symbol — they should omit it from the returned DataFrame so the rest of
    the batch still succeeds.
    """

    def get_history(
        self,
        symbols: list[str],
        start: datetime,
        end: datetime,
        interval: str,
    ) -> pd.DataFrame:
        """Return OHLCV history with columns PRICE_COLUMNS."""
        ...

    def get_latest(self, symbols: list[str]) -> pd.DataFrame:
        """Return the most recent available bar per symbol, columns PRICE_COLUMNS."""
        ...
