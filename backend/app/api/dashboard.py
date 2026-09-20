from fastapi import APIRouter, Depends

from app.config.universe import Universe
from app.deps import get_market_service, get_universe
from app.models.schemas import DashboardResponse
from app.services.dashboard_service import build_dashboard
from app.services.market_service import MarketService

router = APIRouter()


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    service: MarketService = Depends(get_market_service),
    universe: Universe = Depends(get_universe),
) -> DashboardResponse:
    return build_dashboard(service, universe)
