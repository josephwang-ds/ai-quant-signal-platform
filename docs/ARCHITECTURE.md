# AI Quant Research Workspace — Architecture

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

This document describes the intended architecture. Database, cache, ML, and LLM implementations are planned but not yet built in v1.

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

Planned providers under `backend/app/data_providers/`:

| Provider | Market | Status |
|----------|--------|--------|
| `yahoo_provider.py` | US / global via Yahoo | **Current** |
| `akshare_provider.py` | China A-share | Planned |
| `tushare_provider.py` | China markets | Planned |
| `csv_provider.py` | User upload | Planned |
| Paid APIs | As needed | Future |

All providers implement a common interface in `base.py`:

- Symbol metadata resolution
- Historical OHLCV fetch with adjustment mode
- Provider health / freshness reporting

The **Data Center** frontend module will surface provider selection, market type (US / HK / CN), adjustment mode, and data quality checks.

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

API routes (planned): `backend/app/api/routes/experiments.py`

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
