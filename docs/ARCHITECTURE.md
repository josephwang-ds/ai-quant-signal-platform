# AI Quant Research Workspace — Architecture (Legacy Snapshot)

> **Status: Legacy**  
> **Not the frozen architecture source of truth.**  
> Use [`docs/PROJECT_BIBLE.md`](PROJECT_BIBLE.md) and the [Architecture Bible](Architecture-Bible/) for authoritative product, domain, state, and runtime design.  
> Use [`PROJECT_STRUCTURE.md`](../PROJECT_STRUCTURE.md) for current vs target repository layout.  
> This file is retained as a historical implementation/planning snapshot from the pre–Architecture Bible era. Do not extend it.

## Product concept

**AI Quant Research Workspace** is a modular quant research environment for portfolio showcase and research demonstration. It separates concerns across data ingestion, signal research, rule-based strategies, ML experiments, durable research assets, and AI-assisted explanation.

Core design principles:

- **Data Center** manages data sources and data quality.
- **Cache** holds temporary, rebuildable data.
- **Database** stores durable research assets.
- **Strategy Lab** is for rule-based strategies.
- **Model Lab** is for ML / deep learning signal research.
- **Experiments** stores saved backtests, trade logs, strategy comparisons, and model runs.
- **Research Notes** holds human and AI-generated research notes.
- **AI Research Agent** provides explanation and workflow support — not trading.

This document describes a historical intended architecture. Database, cache, ML, and LLM implementations remain subject to the frozen Architecture Bible and accepted ADRs.

---

## Production Deployment

| Component | Platform | URL / config |
|-----------|----------|--------------|
| Frontend | Vercel | Requires `NEXT_PUBLIC_API_BASE_URL` in production; no hardcoded production fallback |
| Backend | Render | `https://ai-quant-signal-platform.onrender.com` |
| Database | Supabase Postgres | Transaction Pooler via backend `SUPABASE_DB_URL` only |

Rules:

- **Active backend URL:** `https://ai-quant-signal-platform.onrender.com`
- **Backend env:** `SUPABASE_DB_URL` (Render Environment; never commit real credentials)
- **Frontend must not** connect directly to Supabase; all DB access goes through FastAPI
- Local dev: frontend → `http://127.0.0.1:8000` when the env is unset
- `NEXT_PUBLIC_API_BASE_URL` always takes precedence when set
- Production fails with a typed configuration error when the env is unset or invalid
- Do **not** use `https://ai-quant-backend.onrender.com` (deprecated / inactive)

### Canonical production endpoints

```bash
curl https://ai-quant-signal-platform.onrender.com/health
curl https://ai-quant-signal-platform.onrender.com/api/data-sources/status
curl https://ai-quant-signal-platform.onrender.com/api/database/status
```

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Process liveness only |
| `GET /api/data-sources/status` | Configured/install-time active and planned providers; not live connectivity |
| `GET /api/database/status` | Supabase Postgres connectivity |

---

## Module map

| Frontend route | Module | Purpose |
|----------------|--------|---------|
| `/` | Overview | Landing page with module links and system notes |
| `/data-center` | Data Center | Data sources, provider status, symbol metadata, freshness |
| `/market-watch` | Market Watch | Signal ranking, ticker detail, indicator charts |
| `/strategy-lab` | Strategy Lab | Rule-based backtests (MA, Momentum, Combined) |
| `/comparison` | Strategy Comparison | Compare strategies vs buy & hold |
| `/robustness` | Robustness Checks | Sensitivity, OOS, walk-forward (later) |
| `/model-lab` | Model Lab | ML dataset, features, training, evaluation |
| `/experiments` | Experiments | Saved runs and experiment history |
| `/research-notes` | Research Notes | Human and AI notes linked to research |
| `/ai-agent` | AI Research Agent | LLM explanations and note drafting |

---

## Data source layer

Providers under `backend/app/data_providers/`:

| Provider | Market | Status |
|----------|--------|--------|
| `akshare_provider.py` | A-shares + US equities (China-friendly free) | **Active** (primary in `auto`) |
| `yahoo_provider.py` | US / global via Yahoo | **Active** (failover) |
| `stooq_provider.py` | US / HK / EU via free CSV | **Active** (last failover) |
| `coingecko_provider.py` | Crypto | Planned |
| `tushare_provider.py` | China markets | Planned |
| `csv_provider.py` | User upload | Planned |
| Paid APIs | As needed | Future |

