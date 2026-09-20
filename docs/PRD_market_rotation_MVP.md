# Product Requirements Document

## Market Rotation Dashboard — MVP

**Status:** Ready for implementation  
**Repository:** Public GitHub repository  
**Target:** Personal research / market-monitoring tool  
**Primary data source:** `yfinance`  
**Architecture requirement:** Data-source agnostic; `yfinance` must be implemented as a replaceable adapter.

---

# 1. Product Summary

Build an open-source dashboard that helps answer:

> Is the market experiencing normal rotation between equity sectors, or is there evidence of a broader movement away from equities into defensive or alternative assets?

The dashboard tracks:

1. U.S. equity sector ETFs.
2. Broad U.S. equity benchmarks.
3. Bonds and credit.
4. Gold and commodities.
5. U.S. dollar.
6. Volatility.
7. Market breadth proxies.

The MVP must emphasize **relative market behavior**, not attempt to predict future prices.

The dashboard should make it possible to quickly distinguish between patterns such as:

- Technology selling while Energy and Financials rise → internal sector rotation.
- Cyclical sectors weakening while Utilities, Staples, and Healthcare strengthen → defensive rotation.
- Most sectors falling while Treasuries and Gold rise → broad risk-off behavior.
- SPY rising while RSP/IWM lag → narrow market leadership.
- Most sectors rising alongside credit and small caps → broad risk-on behavior.

---

# 2. Important Terminology

The MVP must NOT claim that price movement itself proves money literally "flowed" from one asset class into another.

For example:

- SPY falling while GLD rises is evidence of **cross-asset rotation / risk-off behavior**.
- It is NOT proof that dollars were directly withdrawn from SPY and deposited into GLD.

Actual ETF creation/redemption and fund-flow data are not part of MVP.

Therefore the MVP should use terminology such as:

- `Internal Rotation`
- `Defensive Rotation`
- `Broad Risk-On`
- `Broad Risk-Off`
- `Mixed / Unclear`

Do not label inferred price behavior as "net inflow" or "net outflow."

Actual ETF flow data is explicitly deferred to a later milestone/version.

---

# 3. Public Repository Requirement

This project WILL be hosted in a **public GitHub repository**.

This is a hard requirement and must influence all implementation decisions.

## 3.1 Never commit

The repository must never contain:

- API keys
- passwords
- access tokens
- cookies
- session tokens
- personal email addresses
- brokerage credentials
- account numbers
- personal portfolio information
- local machine paths containing usernames
- `.env`
- downloaded private datasets
- browser sessions
- authentication headers

There should be no credentials required for the default MVP.

## 3.2 Required repository protections

Provide:

```text
.env
.env.*
!.env.example
*.db
*.duckdb
data/raw/
data/cache/
.cache/
__pycache__/
node_modules/
dist/
```

in `.gitignore` as appropriate.

If environment variables become necessary later, provide only:

```text
.env.example
```

with placeholder values.

Example:

```text
OPTIONAL_PROVIDER_API_KEY=
```

Never put a real credential into `.env.example`.

## 3.3 Market data

Yahoo/yfinance data must be fetched at runtime.

Do not commit large downloaded Yahoo datasets to Git.

Small synthetic test fixtures may be committed.

Test fixtures should be generated or manually constructed and must not contain personal information.

---

# 4. Target User

Primary user:

A trader/investor who wants a fast visual answer to:

> What is actually moving today?

and:

> Is weakness/strength concentrated in a few sectors, rotating between sectors, or appearing across multiple asset classes?

The MVP is not intended to execute trades.

---

# 5. MVP Goals

The MVP MUST:

1. Download market data using `yfinance`.
2. Store/cache normalized data locally.
3. Track a fixed initial asset universe.
4. Calculate:
   - 1-day return
   - 5-day return
   - 20-day return
   - relative performance vs SPY
   - sector breadth
   - sector dispersion
   - RSP vs SPY
   - HYG vs LQD
