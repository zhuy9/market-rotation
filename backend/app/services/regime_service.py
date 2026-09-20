"""Deterministic, rule-based market-regime classifier (PRD sections 25-27).

No LLM/AI is involved. Rules and their thresholds are evaluated in a fixed,
documented priority order so overlapping conditions resolve predictably:

    BROAD_RISK_OFF > DEFENSIVE_ROTATION > BROAD_RISK_ON > INTERNAL_ROTATION > MIXED

Every result states which observations produced it. Price-based rotation is
never described as confirmed fund flow.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_REGIMES_PATH = Path(__file__).parents[1] / "config" / "regimes.yaml"


@dataclass(frozen=True)
class RegimeMetrics:
    """Pre-computed metric snapshot (see app.services.metrics_service) that the
    regime rules are evaluated against. Any field may be None when the
    underlying instrument's data is missing — rules treat that as "condition
    not met" rather than raising. That is also why every metric defaults to
    "no data": an empty cache only has to supply `sector_total`.
    """

    sector_total: int  # how many sectors the universe config defines, not how many had data
    spy_return_5d: float | None = None
    sector_positive_count_5d: int = 0
    sector_negative_count_5d: int = 0
    sector_dispersion_5d: float | None = None
    rsp_vs_spy_5d: float | None = None
    hyg_vs_lqd_5d: float | None = None
    defensive_spread_5d: float | None = None
    defensive_outperform_count: int = 0
    qqq_vs_spy_5d: float | None = None
    iwm_vs_spy_5d: float | None = None
    gld_vs_spy_5d: float | None = None
    ief_vs_spy_5d: float | None = None
    tlt_vs_spy_5d: float | None = None
    vix_return_5d: float | None = None


@dataclass(frozen=True)
class RegimeResult:
    regime: str
    confidence: str  # heuristic ("low"/"medium"/"high"), not a statistical probability
    reasons: list[str]


def load_regime_config(path: Path = DEFAULT_REGIMES_PATH) -> dict:
    return yaml.safe_load(path.read_text())


def classify_regime(metrics: RegimeMetrics, config: dict | None = None) -> RegimeResult:
    config = config if config is not None else load_regime_config()

    checks = [
        (_check_broad_risk_off, config["broad_risk_off"]),
        (_check_defensive_rotation, config["defensive_rotation"]),
        (_check_broad_risk_on, config["broad_risk_on"]),
        (_check_internal_rotation, config["internal_rotation"]),
    ]
    for check, rule_config in checks:
        result = check(metrics, rule_config)
        if result is not None:
            return result
    return _mixed_result(metrics)


def _gt(value: float | None, threshold: float) -> bool:
    return value is not None and value > threshold


def _lt(value: float | None, threshold: float) -> bool:
    return value is not None and value < threshold


def _gte(value: float | None, threshold: float) -> bool:
    return value is not None and value >= threshold


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:+.1f}%"


def _check_broad_risk_off(m: RegimeMetrics, cfg: dict) -> RegimeResult | None:
    spy_down = _lt(m.spy_return_5d, cfg["spy_5d_max"])
    breadth_weak = m.sector_positive_count_5d <= cfg["max_positive_sectors"]

    confirmations = []
    if _gt(m.gld_vs_spy_5d, 0):
        confirmations.append("Gold outperformed SPY.")
    if _gt(m.ief_vs_spy_5d, 0) or _gt(m.tlt_vs_spy_5d, 0):
        confirmations.append("Treasuries outperformed SPY.")
    if _lt(m.hyg_vs_lqd_5d, 0):
        confirmations.append("High-yield credit underperformed investment-grade credit.")
    if _gt(m.vix_return_5d, 0):
        confirmations.append("Volatility (VIX) rose.")

    if not (spy_down and breadth_weak and len(confirmations) >= cfg["min_confirmations"]):
        return None

    confidence = "high" if len(confirmations) >= 3 else "medium"
    reasons = [
        f"SPY fell {_pct(m.spy_return_5d)} over five sessions.",
        f"Only {m.sector_positive_count_5d} of {m.sector_total} sectors were positive.",
        *confirmations,
    ]
    return RegimeResult(regime="BROAD_RISK_OFF", confidence=confidence, reasons=reasons)


def _check_defensive_rotation(m: RegimeMetrics, cfg: dict) -> RegimeResult | None:
    qqq_or_iwm_underperforms = _lt(m.qqq_vs_spy_5d, 0) or _lt(m.iwm_vs_spy_5d, 0)
    matched = (
        _gte(m.defensive_spread_5d, cfg["spread_5d_min"])
        and m.defensive_outperform_count >= cfg["min_defensive_outperformers"]
        and qqq_or_iwm_underperforms
    )
    if not matched:
        return None

    confidence = "high" if m.defensive_outperform_count >= 3 else "medium"
    reasons = [
        f"Defensive sectors outperformed cyclical sectors by {_pct(m.defensive_spread_5d)}.",
        f"{m.defensive_outperform_count} of XLV/XLP/XLU outperformed SPY.",
        "Small caps or Nasdaq underperformed SPY.",
    ]
    return RegimeResult(regime="DEFENSIVE_ROTATION", confidence=confidence, reasons=reasons)


def _check_broad_risk_on(m: RegimeMetrics, cfg: dict) -> RegimeResult | None:
    matched = (
        _gt(m.spy_return_5d, cfg["spy_5d_min"])
        and m.sector_positive_count_5d >= cfg["min_positive_sectors"]
        and _gte(m.rsp_vs_spy_5d, cfg["rsp_vs_spy_5d_min"])
        and _gte(m.hyg_vs_lqd_5d, cfg["hyg_vs_lqd_5d_min"])
    )
    if not matched:
        return None

    confidence = "high" if m.sector_positive_count_5d >= 9 else "medium"
    reasons = [
        f"SPY gained {_pct(m.spy_return_5d)} over five sessions.",
        f"{m.sector_positive_count_5d} of {m.sector_total} sectors were positive.",
        "Equal-weight S&P outperformed SPY.",
        "High-yield credit outperformed investment-grade credit.",
    ]
    return RegimeResult(regime="BROAD_RISK_ON", confidence=confidence, reasons=reasons)


def _check_internal_rotation(m: RegimeMetrics, cfg: dict) -> RegimeResult | None:
    spy_flat = m.spy_return_5d is not None and abs(m.spy_return_5d) <= cfg["spy_5d_abs_max"]
    matched = (
        spy_flat
        and m.sector_positive_count_5d >= cfg["min_positive_sectors"]
        and m.sector_negative_count_5d >= cfg["min_negative_sectors"]
        and _gte(m.sector_dispersion_5d, cfg["dispersion_5d_min"])
    )
    if not matched:
        return None

    strong_dispersion = _gte(m.sector_dispersion_5d, 2 * cfg["dispersion_5d_min"])
    confidence = "high" if strong_dispersion else "medium"
    reasons = [
        f"SPY was approximately flat over five sessions ({_pct(m.spy_return_5d)}).",
        f"{m.sector_positive_count_5d} sectors advanced while "
        f"{m.sector_negative_count_5d} declined.",
        f"Sector return dispersion was elevated ({_pct(m.sector_dispersion_5d)}).",
    ]
    return RegimeResult(regime="INTERNAL_ROTATION", confidence=confidence, reasons=reasons)


def _mixed_result(m: RegimeMetrics) -> RegimeResult:
    reasons = [
        f"SPY returned {_pct(m.spy_return_5d)} over five sessions.",
        f"{m.sector_positive_count_5d} of {m.sector_total} sectors were positive, "
        f"{m.sector_negative_count_5d} were negative.",
        f"Sector return dispersion was {_pct(m.sector_dispersion_5d)}.",
    ]
    return RegimeResult(regime="MIXED", confidence="low", reasons=reasons)
