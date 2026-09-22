from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


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
    # Built from metrics_service.BreadthResult, a NamedTuple with these fields.
    model_config = ConfigDict(from_attributes=True)

    positive: int
    total: int
    ratio: float | None


class RotationPointOut(BaseModel):
    x: float | None
    y: float | None


class SectorRowOut(BaseModel):
    symbol: str
    name: str
    return_1d: float | None
    return_5d: float | None
    return_20d: float | None
    vs_spy_5d: float | None
    vs_spy_20d: float | None
    quadrant: str | None
    trail: list[RotationPointOut]


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


class RatiosOut(BaseModel):
    """The ratio proxies the dashboard always reports: equal-weight breadth
    (PRD section 21), credit risk (PRD section 22), and growth vs value style."""

    rsp_spy: RatioOut
    hyg_lqd: RatioOut
    ivw_ive: RatioOut


class SectorFlowOut(BaseModel):
    symbol: str
    name: str
    # Keyed by window label ("5D"), in dollars. None where the window has no
    # trustworthy flow, so the UI can tell "no data" from "zero net flow".
    flows: dict[str, float | None]


class FlowsResponse(BaseModel):
    """Empty `sectors` means the local cache has no flows yet, which is the
    normal state until scripts/spdr_flows_report.py has been run."""

    as_of: datetime | None
    windows: list[int]
    sectors: list[SectorFlowOut]


class DashboardResponse(BaseModel):
    as_of: datetime
    provider: str
    data_timestamp: datetime | None
    retrieved_at: datetime | None
    is_stale: bool
    regime: RegimeOut
    sectors: list[SectorRowOut]
    cross_asset: list[CrossAssetRowOut]
    breadth_1d: BreadthOut
    breadth_5d: BreadthOut
    dispersion_1d: float | None
    dispersion_5d: float | None
    defensive_spread_5d: float | None
    ratios: RatiosOut
    warnings: list[str]