5. Produce a sector heatmap/table.
6. Produce a relative rotation chart.
7. Produce a cross-asset overview.
8. Produce a deterministic market-regime classification.
9. Explain why the current regime was selected.
10. Clearly display data freshness.
11. Handle missing or stale data without crashing.
12. Have automated tests for calculations and regime classification.
13. Be easy for another developer to run locally.
14. Keep market-data providers replaceable.

---

# 6. Non-Goals for MVP

Do NOT implement:

- Brokerage integration.
- Trade execution.
- User authentication.
- User accounts.
- Portfolio tracking.
- AI/LLM analysis.
- News integration.
- Benzinga integration.
- Economic calendar.
- Options/GEX.
- SEC data.
- Real ETF fund flows.
- Prediction models.
- Machine learning.
- Backtesting.
- Mobile application.
- Alerts.
- Push notifications.
- WebSockets.
- Multi-user infrastructure.

These can be future enhancements.

The coding agent should not expand scope without an explicit requirement change.

---

# 7. Technology Stack

Recommended implementation:

## Backend

Python 3.12+

Use:

- FastAPI
- pandas
- numpy
- yfinance
- DuckDB
- Pydantic
- pytest

## Frontend

Use:

- React
- TypeScript
- Vite
- shadcn/ui
- Tailwind CSS
- Recharts or Plotly for charts

Prefer Recharts for ordinary charts.

Plotly is acceptable if it significantly simplifies the relative-rotation scatter/trail visualization.

## Storage

Use:

```text
DuckDB
```

Storage should remain local.

The database must NOT be committed to Git.

---

# 8. Architecture

Use this architecture:

```text
                    ┌──────────────────┐
                    │   React Client   │
                    └────────┬─────────┘
                             │
                           HTTP
                             │
                    ┌────────▼─────────┐
                    │     FastAPI      │
                    │       API        │
                    └────────┬─────────┘
                             │
                ┌────────────┼─────────────┐
                │            │             │
                ▼            ▼             ▼
          MarketService  RegimeService  MetricsService
                │
                ▼
        MarketDataProvider
                │
        ┌───────┴────────┐
        │                │
        ▼                ▼
 YFinanceProvider   FutureProvider
        │
        ▼
     DuckDB
```

The frontend must never directly call `yfinance`.

All external market-data access belongs behind the backend provider interface.

---

# 9. Market Data Provider Interface

Create an explicit interface similar to:

```python
class MarketDataProvider(Protocol):

    def get_history(
        self,
        symbols: list[str],
        start: datetime,
        end: datetime,
        interval: str,
    ) -> pd.DataFrame:
        ...

    def get_latest(
        self,
        symbols: list[str],
    ) -> pd.DataFrame:
        ...
```

Implement:

```text
YFinanceMarketDataProvider
```

The rest of the application must depend on `MarketDataProvider`, NOT directly on `yfinance`.

This allows future providers such as:

```text
TiingoMarketDataProvider
PolygonMarketDataProvider
DatabentoMarketDataProvider
```

without rewriting business logic.

---

# 10. Asset Universe

Store the universe in configuration rather than hardcoding symbols throughout application logic.

Example:

```yaml
sectors:
  XLK: Technology
  XLF: Financials
  XLE: Energy
  XLV: Health Care
  XLI: Industrials
  XLY: Consumer Discretionary
  XLP: Consumer Staples
  XLU: Utilities
  XLB: Materials
  XLRE: Real Estate
  XLC: Communication Services

equity:
  SPY: S&P 500
  QQQ: Nasdaq 100
  IWM: Russell 2000
  RSP: S&P 500 Equal Weight

rates:
  SHY: Short Treasury
  IEF: 7-10Y Treasury
  TLT: 20+Y Treasury

credit:
  HYG: High Yield Credit
  LQD: Investment Grade Credit

commodities:
  GLD: Gold
  SLV: Silver
  USO: Oil
  DBC: Broad Commodities

currency:
  UUP: US Dollar

volatility:
  ^VIX: VIX
```

For MVP, prefer ETFs over commodity futures where practical because they simplify price-history comparison.

