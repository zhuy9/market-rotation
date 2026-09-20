from fastapi import APIRouter, Depends

from app.config.universe import Universe
from app.deps import get_universe
from app.models.schemas import InstrumentOut

router = APIRouter()


@router.get("/universe", response_model=list[InstrumentOut])
def get_universe_endpoint(universe: Universe = Depends(get_universe)) -> list[InstrumentOut]:
    return [
        InstrumentOut(symbol=i.symbol, name=i.name, category=i.category)
        for i in universe.instruments
    ]
