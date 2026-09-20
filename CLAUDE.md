# Project instructions — Market Rotation Dashboard

Full spec: [docs/PRD_market_rotation_MVP.md](docs/PRD_market_rotation_MVP.md).
This file only holds what the global rules don't already cover.

## Goal

Open-source dashboard that classifies market regime (risk-on / risk-off /
internal rotation / defensive rotation / mixed) from relative price behavior
across sector ETFs, benchmarks, bonds, credit, commodities, USD, and VIX.
**Public repository** — treat every file as visible to the internet.

## Stack

- Backend: Python 3.12+, FastAPI, pandas, numpy, `yfinance`, DuckDB,
  Pydantic, pytest, Ruff. Managed with `uv`.
- Frontend: React + TypeScript + Vite, shadcn/ui, Tailwind, Recharts
  (Plotly only if it meaningfully simplifies the rotation scatter chart).
- Storage: DuckDB, local only, never committed.

## Commands

```bash
cd backend && uv sync && uv run uvicorn app.main:app --reload
cd backend && ruff check . && uv run pytest
cd frontend && npm install && npm run dev
cd frontend && npm run lint && npm run type-check && npm test && npm run build
```

## Milestone rules

Build in order (0 → 5), one milestone per PR/commit sequence: code → review
(ponytail + code-reviewer/security-reviewer) → fix → commit. Do not start a
milestone's UI/consumer code before its dependency milestone is done (e.g. no
regime UI before the regime engine has passing tests). Do not expand scope
past the milestone's stated deliverables/acceptance criteria without an
explicit requirement change from the user.

Regime rule evaluation order is fixed and must stay documented in code:
`BROAD_RISK_OFF → DEFENSIVE_ROTATION → BROAD_RISK_ON → INTERNAL_ROTATION → MIXED`.

## Domain gotchas

- `yfinance` may only be imported inside
  `backend/app/providers/yfinance_provider.py`. Everything else depends on
  the `MarketDataProvider` protocol.
- Returns use **trading-session offsets**, not calendar-day subtraction
  (`5D` = 5 sessions back, not `today - 5 days`).
- Use `auto_adjust=True` / adjusted `Close` consistently for every return
  calculation.
- Never describe price-based rotation as proven fund flow ("net inflow" /
  "net outflow" are banned terms). Use: Internal Rotation, Defensive
  Rotation, Broad Risk-On, Broad Risk-Off, Mixed/Unclear.
- A single failed/stale ticker must degrade to a warning, never a crashed
  endpoint or a silently-wrong regime.
- All regime thresholds and sector/defensive/cyclical group membership live
  in `backend/app/config/*.yaml`, not hardcoded in Python.
- Tests for calculations/regimes use synthetic fixtures only — never assert
  against live Yahoo data (nondeterministic).

## Exceptions to global rules

- None currently. Global `~/.claude/CLAUDE.md` applies in full (commit
  identity, no secrets, MIT license, Ruff/ESLint/Prettier/strict TS, etc.).