Future versions may add:

```text
GC=F
CL=F
DX-Y.NYB
```

as direct futures/index benchmarks.

---

# 11. Historical Data Requirements

The application should request enough daily history to calculate stable metrics.

Default:

```text
History: 400 calendar days
Interval: 1d
```

This should normally provide approximately one trading year or more.

Use adjusted prices consistently.

All return calculations must use the same price field.

Recommended:

```text
auto_adjust=True
Close
```

---

# 12. Refresh Behavior

## MVP default

On application startup:

1. Check cached data.
2. Determine most recent available date.
3. Request missing data.
4. Update DuckDB.
5. Calculate metrics.
6. Serve dashboard.

Provide manual:

```text
Refresh Data
```

button.

The backend should enforce a short cooldown to prevent repeated requests caused by accidental double clicks.

Example:

```text
minimum refresh interval = 60 seconds
```

MVP does NOT require continuously streaming prices.

---

# 13. Data Freshness

Every dashboard must visibly show:

```text
Last updated: 2026-09-18 16:05 ET
```

Also expose:

```text
data_timestamp
retrieved_at
provider
```

through the API.

If the latest available observation is older than expected, show:

```text
STALE DATA
```

instead of silently presenting it as current.

Do not assume weekends and holidays are data failures.

---

# 14. DuckDB Schema

Recommended table:

```sql
CREATE TABLE market_prices (
    symbol VARCHAR NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    interval VARCHAR NOT NULL,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume DOUBLE,
    provider VARCHAR NOT NULL,
    retrieved_at TIMESTAMP NOT NULL,
    PRIMARY KEY(symbol, timestamp, interval)
);
```

Optional metadata table:

```sql
CREATE TABLE instruments (
    symbol VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    category VARCHAR NOT NULL,
    subgroup VARCHAR,
    benchmark_symbol VARCHAR
);
```

Do not store application secrets in DuckDB.

---

# 15. Return Calculations

For each instrument calculate:

```text
1D
5D
20D
```

Define N-day return as:

```text
return_N = latest_close / close_N_sessions_ago - 1
```

Use trading observations rather than calendar-day subtraction.

Example:

```text
5D = five market sessions
```

not:

```text
five calendar days
```

Return calculations must be implemented in a reusable metrics module.

---

# 16. Relative Strength

For sector ETF `S` relative to SPY:

```text
RelativeRatio(t) = Price(S,t) / Price(SPY,t)
```

For dashboard tables calculate:

```text
RelativeReturn5D =
    SectorReturn5D - SPYReturn5D

RelativeReturn20D =
    SectorReturn20D - SPYReturn20D
```

Positive means the sector outperformed SPY during the period.

Negative means it underperformed.

Do not describe this as fund flow.

---

# 17. Relative Rotation Chart

Create a chart inspired by relative-rotation concepts but do NOT claim to reproduce StockCharts/JdK proprietary metrics.

For every sector:

```text
X = 20-day relative return vs SPY
Y = 5-day relative return vs SPY
```

Quadrants:

```text
                 Y > 0

          IMPROVING | LEADING
                    |
X < 0  -------------+------------- X > 0
                    |
           LAGGING  | WEAKENING

                 Y < 0
```

Definitions:

### Leading

```text
20D relative return > 0
AND
5D relative return > 0
```

### Improving

```text
20D relative return <= 0
AND
5D relative return > 0
```

### Weakening

```text
20D relative return > 0
AND
5D relative return <= 0
```

### Lagging

```text
20D relative return <= 0
AND
5D relative return <= 0
```

Display ticker labels directly.

Optional if easy:

Show the previous five daily positions as a faded trail.

The trail is desirable but is not required for initial completion.

---

# 18. Sector Heatmap

Create a table or heatmap with:

| Sector | Ticker | 1D | 5D | 20D | vs SPY 5D | vs SPY 20D |
|---|---|---:|---:|---:|---:|---:|

Rows should be sortable.

Color cells according to positive/negative performance.

