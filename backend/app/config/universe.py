from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_UNIVERSE_PATH = Path(__file__).parent / "universe.yaml"
DEFAULT_GROUPS_PATH = Path(__file__).parent / "groups.yaml"


@dataclass(frozen=True)
class Instrument:
    symbol: str
    name: str
    category: str


class Universe:
    def __init__(self, instruments: list[Instrument]) -> None:
        self.instruments = instruments
        self._by_symbol = {i.symbol: i for i in instruments}

    @property
    def symbols(self) -> list[str]:
        return list(self._by_symbol)

    def get(self, symbol: str) -> Instrument | None:
        return self._by_symbol.get(symbol)


def load_universe(path: Path = DEFAULT_UNIVERSE_PATH) -> Universe:
    data = yaml.safe_load(path.read_text())
    instruments = [
        Instrument(symbol=symbol, name=name, category=category)
        for category, symbols in data.items()
        for symbol, name in symbols.items()
    ]
    return Universe(instruments)


def load_groups(path: Path = DEFAULT_GROUPS_PATH) -> dict[str, list[str]]:
    """Defensive/cyclical sector membership, kept in config per PRD section 24."""
    return yaml.safe_load(path.read_text())
