from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class InstrumentOut(BaseModel):
    symbol: str
    name: str
    category: str


class RefreshResponse(BaseModel):
    status: str
    updated_symbols: int
    failed_symbols: list[str]
    as_of: datetime


class RegimeOut(BaseModel):
    name: str
    confidence: str
    reasons: list[str]


class BreadthOut(BaseModel):
    positive: int
    total: int
    ratio: float | None


class SectorRowOut(BaseModel):
    symbol: str
    name: str
    return_1d: float | None
    return_5d: float | None
    return_20d: float | None
    vs_spy_5d: float | None
    vs_spy_20d: float | None
    quadrant: str | None


class CrossAssetRowOut(BaseModel):
    symbol: str
    name: str
    category: str
    return_1d: float | None
    return_5d: float | None
    return_20d: float | None


class RatioOut(BaseModel):
    return_1d: float | None
    return_5d: float | None
    return_20d: float | None


class DashboardResponse(BaseModel):
    as_of: datetime
    provider: str
    data_timestamp: datetime | None
    is_stale: bool
    regime: RegimeOut
    sectors: list[SectorRowOut]
    cross_asset: list[CrossAssetRowOut]
    breadth_1d: BreadthOut
    breadth_5d: BreadthOut
    dispersion_1d: float | None
    dispersion_5d: float | None
    defensive_spread_5d: float | None
    ratios: dict[str, RatioOut]
    warnings: list[str]