Do not encode meaning purely through color; numeric values must remain visible for accessibility.

---

# 19. Cross-Asset Panel

Display:

```text
SPY
QQQ
IWM
RSP

SHY
IEF
TLT

HYG
LQD

GLD
SLV
USO
DBC

UUP
VIX
```

Show at minimum:

```text
1D
5D
20D
```

Group instruments visually by asset class.

---

# 20. Market Breadth Proxies

Actual NYSE/S&P advance-decline data is not required for MVP.

Instead calculate breadth from the tracked sectors.

## Sector breadth

```text
positive_sector_count_1d =
    count(sector 1D return > 0)

sector_breadth_1d =
    positive_sector_count_1d / 11
```

Repeat for 5D.

Example:

```text
Sector Breadth
8 / 11 positive
73%
```

---

# 21. Equal-Weight Breadth Proxy

Calculate:

```text
RSP / SPY
```

and show:

```text
1D change
5D change
20D change
```

Interpretation displayed in UI:

```text
RSP outperforming SPY
→ broader participation

RSP underperforming SPY
→ larger-cap stocks contributing more to index strength
```

Avoid presenting this interpretation as absolute proof.

---

# 22. Credit Risk Proxy

Calculate:

```text
HYG / LQD
```

and its:

```text
1D
5D
20D
```

relative changes.

Display:

```text
HYG/LQD strengthening
```

or:

```text
HYG/LQD weakening
```

rather than a trading recommendation.

---

# 23. Sector Dispersion

Calculate cross-sectional standard deviation of sector returns:

```text
sector_dispersion_1d =
    stddev(1D returns of 11 sector ETFs)

sector_dispersion_5d =
    stddev(5D returns of 11 sector ETFs)
```

Higher dispersion means sector performance is more spread out.

This is particularly useful for identifying internal rotation.

---

# 24. Defensive vs Cyclical Groups

Define:

```text
DEFENSIVE:
XLV
XLP
XLU
```

Define initial cyclical/growth group:

```text
XLK
XLY
XLI
XLF
XLE
XLB
```

Calculate:

```text
Defensive5D =
    mean(5D returns of XLV, XLP, XLU)

Cyclical5D =
    mean(5D returns of cyclical group)

DefensiveSpread5D =
    Defensive5D - Cyclical5D
```

Keep the group membership in configuration.

---

# 25. Market Regime Engine

The regime engine must be:

- deterministic
- transparent
- configurable
- testable

No LLM should determine regime classification.

Initial regimes:

```text
BROAD_RISK_ON
INTERNAL_ROTATION
DEFENSIVE_ROTATION
BROAD_RISK_OFF
MIXED
```

The algorithm must return both:

```json
{
  "regime": "INTERNAL_ROTATION",
  "confidence": "medium",
  "reasons": [...]
}
```

`confidence` is heuristic confidence in the classification, NOT statistical probability.

---

# 26. Initial Regime Rules

All thresholds must live in configuration rather than being scattered through code.

Suggested starting values follow.

## BROAD_RISK_ON

Example rule:

```text
SPY 5D > +1%
AND
sector breadth 5D >= 7/11
AND
RSP 5D relative to SPY >= 0
AND
HYG 5D relative to LQD >= 0
```

Reason examples:

```text
SPY gained 2.1% over five sessions.
9 of 11 sectors were positive.
Equal-weight S&P outperformed SPY.
High-yield credit outperformed investment-grade credit.
```

---

## INTERNAL_ROTATION

Example:

```text
abs(SPY 5D) <= 2%
AND
at least 3 sectors positive
AND
at least 3 sectors negative
AND
sector dispersion 5D >= configured threshold
```

Initial configurable dispersion threshold:

```text
2.0 percentage points
```

Example explanation:

```text
SPY was approximately flat over five sessions.
5 sectors advanced while 6 declined.
Sector return dispersion was elevated.
```

---

## DEFENSIVE_ROTATION

Example:

```text
DefensiveSpread5D >= +1.0%
AND
at least 2 of XLV/XLP/XLU outperform SPY
AND
QQQ or IWM underperforms SPY
```

Example explanation:

```text
Defensive sectors outperformed cyclical sectors by 1.6%.
Utilities and Consumer Staples outperformed SPY.
Small caps underperformed SPY.
```

---

## BROAD_RISK_OFF

Example:

```text
SPY 5D < -1%
AND
sector breadth 5D <= 4/11
AND
at least two of the following are true:

GLD 5D > SPY 5D
IEF or TLT 5D > SPY 5D
HYG underperforms LQD
VIX 5D > 0
```

This regime should be described as:

```text
Broad Risk-Off
```

NOT:

```text
Money definitely left the stock market.
```

---

## MIXED

If none of the previous conditions are satisfied:

```text
MIXED
```

Provide the strongest contributing observations anyway.

---

# 27. Regime Rule Priority

Some rules may overlap.

Evaluate in this order:

```text
1. BROAD_RISK_OFF
2. DEFENSIVE_ROTATION
3. BROAD_RISK_ON
4. INTERNAL_ROTATION
5. MIXED
```

The implementation must document this priority.

Future work can replace this with a scoring model.

---

# 28. Regime Explanation UI

The dashboard header should look conceptually like:

```text
MARKET REGIME

INTERNAL ROTATION

SPY 5D: +0.3%
Sector breadth: 6 / 11
Sector dispersion: 2.4%

Why:
• Energy +3.4%
• Financials +1.8%
• Technology -2.1%
• Healthcare -1.2%
• Broad index remained approximately flat
```

Users should never need to guess how the regime was determined.

---

# 29. Dashboard Layout

Desktop-first MVP.

Suggested layout:

```text
┌──────────────────────────────────────────────────────┐
│ MARKET ROTATION DASHBOARD                            │
│ Last updated: ...                     [Refresh Data] │
├──────────────────────────────────────────────────────┤
│                                                      │
│ MARKET REGIME                                        │
│ INTERNAL ROTATION                                    │
│ explanation...                                       │
│                                                      │
├───────────────────────────┬──────────────────────────┤
│ SECTOR HEATMAP            │ RELATIVE ROTATION       │
│                           │                          │
│ XLK  ...                  │           XLE            │
│ XLF  ...                  │         ↗                │
│ XLE  ...                  │                          │
│ ...                       │                          │
├───────────────────────────┴──────────────────────────┤
│ CROSS-ASSET PERFORMANCE                              │
│                                                      │
│ Equities | Rates | Credit | Commodities | USD | VIX │
├──────────────────────────────────────────────────────┤
│ MARKET INTERNALS                                     │
│                                                      │
│ Sector Breadth   RSP/SPY   HYG/LQD   Dispersion     │
└──────────────────────────────────────────────────────┘
```

---

# 30. API Design

Implement at minimum:

## Health

```http
GET /api/health
```

Response:

```json
{
  "status": "ok"
}
```

---

## Universe

```http
GET /api/universe
```

Return instrument metadata.

---

## Dashboard

```http
GET /api/dashboard
```

Recommended response structure:

```json
{
  "as_of": "2026-09-18T20:00:00Z",
  "provider": "yfinance",

  "regime": {
    "name": "INTERNAL_ROTATION",
    "confidence": "medium",
    "reasons": []
  },

  "sectors": [],

  "cross_asset": [],

  "breadth": {
    "positive_1d": 7,
    "total": 11,
    "ratio_1d": 0.636
  },

  "dispersion": {
    "one_day": 0.014,
    "five_day": 0.023
  },

  "ratios": {
    "rsp_spy": {},
    "hyg_lqd": {}
  }
}
```

---

## Refresh

```http
POST /api/data/refresh
```

Response:

```json
{
  "status": "success",
  "updated_symbols": 27,
  "failed_symbols": [],
  "as_of": "..."
}
```

A partial provider failure must not crash the API.

---

# 31. Error Handling

The app must handle:

