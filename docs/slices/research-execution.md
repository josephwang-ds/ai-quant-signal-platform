# Research Execution (PR-008B)

## Outcome

Load authentic SPY history through Infrastructure, run a deterministic MA20/60
backtest in Application/calc code, expose `POST /api/v1/research/execution`, and
connect only the canonical Research Workspace (`ma-crossover-spy`) to that
endpoint. The frontend displays evidence; it never fetches Yahoo Finance or
computes strategy metrics.

## Incremental integration path

Chosen path (smallest correct slice):

1. New package `backend/app/research_execution/` (port, Yahoo adapter, fixture
   adapter, filesystem cache, calculations, service, schemas).
2. New FastAPI router mounted on the existing learning-stage `backend/app/main.py`.
3. Frontend client + overlay helpers; canonical research id only.
4. Leave legacy `/api/backtest` and modular-monolith `apps/api` untouched.

Domain/Application never import `yfinance`. Presentation never invents fallback
numbers when the provider or API fails.

Legacy Strategy Lab (`backend/app/backtest/`) remains for `/api/backtest` demos.
Research Workspace uses only `research_execution` so MA conventions
(adjusted_close, one-day lag, JSON-safe metrics) stay consistent for this path.

## API contract

`POST /api/v1/research/execution`

Request (defaults shown):

```json
{
  "research_id": "ma-crossover-spy",
  "symbol": "SPY",
  "benchmark": "SPY",
  "start_date": "2018-01-01",
  "end_date": null,
  "short_window": 20,
  "long_window": 60,
  "transaction_cost": 0.001,
  "risk_free_rate": 0
}
```

Also accepted research id alias: `rs-ma-crossover-001`.

**Benchmark rule (PR-008B):** `benchmark` must equal `symbol` (same-asset
buy-and-hold only). Independent benchmark series are deferred. Mismatched
values return HTTP **400** with:

`PR-008B supports only same-asset buy-and-hold benchmarking. Independent benchmark series are deferred.`

Response `strategy.benchmark` / `benchmark_label` always describe the calculated
same-asset buy-and-hold series (never a different ticker).

**Open-ended `end_date: null`:** bars on or after the current calendar date in
`America/New_York` are excluded so an incomplete in-session daily bar is never
treated as complete. Provenance `actual_end` reflects the last retained bar.
An explicit `end_date` is not clipped by this rule.

**Yahoo timeout:** `YahooFinanceMarketDataAdapter(timeout_seconds=…)` is passed
to `yfinance.download(..., timeout=…)`. Timeouts map to `MarketDataUnavailableError`
(HTTP 502 via the service).

Response includes `strategy`, `provenance`, `metrics`, `benchmark_metrics`,
`series`, `warnings`, `generated_at`, and `supported_evidence`.

HTTP:

- `400` / `422` — invalid parameters or insufficient history
- `502` — provider unavailable (never substitutes fake metrics)

## Calculation definitions

| Item | Definition |
| --- | --- |
| Price field | `adjusted_close` |
| Short / long MA | Rolling mean of adjusted close (windows 20 / 60) |
| Signal | `1` when short MA > long MA, else `0` |
| Position | `signal.shift(1)` — one trading-day lag, no look-ahead |
| Warm-up | First rows until long MA is defined are excluded from metrics |
| Daily strategy return | `position * asset_return − \|Δposition\| * transaction_cost` |
| Transaction cost | Per **unit position turnover** (`\|Δposition\| × cost`). For 0/1 positions this equals cost on each **entry or exit**. First valid row turnover forced to 0 (no invented opening trade). |
| Benchmark | Buy-and-hold of the same adjusted-close series |
| Annualization | **252** trading days |
| Trade count | Number of days with `turnover > 0` after warm-up |
| Win rate | Fraction of days with non-zero position whose strategy return > 0 |
| JSON safety | Non-finite metrics → `null` + warning (never NaN/Infinity) |

## Data provenance and cache

Normalized OHLCV fields: symbol, date, open, high, low, close, adjusted_close,
volume, plus provenance: source, retrieved_at, requested/actual start/end,
cache_hit, cache_stale.

**Provider:** Yahoo Finance via `yfinance` (research/demo grade — not
exchange-grade; replaceable through `MarketDataPort`).

**Cache:** filesystem under `backend/.cache/market_data/`.

- Key: `provider|symbol|start|end|interval`
- TTL: **24 hours** (`CACHE_TTL_SECONDS`)
- Cached hits preserve original `retrieved_at`
- Stale cache may be used on provider failure **only** when labeled `cache_stale`
- No fabricated price series on failure

## Environment

| Variable | Purpose |
| --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | Frontend → FastAPI base (default `http://127.0.0.1:8000`) |

Optional: none required for fixture tests. Live Yahoo needs network.

## Local run

```bash
# Backend
cd backend
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

## Tests

```bash
# Offline fixture suite (default CI)
cd backend && PYTHONPATH=. python -m pytest tests/test_research_execution.py -v

# Optional live Yahoo smoke (excluded from default CI)
cd backend && PYTHONPATH=. python -m pytest tests/test_research_execution_live.py -v -m live

# Frontend
cd frontend && npm test && npm run build
```

## Supported vs unavailable evidence

Supported after successful execution:

- Authentic historical backtest → Completed
- Same-asset buy-and-hold benchmark comparison → Completed

Remain unavailable / not started:

- OOS
- Parameter sensitivity
- Stress testing
- Regime analysis
- Full robustness evaluation
- Transaction-cost review grid
- Formal data-quality review
- Evaluation / Research Confidence score
- Publish Strategy, Paper Trading, Portfolio
