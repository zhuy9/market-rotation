from fastapi import APIRouter, Depends

from app.deps import get_market_service
from app.models.schemas import RefreshResponse
from app.services.market_service import MarketService

router = APIRouter()


@router.post("/data/refresh", response_model=RefreshResponse)
def refresh_data(service: MarketService = Depends(get_market_service)) -> RefreshResponse:
    result = service.refresh()
    return RefreshResponse(
        status=result.status,
        updated_symbols=result.updated_symbols,
        failed_symbols=result.failed_symbols,
        as_of=result.as_of,
    )