- ticker unavailable
- Yahoo request timeout
- rate limiting
- malformed response
- missing trading sessions
- empty result
- one instrument missing
- network unavailable
- stale cache
- DuckDB unavailable/corrupt

If one nonessential symbol fails, the entire dashboard should not fail.

Return data-quality warnings such as:

```json
{
  "warnings": [
    "USO data is unavailable.",
    "Latest TLT observation is stale."
  ]
}
```

Display these warnings in the UI.

---

# 32. Repository Structure

Recommended:

```text
market-rotation-dashboard/
│
├── README.md
├── LICENSE
├── SECURITY.md
├── .gitignore
├── .env.example
│
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py
│   │   │
│   │   ├── api/
│   │   │   ├── dashboard.py
│   │   │   ├── health.py
│   │   │   └── refresh.py
│   │   │
│   │   ├── providers/
│   │   │   ├── base.py
│   │   │   └── yfinance_provider.py
│   │   │
│   │   ├── services/
│   │   │   ├── market_service.py
│   │   │   ├── metrics_service.py
│   │   │   └── regime_service.py
│   │   │
│   │   ├── storage/
│   │   │   └── duckdb_repository.py
│   │   │
│   │   ├── models/
│   │   │   └── schemas.py
│   │   │
│   │   └── config/
│   │       ├── universe.yaml
│   │       └── regimes.yaml
│   │
│   └── tests/
│       ├── fixtures/
│       ├── test_metrics.py
│       ├── test_regimes.py
│       ├── test_provider.py
│       └── test_api.py
│
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── api/
│   │   └── types/
│   └── tests/
│
└── docs/
    ├── architecture.md
    ├── data-methodology.md
    └── screenshots/
```

---

# 33. Testing Requirements

Calculations must not rely solely on tests against live Yahoo data.

Live external APIs make tests nondeterministic.

Use synthetic fixtures.

Example fixture:

```text
SPY:
100, 101, 102...

XLE:
100, 103, 106...
```

Tests should know the expected mathematical result exactly.

---

# 34. Milestone 0 — Repository Foundation

## Deliverables

Create:

- public-ready repository structure
- backend skeleton
- frontend skeleton
- README
- LICENSE
- `.gitignore`
- `.env.example`
- SECURITY.md
- test frameworks
- formatting/linting configuration

Set up GitHub Actions.

CI should run:

```text
backend lint
backend tests
frontend lint
frontend type-check
frontend tests
frontend build
```

## Acceptance Criteria

- [ ] Repository can safely be made public.
- [ ] No secrets or personal information exist anywhere in tracked files.
- [ ] `.env` is ignored.
- [ ] DuckDB/data files are ignored.
- [ ] Backend starts successfully.
- [ ] Frontend starts successfully.
- [ ] `/api/health` returns HTTP 200.
- [ ] CI executes on pull requests.
- [ ] CI passes from a fresh clone.
- [ ] README contains local setup instructions.

---

# 35. Milestone 1 — Market Data Layer

## Deliverables

Implement:

```text
MarketDataProvider
YFinanceMarketDataProvider
DuckDB storage
universe.yaml
```

Download at least 400 calendar days of daily prices.

Implement cache/update logic.

## Acceptance Criteria

- [ ] All configured tickers are loaded from configuration.
- [ ] Business logic does not directly import `yfinance`.
- [ ] Only `YFinanceMarketDataProvider` imports `yfinance`.
- [ ] Multiple symbols can be fetched in one operation.
- [ ] Data is normalized into a common schema.
- [ ] Data is persisted in DuckDB.
- [ ] Re-running refresh does not duplicate rows.
- [ ] Missing data for one ticker does not destroy data for other tickers.
- [ ] Provider errors produce structured errors/warnings.
- [ ] Unit tests use mocks/fixtures rather than requiring Yahoo.
- [ ] Application works using cached data when Yahoo is temporarily unavailable.
- [ ] Local database files cannot accidentally be committed.

---

# 36. Milestone 2 — Analytics Engine

## Deliverables

Implement:

