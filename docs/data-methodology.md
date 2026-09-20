# Data Methodology

This document lists every formula the dashboard computes and every rule the
regime engine evaluates. If a number appears on the dashboard, its formula
is on this page.

> The dashboard infers rotation/risk regimes from **relative price
> behavior**. It does not measure actual money flows — that requires ETF
> creation/redemption (fund-flow) data, which is out of scope for this
> version. Nothing here should be read as "money left X and entered Y."

## Data source and freshness

- Provider: `yfinance` (Yahoo Finance), adjusted prices (`auto_adjust=True`,
  `Close`), daily interval, ~400 calendar days of history.
- All return calculations use the same adjusted-close field, consistently.
- `data_timestamp` = the most recent bar timestamp across the cached
  universe. If it is more than 4 calendar days old (covers a long
  weekend/holiday plus a buffer day), the dashboard marks the data
  `STALE DATA` rather than silently presenting it as current.
- A symbol with zero cached rows produces a `"<SYMBOL> data is
  unavailable."` warning instead of breaking the page.

## Returns

```text
return_N = latest_close / close_N_sessions_ago - 1
```

`N` ∈ {1, 5, 20}, counted in **trading sessions** (row offsets), never
calendar-day subtraction. If there isn't at least `N + 1` sessions of
history, or the base price is 0, the return is `None`/`null` — never a
crash or a silently wrong number.

Implementation: `app/services/metrics_service.py::compute_return`.

## Relative return vs. a benchmark

```text
relative_return = instrument_return - benchmark_return
```

Positive = the instrument outperformed the benchmark over that period.
Used for every "vs SPY" column and for the RSP/SPY and HYG/LQD ratios
below. `None` if either side is `None`.

## Sector breadth

```text
positive_count = count(sector 1D or 5D return > 0)
total          = count(sectors with a known return)
breadth_ratio  = positive_count / total
```

Missing sectors are excluded from both the numerator and denominator
(never silently counted as negative).

## Sector dispersion

```text
dispersion = sample_stddev(sector returns), same period
```

`None` if fewer than 2 sectors have a known return for that period. Higher
dispersion = sector performance is more spread out (useful for identifying
internal rotation vs. a uniform market move).

## RSP/SPY and HYG/LQD ratios

```text
RelativeRatio(t) = Price(numerator, t) / Price(denominator, t)
```

The dashboard reports 1D/5D/20D **returns of that ratio series** (same
N-session-return formula above, applied to the ratio instead of a raw
price). RSP outperforming SPY is shown as "broader participation"; HYG
outperforming LQD is shown as "credit strengthening" — both are
interpretive labels, not proof.

## Defensive / cyclical spread

```text
Defensive5D = mean(5D returns of XLV, XLP, XLU)
Cyclical5D  = mean(5D returns of XLK, XLY, XLI, XLF, XLE, XLB)
DefensiveSpread5D = Defensive5D - Cyclical5D
```

Group membership lives in `app/config/groups.yaml`, not in code. A group
with zero available members returns `None` for that group's mean (and for
the spread).

## Relative Rotation Chart

For every sector:

```text
X = 20D relative return vs SPY
Y = 5D relative return vs SPY
```

| Quadrant  | Condition                          |
|-----------|-------------------------------------|
| Leading   | X > 0 and Y > 0                     |
| Improving | X ≤ 0 and Y > 0                      |
| Weakening | X > 0 and Y ≤ 0                      |
| Lagging   | X ≤ 0 and Y ≤ 0                      |

`None` if either coordinate is missing. This chart is inspired by
relative-rotation concepts; it does not reproduce StockCharts/JdK
proprietary metrics.

## Regime classification

Deterministic, rule-based, no LLM/AI involved. Rules are evaluated **in
this fixed order** — the first match wins:

```text
1. BROAD_RISK_OFF
2. DEFENSIVE_ROTATION
3. BROAD_RISK_ON
4. INTERNAL_ROTATION
5. MIXED (fallback — none of the above matched)
```

Thresholds live in `app/config/regimes.yaml`. Current defaults:

| Rule | Conditions (all must hold) |
|------|------------------------------|
| **BROAD_RISK_OFF** | SPY 5D < −1% · sector breadth 5D ≤ 4/11 · at least 2 of: GLD 5D > SPY 5D, (IEF or TLT) 5D > SPY 5D, HYG underperforms LQD, VIX 5D > 0 |
| **DEFENSIVE_ROTATION** | DefensiveSpread5D ≥ +1% · at least 2 of XLV/XLP/XLU outperform SPY · QQQ or IWM underperforms SPY |
| **BROAD_RISK_ON** | SPY 5D > +1% · sector breadth 5D ≥ 7/11 · RSP 5D vs SPY ≥ 0 · HYG 5D vs LQD ≥ 0 |
| **INTERNAL_ROTATION** | \|SPY 5D\| ≤ 2% · ≥ 3 sectors positive · ≥ 3 sectors negative · sector dispersion 5D ≥ 2% |
| **MIXED** | None of the above — the response still includes the strongest available observations (SPY 5D, breadth, dispersion) |

A missing input (e.g. no RSP data) makes that rule's condition evaluate to
"not met" rather than raising, so the engine degrades to a later rule or to
`MIXED` instead of crashing.

Every result includes:

```json
{ "regime": "INTERNAL_ROTATION", "confidence": "medium", "reasons": ["..."] }
```

`confidence` is a heuristic ("low"/"medium"/"high") based on how strongly a
rule's own inputs exceeded its threshold (e.g. how many BROAD_RISK_OFF
confirmations fired) — it is **not** a statistical probability.

Implementation: `app/services/regime_service.py`. Synthetic fixtures for
all five regimes (including a fixture that deliberately satisfies both
BROAD_RISK_OFF and DEFENSIVE_ROTATION, to prove priority ordering) live in
`backend/tests/fixtures/`.
