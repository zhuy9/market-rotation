from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.regime_service import RegimeMetrics, classify_regime, load_regime_config

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_metrics(name: str) -> RegimeMetrics:
    data = json.loads((FIXTURES_DIR / f"{name}.json").read_text())
    return RegimeMetrics(**data)


@pytest.mark.parametrize(
    "fixture_name,expected_regime",
    [
        ("broad_risk_on", "BROAD_RISK_ON"),
        ("internal_rotation", "INTERNAL_ROTATION"),
        ("defensive_rotation", "DEFENSIVE_ROTATION"),
        ("broad_risk_off", "BROAD_RISK_OFF"),
        ("mixed", "MIXED"),
    ],
)
def test_fixture_produces_expected_regime(fixture_name, expected_regime):
    metrics = _load_metrics(fixture_name)

    result = classify_regime(metrics)

    assert result.regime == expected_regime
    assert result.confidence in {"low", "medium", "high"}
    assert len(result.reasons) > 0
    assert all(isinstance(r, str) and r for r in result.reasons)


def test_reasons_never_claim_confirmed_fund_flow():
    banned_phrases = ["net inflow", "net outflow", "money left", "money flowed"]

    all_fixtures = [
        "broad_risk_on",
        "internal_rotation",
        "defensive_rotation",
        "broad_risk_off",
        "mixed",
    ]
    for fixture_name in all_fixtures:
        result = classify_regime(_load_metrics(fixture_name))
        text = " ".join(result.reasons).lower()
        for phrase in banned_phrases:
            assert phrase not in text


def test_broad_risk_off_wins_over_overlapping_defensive_rotation_conditions():
    """The broad_risk_off fixture also satisfies DEFENSIVE_ROTATION's rule —
    priority order must still pick BROAD_RISK_OFF (checked first)."""
    metrics = _load_metrics("broad_risk_off")
    config = load_regime_config()

    defensive_cfg = config["defensive_rotation"]
    assert metrics.defensive_spread_5d >= defensive_cfg["spread_5d_min"]
    assert metrics.defensive_outperform_count >= defensive_cfg["min_defensive_outperformers"]

    result = classify_regime(metrics)

    assert result.regime == "BROAD_RISK_OFF"


def test_missing_benchmark_data_does_not_crash_and_fails_the_condition():
    metrics = RegimeMetrics(
        sector_total=11,
        spy_return_5d=0.015,
        sector_positive_count_5d=8,
        sector_negative_count_5d=3,
        sector_dispersion_5d=0.01,
        hyg_vs_lqd_5d=0.0,
        qqq_vs_spy_5d=0.01,
        iwm_vs_spy_5d=0.01,
        # rsp_vs_spy_5d is deliberately left unset: RSP data is missing.
    )

    result = classify_regime(metrics)

    # BROAD_RISK_ON requires rsp_vs_spy_5d >= 0, which is unknown here, so it
    # must not match even though every other BROAD_RISK_ON condition holds.
    assert result.regime != "BROAD_RISK_ON"
    assert result.regime == "MIXED"


def test_all_none_metrics_produce_mixed_without_raising():
    metrics = RegimeMetrics(sector_total=11)  # every metric defaults to "no data"

    result = classify_regime(metrics)

    assert result.regime == "MIXED"
    assert result.confidence == "low"
    assert len(result.reasons) > 0


def test_load_regime_config_reads_shipped_thresholds():
    config = load_regime_config()

    assert config["broad_risk_on"]["spy_5d_min"] == pytest.approx(0.01)
    assert config["internal_rotation"]["dispersion_5d_min"] == pytest.approx(0.02)


def test_reasons_report_the_configured_sector_count_not_a_hardcoded_eleven():
    """The sector total comes from the universe config, so a universe with a
    different number of sectors reports that number instead of always "11"."""
    metrics = RegimeMetrics(
        spy_return_5d=-0.03,
        sector_positive_count_5d=1,
        sector_negative_count_5d=5,
        sector_total=6,
        sector_dispersion_5d=0.01,
        rsp_vs_spy_5d=-0.01,
        hyg_vs_lqd_5d=-0.02,
        defensive_spread_5d=0.0,
        defensive_outperform_count=0,
        qqq_vs_spy_5d=-0.01,
        iwm_vs_spy_5d=-0.01,
        gld_vs_spy_5d=0.02,
        ief_vs_spy_5d=0.02,
        tlt_vs_spy_5d=0.02,
        vix_return_5d=0.1,
    )

    result = classify_regime(metrics)

    assert result.regime == "BROAD_RISK_OFF"
    assert any("1 of 6 sectors were positive" in reason for reason in result.reasons)
    assert not any("of 11" in reason for reason in result.reasons)