```text
1D return
5D return
20D return

sector relative performance
sector breadth
sector dispersion
RSP/SPY
HYG/LQD
defensive/cyclical spread
relative rotation coordinates
```

## Acceptance Criteria

Using known synthetic datasets:

- [ ] 1D returns match expected values.
- [ ] 5D returns match expected values.
- [ ] 20D returns match expected values.
- [ ] Returns use trading observations rather than calendar-day offsets.
- [ ] Sector relative returns vs SPY are correct.
- [ ] Sector breadth is correct.
- [ ] Sector dispersion is mathematically correct.
- [ ] RSP/SPY calculations are correct.
- [ ] HYG/LQD calculations are correct.
- [ ] Defensive/cyclical spread is correct.
- [ ] Rotation quadrant assignment is correct.
- [ ] Missing values produce controlled results rather than silent mathematical errors.
- [ ] All metric functions have automated unit tests.

Minimum backend unit-test coverage target for analytics code:

```text
90%
```

---

# 37. Milestone 3 — Regime Classification Engine

## Deliverables

Implement configurable deterministic regime rules.

Return:

```text
regime
confidence
reasons
metrics used
```

Create synthetic scenarios for each regime.

Example fixtures:

```text
broad_risk_on.json
internal_rotation.json
defensive_rotation.json
broad_risk_off.json
mixed.json
```

## Acceptance Criteria

- [ ] BROAD_RISK_ON fixture produces BROAD_RISK_ON.
- [ ] INTERNAL_ROTATION fixture produces INTERNAL_ROTATION.
- [ ] DEFENSIVE_ROTATION fixture produces DEFENSIVE_ROTATION.
- [ ] BROAD_RISK_OFF fixture produces BROAD_RISK_OFF.
- [ ] Ambiguous fixture produces MIXED.
- [ ] Rule thresholds live in configuration.
- [ ] Rule priority is explicitly implemented.
- [ ] Every regime result contains human-readable reasons.
- [ ] No LLM/API is required for classification.
- [ ] No result describes inferred price behavior as confirmed fund flows.
- [ ] Tests cover overlapping-rule cases.
- [ ] Tests cover missing benchmark data.

---

# 38. Milestone 4 — Dashboard UI

## Deliverables

Build the complete dashboard UI.

Components:

```text
DashboardHeader
RegimeCard
SectorHeatmap
RelativeRotationChart
CrossAssetPanel
MarketInternalsPanel
DataQualityBanner
RefreshButton
```

## SectorHeatmap

Must display:

```text
Ticker
Sector
1D
5D
20D
vs SPY 5D
vs SPY 20D
```

## RelativeRotationChart

Must display all 11 sectors.

Axes centered at:

```text
X = 0
Y = 0
```

Quadrants visibly labeled:

```text
Leading
Improving
Weakening
Lagging
```

## MarketInternalsPanel

Display:

```text
Sector Breadth
Sector Dispersion
RSP/SPY
HYG/LQD
Defensive Spread
```

## Acceptance Criteria

- [ ] User can see current regime without scrolling on normal desktop resolution.
- [ ] User can see why the regime was assigned.
- [ ] All 11 sectors appear in the heatmap.
- [ ] All 11 sectors appear in the rotation chart.
- [ ] Cross-asset instruments are grouped logically.
- [ ] Positive and negative performance are visually distinguishable.
- [ ] Numeric values are available in addition to colors.
- [ ] Dashboard displays the data timestamp.
- [ ] Dashboard displays provider name.
- [ ] Stale data is visibly labeled.
- [ ] Missing data generates a visible warning without breaking the page.
- [ ] Refresh button triggers backend refresh.
- [ ] Refresh button shows loading state.
- [ ] API errors generate a useful error state.
- [ ] Layout is usable at standard desktop widths.
- [ ] No credentials are requested in the UI.

---

# 39. Milestone 5 — Documentation and Public Release

## Deliverables

Complete:

```text
README.md
docs/architecture.md
docs/data-methodology.md
SECURITY.md
LICENSE
```

