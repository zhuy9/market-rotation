from __future__ import annotations

from app.config.universe import load_groups, load_universe


def test_load_universe_reads_shipped_config():
    universe = load_universe()

    assert "SPY" in universe.symbols
    assert len(universe.symbols) > 20
    assert universe.instruments[0].category  # every instrument has a category


def test_load_groups_reads_shipped_config():
    groups = load_groups()

    assert set(groups["defensive"]) == {"XLV", "XLP", "XLU"}
    assert "XLK" in groups["cyclical"]
