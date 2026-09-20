from __future__ import annotations

import logging
from datetime import UTC, datetime

import numpy as np
import pandas as pd

from app.providers.yfinance_provider import YFinanceMarketDataProvider


def _multiindex_frame() -> pd.DataFrame:
    """Mimics yf.download(group_by='ticker') output for two tickers.

    AAA has three good bars; BBB has none (simulates a bad/delisted ticker).
    """
    dates = pd.date_range("2026-01-01", periods=3, freq="D")
    fields = ["Open", "High", "Low", "Close", "Volume"]
    columns = pd.MultiIndex.from_product([["AAA", "BBB"], fields])
    frame = pd.DataFrame(np.nan, index=dates, columns=columns)

    frame[("AAA", "Open")] = [10, 11, 12]
    frame[("AAA", "High")] = [10.5, 11.5, 12.5]
    frame[("AAA", "Low")] = [9.5, 10.5, 11.5]
    frame[("AAA", "Close")] = [10.2, 11.2, 12.2]
    frame[("AAA", "Volume")] = [1000, 1100, 1200]

    return frame


def test_get_history_normalizes_and_skips_symbols_with_no_data(monkeypatch):
    monkeypatch.setattr(
        "app.providers.yfinance_provider.yf.download", lambda **kwargs: _multiindex_frame()
    )

    provider = YFinanceMarketDataProvider()
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 4, tzinfo=UTC)

    result = provider.get_history(["AAA", "BBB"], start, end, "1d")

    assert list(result.columns) == [
        "symbol",
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]
    assert set(result["symbol"]) == {"AAA"}
    assert len(result) == 3
    assert result.iloc[0]["close"] == 10.2


def test_get_history_returns_empty_frame_when_provider_raises(monkeypatch):
    def _boom(**kwargs):
        raise RuntimeError("network unavailable")

    monkeypatch.setattr("app.providers.yfinance_provider.yf.download", _boom)

    provider = YFinanceMarketDataProvider()
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 4, tzinfo=UTC)

    result = provider.get_history(["AAA"], start, end, "1d")

    assert result.empty


def test_get_history_logs_the_cause_when_the_provider_raises(monkeypatch, caplog):
    """Degrading to an empty frame keeps the API alive, but the reason must
    still be recorded rather than silently swallowed."""

    def _boom(**kwargs):
        raise RuntimeError("rate limited")

    monkeypatch.setattr("app.providers.yfinance_provider.yf.download", _boom)

    with caplog.at_level(logging.ERROR):
        YFinanceMarketDataProvider().get_history(
            ["AAA"], datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 1, 4, tzinfo=UTC), "1d"
        )

    assert "Market data request failed" in caplog.text
    assert "rate limited" in caplog.text


def test_get_history_with_no_symbols_returns_empty_frame():
    provider = YFinanceMarketDataProvider()
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 4, tzinfo=UTC)

    result = provider.get_history([], start, end, "1d")

    assert result.empty


def test_get_latest_returns_most_recent_bar_per_symbol(monkeypatch):
    monkeypatch.setattr(
        "app.providers.yfinance_provider.yf.download", lambda **kwargs: _multiindex_frame()
    )

    provider = YFinanceMarketDataProvider()

    result = provider.get_latest(["AAA", "BBB"])

    assert list(result["symbol"]) == ["AAA"]
    assert result.iloc[0]["close"] == 12.2
