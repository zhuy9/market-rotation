from fastapi import APIRouter, Depends

from app.config.universe import Universe
from app.deps import get_repository, get_universe
from app.models.schemas import FlowsResponse
from app.services.flow_service import build_flows
from app.storage.duckdb_repository import DuckDBRepository

router = APIRouter()


@router.get("/flows", response_model=FlowsResponse)
def get_flows(
    repository: DuckDBRepository = Depends(get_repository),
    universe: Universe = Depends(get_universe),
) -> FlowsResponse:
    """Returns an empty `sectors` list rather than an error when no flows are
    cached, so the dashboard can simply omit the panel."""
    return build_flows(repository, universe)
