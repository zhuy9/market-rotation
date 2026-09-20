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