All providers implement a common interface in `base.py`:

- Symbol metadata resolution
- Historical OHLCV fetch with adjustment mode
- Provider health / freshness reporting

Default request mode is `data_source=auto` with failover order **AKShare → Yahoo → Stooq**. Callers may lock a single provider. Manual lock does **not** fall back on failure.

The **Data Center** frontend module surfaces configured/install-time provider status, preferred-source selection (localStorage), and a separate price probe action.

### Data Center (live status + preference)

| Provider | Asset focus | Status |
|----------|-------------|--------|
| auto | Routes via failover chain | **Active (default)** |
| AKShare | A-shares, US equities | **Active** when package installed |
| Yahoo / yfinance | US stocks, ETFs, HK, basic CN A-share, basic crypto, indices, FX, futures | **Active** |
| Stooq | US / HK / EU free CSV | **Active** (may hit bot checks on some networks) |
| CoinGecko | Crypto market cap, volume, historical crypto data | Planned |
| CSV upload | Custom local research datasets, Model Lab experiments | Planned |
| Tushare / BaoStock | Alternative China market data | Coming later |

Cache remains postponed. Database preparation v1 plus Experiments Persistence v1 store saved backtest runs and trade logs (not raw OHLCV).

#### Market data normalization target schema

Future providers should normalize into a common OHLCV schema before Strategy Lab or Model Lab consumes data:

`date`, `open`, `high`, `low`, `close`, `volume`, `symbol`, `market`, `data_source`, `adjustment`, `currency`

### Provider Abstraction v1 (backend)

Provider Abstraction v1 introduces a unified backend entry point for market data.

| Component | Path | Role |
|-----------|------|------|
| `MarketDataRequest` | `backend/app/data_providers/base.py` | Request dataclass |
| `MarketDataProvider` | `backend/app/data_providers/base.py` | Provider protocol |
| `AkshareProvider` | `backend/app/data_providers/akshare_provider.py` | Primary free / China-friendly provider |
| `YahooProvider` | `backend/app/data_providers/yahoo_provider.py` | Yahoo/yfinance provider |
| `StooqProvider` | `backend/app/data_providers/stooq_provider.py` | Free CSV last resort |
| `MarketDataService` | `backend/app/services/market_data_service.py` | Routes `data_source` / `auto` failover |
| `load_price_data()` | `yahoo_provider.py` | Backward-compatible helper → `MarketDataService` |

Status:

- **Default:** `auto` (`akshare` → `yahoo` → `stooq`)
- **Active locks:** `akshare`, `yahoo`, `stooq`
- **Planned:** `coingecko`, `csv`

Rules:

- Strategy, model, and research modules should not call provider-specific code directly.
- All providers normalize to: `date`, `open`, `high`, `low`, `close`, `volume`
- Optional metadata: `symbol`, `market`, `data_source`, `adjustment`
- Cache will later wrap `MarketDataService` (not implemented in v1).
- Database stores durable research assets, not raw market data in v1.
- CORS allows `GET`, `POST`, and `DELETE` (Experiments delete).

Status endpoint: `GET /api/data-sources/status`

### Database Preparation v1 (backend)

Database Preparation v1 wires Supabase Postgres. Experiments Persistence v1 adds save / list / detail / delete for backtest runs.

| Component | Path | Role |
|-----------|------|------|
| `SUPABASE_DB_URL` | backend env only | Transaction Pooler connection string |
| `get_database_url()` | `backend/app/db/client.py` | Read env; returns `None` if unset |
| `check_database_connection()` | `backend/app/db/client.py` | `select 1` health probe |
| `schema.sql` | `backend/db/schema.sql` | `backtest_runs`, `backtest_trades` tables |

Status endpoint: `GET /api/database/status`

Rules:

- Supabase Postgres is the planned database layer.
- `SUPABASE_DB_URL` is **backend-only**; frontend does not connect directly to Supabase.
- App must not crash if `SUPABASE_DB_URL` is missing.
- `schema.sql` defines `backtest_runs` and `backtest_trades` (UUID PKs, RLS enabled, no policies yet).
- Raw OHLCV market data is **not** stored in database v1.
- Cache remains **postponed** (can introduce stale data and debugging complexity).

### Experiments Persistence v1 (backend + frontend)

Experiments v1 completes the research loop: run backtest → save → review later.

| Component | Path | Role |
|-----------|------|------|
| Repository | `backend/app/db/repositories/backtest_runs.py` | Insert / list / get / delete |
| API routes | `backend/app/api/routes/experiments.py` | REST endpoints |
| Strategy Lab save | `frontend/components/features/strategy-lab/StrategyLabPage.tsx` | Notes + Save button |
| Experiments UI | `frontend/components/features/experiments/ExperimentsPage.tsx` | List + detail |

Endpoints:

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/experiments/backtest-runs` | Save run metadata + trade log |
| `GET` | `/api/experiments/backtest-runs` | List saved runs (newest first) |
| `GET` | `/api/experiments/backtest-runs/{id}` | Detail + trades |
| `DELETE` | `/api/experiments/backtest-runs/{id}` | Delete saved run |

Rules:

- Stores metrics, strategy config, notes, and trade logs only — **not** full equity curves or OHLCV.
- All writes go through FastAPI; frontend never connects to Supabase directly.
- Missing / failed DB returns HTTP 503 with a clear message.
- Requires `backend/db/schema.sql` applied in Supabase (`backtest_runs`, `backtest_trades`).

**Saved Experiments Comparison (frontend v1):** On `/experiments`, select 2–4 saved runs via checkboxes and compare stored metrics side by side (no re-backtest, no new API).

---

## Cache layer

Cache is **disposable and rebuildable**. Clearing cache must not destroy research history stored in the database.

### What should be cached

| Cache use case | Example key pattern |
|----------------|---------------------|
| Price history responses | `price:{source}:{market}:{symbol}:{start}:{end}:{adjustment}` |
| Indicator calculations | `indicators:{source}:{market}:{symbol}:{start}:{end}:{config_hash}` |
| Market watch results | `market_watch:{source}:{market}:{tickers_hash}:{lookback}` |
| Repeated backtest computations | `backtest:{source}:{market}:{symbol}:{strategy_config_hash}:{start}:{end}:{cost}` |
| LLM responses | `llm:{task}:{input_hash}:{model}` |
| Symbol metadata | `symbol:{source}:{market}:{symbol}` |

### Planned backend structure

```
backend/app/cache/
  cache_client.py   # Redis / Upstash client
  keys.py           # Key builders
  ttl.py            # TTL policies per cache type
```

### TTL guidance (planned)

- Price data: short-lived (minutes to hours depending on market hours)
- Indicators: tied to underlying price cache
- Market watch: short-lived per ticker set
- Backtest: medium-lived for identical parameter sets
- LLM: longer-lived for identical prompts and inputs
- Symbol metadata: medium-lived

---

## Database persistence layer

Database stores **durable research assets**, not every raw market data point in v1.

### What should be persisted

- Watchlists and watchlist items
- Signal snapshots
- Saved backtest runs and backtest trades
- Strategy comparison results
- Model experiment runs
- Research notes (human and AI-generated)
- AI agent run metadata

### What not to store in DB v1

- All raw historical OHLCV data
- Temporary API responses
- Every chart response
- Every cacheable indicator result
- Secrets or API keys

### Planned backend structure

```
backend/app/db/
  client.py
  repositories/
    watchlists.py
    signal_snapshots.py
    backtest_runs.py
    model_runs.py
    research_notes.py
