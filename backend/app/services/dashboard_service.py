"""Ties MarketService + metrics_service + regime_service into one dashboard payload."""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from app.config.universe import Universe, load_groups
from app.models.schemas import DashboardResponse, RegimeOut
from app.services import metrics_service as metrics
from app.services.market_service import PROVIDER_NAME, STALE_AFTER, MarketService
from app.services.metrics_service import clean_number as _clean
from app.services.regime_service import RegimeMetrics, classify_regime

TRAIL_LENGTH = 5  # PRD section 17: show the previous five daily rotation positions


def build_dashboard(market_service: MarketService, universe: Universe) -> DashboardResponse:
    prices = market_service.get_prices()
    groups = load_groups()
    retrieved_at = market_service.latest_retrieved_at()

    sector_symbols = [i.symbol for i in universe.instruments if i.category == "sectors"]
    other_instruments = [i for i in universe.instruments if i.category != "sectors"]

    if prices.empty:
        return _empty_dashboard(retrieved_at, len(sector_symbols))

    sector_table = metrics.compute_sector_table(prices, sector_symbols, "SPY")
    returns_table = metrics.compute_returns_table(prices).set_index("symbol")
    trail = metrics.compute_rotation_trail(prices, sector_symbols, "SPY", TRAIL_LENGTH)

    sector_returns_1d = _column_as_dict(sector_table, "return_1d")
    sector_returns_5d = _column_as_dict(sector_table, "return_5d")

    breadth_1d = metrics.sector_breadth(sector_returns_1d)
    breadth_5d = metrics.sector_breadth(sector_returns_5d)
    dispersion_1d = metrics.sector_dispersion(sector_returns_1d)
    dispersion_5d = metrics.sector_dispersion(sector_returns_5d)
    negative_5d = sum(1 for v in sector_returns_5d.values() if v is not None and v < 0)

    spy_5d = _return(returns_table, "SPY", "return_5d")
    rsp_spy = metrics.compute_ratio_returns(prices, "RSP", "SPY")
    hyg_lqd = metrics.compute_ratio_returns(prices, "HYG", "LQD")
    spread = metrics.defensive_cyclical_spread(
        sector_returns_5d, groups["defensive"], groups["cyclical"]
    )

    def vs_spy_5d(symbol: str) -> float | None:
        """How far `symbol` out- or under-performed SPY over five sessions."""
        return metrics.relative_return(_return(returns_table, symbol, "return_5d"), spy_5d)

    defensive_vs_spy = [vs_spy_5d(symbol) for symbol in groups["defensive"]]
    defensive_outperform_count = sum(1 for v in defensive_vs_spy if v is not None and v > 0)

    regime = classify_regime(
        RegimeMetrics(
            spy_return_5d=spy_5d,
            sector_positive_count_5d=breadth_5d.positive,
            sector_negative_count_5d=negative_5d,
            sector_total=len(sector_symbols),
            sector_dispersion_5d=dispersion_5d,
            rsp_vs_spy_5d=_clean(rsp_spy["return_5d"]),
            hyg_vs_lqd_5d=_clean(hyg_lqd["return_5d"]),
            defensive_spread_5d=spread["spread_5d"],
            defensive_outperform_count=defensive_outperform_count,
            qqq_vs_spy_5d=vs_spy_5d("QQQ"),
            iwm_vs_spy_5d=vs_spy_5d("IWM"),
            gld_vs_spy_5d=vs_spy_5d("GLD"),
            ief_vs_spy_5d=vs_spy_5d("IEF"),
            tlt_vs_spy_5d=vs_spy_5d("TLT"),
            vix_return_5d=_return(returns_table, "^VIX", "return_5d"),
        )
    )

    sectors_out = [
        {
            "symbol": row["symbol"],
            "name": _instrument_name(universe, row["symbol"]),
            "return_1d": _clean(row["return_1d"]),
            "return_5d": _clean(row["return_5d"]),
            "return_20d": _clean(row["return_20d"]),
            "vs_spy_5d": _clean(row["vs_spy_5d"]),
            "vs_spy_20d": _clean(row["vs_spy_20d"]),
            "quadrant": row["quadrant"] if isinstance(row["quadrant"], str) else None,
            "trail": trail.get(row["symbol"], []),
        }
        for _, row in sector_table.iterrows()
    ]

    cross_asset_out = [
        {
            "symbol": instrument.symbol,
            "name": instrument.name,
            "category": instrument.category,
            "return_1d": _return(returns_table, instrument.symbol, "return_1d"),
            "return_5d": _return(returns_table, instrument.symbol, "return_5d"),
            "return_20d": _return(returns_table, instrument.symbol, "return_20d"),
        }
        for instrument in other_instruments
    ]

    data_timestamp = prices["timestamp"].max()
    is_stale = (pd.Timestamp.now() - data_timestamp) > STALE_AFTER

    warnings = [
        f"{instrument.symbol} data is unavailable."
        for instrument in universe.instruments
        if instrument.symbol not in returns_table.index
    ]
    if is_stale:
        warnings.append("STALE DATA: latest observation is older than expected.")

    return DashboardResponse(
        as_of=datetime.now(UTC),
        provider=PROVIDER_NAME,
        data_timestamp=data_timestamp,
        retrieved_at=retrieved_at,
        is_stale=is_stale,
        regime=RegimeOut(name=regime.regime, confidence=regime.confidence, reasons=regime.reasons),
        sectors=sectors_out,
        cross_asset=cross_asset_out,
        breadth_1d=breadth_1d,
        breadth_5d=breadth_5d,
        dispersion_1d=dispersion_1d,
        dispersion_5d=dispersion_5d,
        defensive_spread_5d=spread["spread_5d"],
        ratios={"rsp_spy": _clean_dict(rsp_spy), "hyg_lqd": _clean_dict(hyg_lqd)},
        warnings=warnings,
    )


def _empty_dashboard(retrieved_at: datetime | None, sector_total: int) -> DashboardResponse:
    empty_breadth = metrics.BreadthResult(positive=0, total=0, ratio=None)
    empty_ratio = {"return_1d": None, "return_5d": None, "return_20d": None}
    regime = classify_regime(RegimeMetrics(sector_total=sector_total))
    return DashboardResponse(
        as_of=datetime.now(UTC),
        provider=PROVIDER_NAME,
        data_timestamp=None,
        retrieved_at=retrieved_at,
        is_stale=True,
        regime=RegimeOut(name=regime.regime, confidence=regime.confidence, reasons=regime.reasons),
        sectors=[],
        cross_asset=[],
        breadth_1d=empty_breadth,
        breadth_5d=empty_breadth,
        dispersion_1d=None,
        dispersion_5d=None,
        defensive_spread_5d=None,
        ratios={"rsp_spy": empty_ratio, "hyg_lqd": empty_ratio},
        warnings=["No cached market data available. Trigger a refresh."],
    )


def _instrument_name(universe: Universe, symbol: str) -> str:
    instrument = universe.get(symbol)
    return instrument.name if instrument else symbol


def _column_as_dict(table: pd.DataFrame, column: str) -> dict[str, float | None]:
    return {row["symbol"]: _clean(row[column]) for _, row in table.iterrows()}


def _return(returns_table: pd.DataFrame, symbol: str, column: str) -> float | None:
    if symbol not in returns_table.index:
        return None
    return _clean(returns_table.loc[symbol, column])



def _clean_dict(values: dict[str, float | None]) -> dict[str, float | None]:
    return {key: _clean(value) for key, value in values.items()}
