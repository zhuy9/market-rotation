# Architecture

```text
                    React Client (Vite/TS)
                             │
                           HTTP (fetch, TanStack Query)
                             │
                    ┌────────▼─────────┐
                    │     FastAPI      │
                    │   /api/health    │
                    │   /api/universe  │
                    │  /api/dashboard  │
                    │ /api/data/refresh│
                    └────────┬─────────┘
                             │
                ┌────────────┼──────────────┐
                │            │              │
                ▼            ▼              ▼
         MarketService  MetricsService  RegimeService
         (refresh/cache)  (pure calc)   (rule engine)
                │              ▲              ▲
                │              └──────┬───────┘
                │                     │
                │              DashboardService
                │            (composes the above)
                ▼
        MarketDataProvider (Protocol)
                │
        ┌───────┴────────┐
        │                │
        ▼                ▼
 YFinanceMarketDataProvider   (future: Tiingo/Polygon/Databento)
        │
        ▼
     DuckDB (local cache, git-ignored)
```

## Layers

### `app/providers`

`MarketDataProvider` (`base.py`) is a `Protocol` with two methods:
`get_history(symbols, start, end, interval)` and `get_latest(symbols)`,
both returning a long-format DataFrame (`symbol, timestamp, open, high, low,
close, volume`).

`YFinanceMarketDataProvider` is the only module in the codebase allowed to
`import yfinance` — enforced by an automated test
(`tests/test_architecture.py`). A provider must never raise for a single bad
symbol; it omits that symbol from the result instead, so the rest of the
batch still succeeds.

Adding a new data source (Tiingo, Polygon, Databento, ...) means writing one
new class that satisfies `MarketDataProvider` and swapping it in
`app/deps.py`. Nothing else in the app changes.

### `app/storage`

`DuckDBRepository` owns the `market_prices` table (schema in
`data-methodology.md`). `upsert_prices` uses `INSERT OR REPLACE`, keyed on
`(symbol, timestamp, interval)`, so re-running a refresh never duplicates
rows. The database file lives at `backend/data/market.duckdb` and is
git-ignored.

FastAPI serves this app's sync endpoints from a threadpool, so one repository
instance is reached by several requests at once. A DuckDB connection is not
thread-safe — sharing one returns `None` from concurrent reads and can
deadlock a read/write mix — so every statement runs on its own `cursor()` and
writes take a lock.

### `app/services`

- **`market_service.py`** — orchestrates fetching (via the provider) and
  caching (via the repository). Requests only the sessions missing since the
  cached edge rather than the whole window, enforces the 60-second refresh
  cooldown, and reports `success` / `partial` / `failed` / `cooldown` so a
  partial provider outage never crashes the API. `refresh_if_stale()` is the
  startup path — see `data-methodology.md` for the full refresh rules.
- **`metrics_service.py`** — pure, dependency-free calculation functions
  (returns, relative return, breadth, dispersion, ratio returns, defensive/
  cyclical spread, rotation quadrants). Every function returns `None`/`NaN`
  instead of raising when data is missing.
- **`regime_service.py`** — deterministic rule engine. See
  `data-methodology.md` for the exact rules, thresholds, and priority order.
- **`dashboard_service.py`** — the only place that ties the other three
  together into the payload the frontend consumes.

### `app/api`

Thin FastAPI routers. Each endpoint depends on a service via
`app/deps.py` (`lru_cache`-backed singletons), which is also the seam tests
use to substitute fakes via `app.dependency_overrides`. `main.py` adds a
lifespan hook that tops up a stale cache before the app starts serving.

### `app/config`

`universe.yaml` (asset universe), `groups.yaml` (defensive/cyclical sector
membership), and `regimes.yaml` (regime rule thresholds). Nothing about the
tracked symbols or rule thresholds is hardcoded in Python.

### Frontend (`frontend/src`)

- `api/client.ts` — the only place that calls `fetch`. The frontend never
  talks to Yahoo Finance directly, only to the FastAPI backend.
- `hooks/useDashboard.ts` — TanStack Query wraps `GET /api/dashboard` (query)
  and `POST /api/data/refresh` (mutation that invalidates the query on
  success), giving loading/error/refetch states without hand-rolled effects.
- `components/` — one component per PRD dashboard section (regime card,
  sector heatmap, relative-rotation chart, cross-asset panel, market
  internals, data-quality banner, refresh button).
