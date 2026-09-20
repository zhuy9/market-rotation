"""Ties MarketService + metrics_service + regime_service into one dashboard payload."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

import pandas as pd

from app.config.groups import load_groups
from app.config.universe import Universe
from app.services import metrics_service as metrics
from app.services.market_service import PROVIDER_NAME, MarketService
from app.services.regime_service import RegimeMetrics, RegimeResult, classify_regime

STALE_AFTER = timedelta(days=4)  # covers a long weekend/holiday plus a day of buffer
TRAIL_LENGTH = 5  # PRD section 17: show the previous five daily rotation positions


@dataclass(frozen=True)
class DashboardResult:
    provider: str
    data_timestamp: pd.Timestamp | None
    is_stale: bool
    regime: RegimeResult
    sectors: list[dict]
    cross_asset: list[dict]
    breadth_1d: metrics.BreadthResult
    breadth_5d: metrics.BreadthResult
    dispersion_1d: float | None
    dispersion_5d: float | None
    defensive_spread_5d: float | None
    ratios: dict[str, dict]
    warnings: list[str]


def build_dashboard(market_service: MarketService, universe: Universe) -> DashboardResult:
    prices = market_service.get_prices()
    groups = load_groups()

    if prices.empty:
        return _empty_dashboard()

    sector_symbols = [i.symbol for i in universe.instruments if i.category == "sectors"]
    other_instruments = [i for i in universe.instruments if i.category != "sectors"]

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

    defensive_vs_spy = {
        symbol: metrics.relative_return(_return(returns_table, symbol, "return_5d"), spy_5d)
        for symbol in groups["defensive"]
    }
    defensive_outperform_count = sum(
        1 for v in defensive_vs_spy.values() if v is not None and v > 0
    )

    def vs_spy_5d(symbol: str) -> float | None:
        return metrics.relative_return(_return(returns_table, symbol, "return_5d"), spy_5d)

    regime = classify_regime(
        RegimeMetrics(
            spy_return_5d=spy_5d,
            sector_positive_count_5d=breadth_5d.positive,
            sector_negative_count_5d=negative_5d,
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

    return DashboardResult(
        provider=PROVIDER_NAME,
        data_timestamp=data_timestamp,
        is_stale=is_stale,
        regime=regime,
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


def _empty_dashboard() -> DashboardResult:
    empty_breadth = metrics.BreadthResult(positive=0, total=0, ratio=None)
    empty_ratio = {"return_1d": None, "return_5d": None, "return_20d": None}
    no_data_regime = classify_regime(
        RegimeMetrics(
            spy_return_5d=None,
            sector_positive_count_5d=0,
            sector_negative_count_5d=0,
            sector_dispersion_5d=None,
            rsp_vs_spy_5d=None,
            hyg_vs_lqd_5d=None,
            defensive_spread_5d=None,
            defensive_outperform_count=0,
            qqq_vs_spy_5d=None,
            iwm_vs_spy_5d=None,
            gld_vs_spy_5d=None,
            ief_vs_spy_5d=None,
            tlt_vs_spy_5d=None,
            vix_return_5d=None,
        )
    )
    return DashboardResult(
        provider=PROVIDER_NAME,
        data_timestamp=None,
        is_stale=True,
        regime=no_data_regime,
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


# Shared with the trail calculation in metrics_service; kept as a short alias
# since this module calls it a dozen times.
_clean = metrics.clean_number


def _clean_dict(values: dict[str, float | None]) -> dict[str, float | None]:
    return {key: _clean(value) for key, value in values.items()}
