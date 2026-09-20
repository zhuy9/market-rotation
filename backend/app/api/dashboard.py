from datetime import UTC, datetime

from fastapi import APIRouter, Depends

from app.config.universe import Universe
from app.deps import get_market_service, get_universe
from app.models.schemas import DashboardResponse, RegimeOut
from app.services.dashboard_service import build_dashboard
from app.services.market_service import MarketService

router = APIRouter()


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    service: MarketService = Depends(get_market_service),
    universe: Universe = Depends(get_universe),
) -> DashboardResponse:
    result = build_dashboard(service, universe)
    return DashboardResponse(
        as_of=datetime.now(UTC),
        provider=result.provider,
        data_timestamp=result.data_timestamp,
        retrieved_at=result.retrieved_at,
        is_stale=result.is_stale,
        regime=RegimeOut(
            name=result.regime.regime,
            confidence=result.regime.confidence,
            reasons=result.regime.reasons,
        ),
        sectors=result.sectors,
        cross_asset=result.cross_asset,
        breadth_1d=result.breadth_1d._asdict(),
        breadth_5d=result.breadth_5d._asdict(),
        dispersion_1d=result.dispersion_1d,
        dispersion_5d=result.dispersion_5d,
        defensive_spread_5d=result.defensive_spread_5d,
        ratios=result.ratios,
        warnings=result.warnings,
    )