README should contain:

1. Screenshot.
2. What the project does.
3. What the project does NOT do.
4. Architecture summary.
5. Data source.
6. Local setup.
7. Development commands.
8. Testing commands.
9. Methodology summary.
10. Data/legal disclaimer.

Explicitly explain:

> The dashboard infers rotation/risk regimes from market prices and relative performance. It does not measure actual money flows in the MVP.

Also explain that users are responsible for complying with the terms applicable to external market-data providers.

## Acceptance Criteria

From a completely clean environment, another developer can:

```text
git clone ...
install backend
install frontend
start backend
start frontend
open dashboard
download data
view regime
run tests
```

without requiring private credentials.

Additionally:

- [ ] No personal information exists in repository history intended for release.
- [ ] Secret-scanning finds no credentials.
- [ ] README clearly identifies `yfinance` as the default provider.
- [ ] README explains that the provider can be replaced.
- [ ] Methodology documents every metric used by the regime engine.
- [ ] All CI checks pass.
- [ ] Production frontend build succeeds.
- [ ] Backend test suite passes.
- [ ] Repository is ready to be made public.

---

# 40. Definition of MVP Complete

MVP is complete only when a user can run the repository locally and open a dashboard that provides an answer like:

```text
MARKET REGIME
Internal Rotation

Why:
SPY 5D: +0.4%
Sector breadth: 6 / 11
Sector dispersion: 2.3%

Leading:
XLE +4.1%
XLF +2.3%

Lagging:
XLK -2.0%
XLY -1.5%

Cross Asset:
TLT +0.2%
GLD +0.8%
HYG/LQD -0.1%

Interpretation:
The broad equity index is approximately flat while sector
performance is highly dispersed, which is consistent with
rotation within equities rather than a uniform market move.
```

The dashboard must show the underlying metrics so that the user can independently evaluate that interpretation.

---

# 41. Deferred Phase 2 Features

Do NOT implement these as part of MVP, but structure the system so they can be added later.

## Actual ETF fund flow data

Add:

```text
daily net flow
5D cumulative net flow
20D cumulative net flow
flow / AUM
```

This will allow us to distinguish price-based rotation signals from actual ETF creations/redemptions.

---

## Intraday Mode

Potential:

```text
5-minute / 15-minute bars
today return
since-open return
rolling relative strength
intraday regime change
```

This should remain separate from the initial daily analytics because intraday data has different reliability and caching requirements.

---

## Historical Regime Timeline

Show:

```text
Risk On
→ Internal Rotation
→ Defensive Rotation
→ Risk Off
```

through time.

This will eventually make the dashboard substantially more useful for event-driven analysis.

---

## Event Overlay

Future integration with the separate event/news system could mark:

```text
CPI
FOMC
Fed speeches
earnings
geopolitical events
major headlines
```

against changes in the market-rotation regime.

---

## Additional Breadth Data

Potential future metrics:

```text
NYSE Advance/Decline
S&P 500 Advance/Decline
% above 20 DMA
% above 50 DMA
52-week highs/lows
up-volume/down-volume
```

These require additional data sources beyond the initial yfinance universe.

---

# 42. Implementation Principles

The coding agent should follow these principles throughout implementation.

### 1. Keep provider code isolated

Never tightly couple calculations or UI to Yahoo Finance.

### 2. Prefer transparent calculations

Every displayed metric should have a documented formula.

### 3. No magic AI

The MVP regime classifier must be deterministic and testable.

### 4. Cache external data

Avoid unnecessary repeated Yahoo requests.

### 5. Degrade gracefully

One failed ticker must not crash the entire dashboard.

### 6. Avoid false precision

The dashboard identifies market behavior patterns. It does not prove causality or literal movement of investor dollars.

### 7. Public-by-default security

Assume every committed file will be visible to the entire internet.

Never place anything personal or secret in repository contents, configuration, tests, screenshots, sample data, commit messages, or documentation.

### 8. Do not expand MVP scope

Complete the specified milestones before adding additional indicators or features.