```

### Planned tables

| Table | Purpose |
|-------|---------|
| `watchlists` | Named watchlist containers |
| `watchlist_items` | Tickers within a watchlist |
| `signal_snapshots` | Point-in-time signal scores and labels |
| `backtest_runs` | Saved backtest configuration and metrics |
| `backtest_trades` | Trades belonging to a saved backtest run |
| `strategy_comparisons` | Saved multi-strategy comparison results |
| `model_runs` | ML experiment metadata, metrics, artifacts refs |
| `research_notes` | Human and AI notes with optional links |
| `ai_agent_runs` | LLM task logs, inputs hashes, outputs |

SQL migrations are not created yet.

---

## Strategy Lab

Rule-based strategies live in `backend/app/strategies/`:

- `ma_crossover.py`
- `momentum.py`
- `combined_signal.py`

Future: RSI, Bollinger, and additional rule-based strategies.

API routes (planned split): `backend/app/api/routes/backtest.py`

The Strategy Lab frontend owns single-strategy backtest UI, trade log, and buy/sell chart markers. Logic currently exists in the legacy monolithic dashboard and will migrate module by module.

---

## Model Lab

ML and deep learning research is **isolated** from rule-based strategy code.

Planned structure:

```
backend/app/model_lab/
  dataset_builder.py
  feature_builder.py
  train.py
  evaluate.py
  backtest_signal.py
```

Planned capabilities:

- Logistic regression baseline
- XGBoost / LightGBM signal models
- Later: CNN, LSTM, TCN, Transformer-style time-series models
- Model runs saved as experiments in `model_runs` table

API routes (planned): `backend/app/api/routes/model_lab.py`

---

## Experiments

The Experiments module is the review surface for saved research outputs:

- Saved backtest runs
- Saved trade logs
- Saved strategy comparison results
- Saved model runs
- Experiment history timeline

API routes (v1): `backend/app/api/routes/experiments.py`

---

## AI Research Agent

Planned structure:

```
backend/app/ai_agent/
  prompts.py
  tools.py
  summarizer.py
  research_note_writer.py
```

API routes (planned): `backend/app/api/routes/ai_agent.py`

### AI Agent can

- Summarize backtest results
- Explain trade log entries
- Draft research notes
- Compare strategies in plain language
- Explain model metrics
- Summarize external text provided by the user (news, filings, notes) — later

### AI Agent cannot

- Place trades
- Guarantee future returns
- Give personalized financial advice
- Access broker accounts
- Modify saved experiments without explicit user action

All AI output must be labeled as research assistance, not financial advice.

---

## Future backend module layout

```
backend/app/
  api/routes/
    data_sources.py
    market.py
    backtest.py
    comparison.py
    robustness.py
    experiments.py
    model_lab.py
    ai_agent.py

  data_providers/
    base.py
    yahoo_provider.py
    akshare_provider.py
    tushare_provider.py
    csv_provider.py

  cache/
    cache_client.py
    keys.py
    ttl.py

  db/
    client.py
    repositories/
      watchlists.py
      signal_snapshots.py
      backtest_runs.py
      model_runs.py
      research_notes.py

  strategies/
    ma_crossover.py
    momentum.py
    combined_signal.py

  model_lab/
    dataset_builder.py
    feature_builder.py
    train.py
    evaluate.py
    backtest_signal.py

  ai_agent/
    prompts.py
    tools.py
    summarizer.py
    research_note_writer.py
```

Current v1 backend remains consolidated in existing modules; restructuring follows frontend route migration.

---

## Frontend layout

```
frontend/
  app/
    page.tsx                  # Overview
    data-center/page.tsx
    market-watch/page.tsx
    strategy-lab/page.tsx
    comparison/page.tsx
    robustness/page.tsx
    model-lab/page.tsx
    experiments/page.tsx
    research-notes/page.tsx
    ai-agent/page.tsx
  components/
    layout/
      AppShell.tsx
      TopNav.tsx
      PageHero.tsx
      LanguageToggle.tsx
    legacy/
      LegacyDashboard.tsx     # Migration backup, not rendered by default
    workspace/
      ModuleSkeletonPage.tsx
  lib/
    workspaceModules.ts
    useWorkspaceLanguage.ts
```

---

## Deployment

- **Frontend:** Vercel (Next.js App Router)
- **Backend:** Render (FastAPI)
- **Future database:** Supabase / Postgres
- **Future cache:** Redis / Upstash or equivalent

---

## Migration notes

1. Route skeletons and layout shell are in place.
2. Business logic remains in `LegacyDashboard.tsx` as a backup.
3. Next step: migrate Market Watch, Strategy Lab, Comparison, and Robustness sections into their route modules one at a time.
4. Backend API splitting can proceed in parallel once frontend boundaries are stable.
