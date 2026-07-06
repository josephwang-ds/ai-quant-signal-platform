# AI Quant Signal Platform

A learning-stage full-stack quant research dashboard for signal scoring, backtesting, benchmark comparison, and robustness checks.

> **Important disclaimer**
>
> This project is for **educational, portfolio, and research demonstration purposes only**.
> It is **not financial advice**.
> It is **not designed for live trading**.
> It does **not** connect to a broker.
> It uses **daily historical market data**.

---

## Overview

This platform lets users enter stock/ETF tickers, calculate technical indicators, rank current signals, run strategy backtests, compare strategy performance against a buy-and-hold benchmark, inspect drawdowns, run parameter sensitivity analysis, perform out-of-sample validation, and switch the UI between English and Simplified Chinese.

The goal is to show a realistic quant research workflow in a readable, interview-friendly demo: data ingestion → feature engineering → signal ranking → backtesting → benchmark comparison → robustness checks.

---

## Why I Built This

Quant research is often explained as a black box. I built this project to demonstrate, end to end, how a learning-stage research platform can:

- Pull market data from a public source
- Engineer technical features in Python
- Convert rules into a transparent signal score
- Backtest simple strategies with realistic constraints such as lagged positions and transaction costs
- Compare strategy results against a benchmark instead of looking at absolute returns alone
- Stress-test claims with sensitivity analysis and out-of-sample validation

This is intentionally scoped as a **research and portfolio demo**, not a production trading system.

---

## Key Features

- **Multi-ticker market watch** — scan several tickers in one request
- **Signal score and watchlist labels** — rule-based 0–100 score with readable labels
- **Technical indicators** — MA20, MA60, RSI, returns, volatility, volume change
- **Ticker detail and signal components** — explain why a ticker received its label
- **Normalized price comparison chart** — compare multiple tickers on a common base
- **Recharts Brush zoom** — zoom and pan across date ranges
- **MA crossover backtest** — classic short/long moving average rule
- **Momentum backtest** — hold when past N-day return is positive
- **Strategy vs buy-and-hold benchmark** — cumulative return comparison
- **Strategy and benchmark drawdown comparison** — downside risk view
- **Backtest interpretation panel** — rule-based educational summary
- **Parameter sensitivity analysis** — compare fixed parameter pairs for robustness
- **Out-of-sample validation** — split in-sample vs out-of-sample performance
- **English / Chinese UI toggle** — bilingual dashboard labels and interpretation
- **FastAPI backend tests with pytest** — endpoint validation for sensitivity and OOS flows

---

## Architecture

```
Next.js Frontend
  ↓
FastAPI Backend
  ↓
yfinance / Yahoo Finance daily OHLCV data
  ↓
pandas feature engineering and backtesting
  ↓
JSON API response
  ↓
Recharts visualization
```

**How the pieces fit together**

- **Next.js** handles UI, forms, tables, charts, bilingual labels, and interpretation panels.
- **FastAPI** exposes REST endpoints for market data, signals, charts, and backtests.
- **Pydantic** validates request parameters such as ticker, date range, windows, and transaction cost.
- **yfinance** retrieves historical daily market data from Yahoo Finance.
- **pandas** calculates indicators, signals, returns, drawdowns, and backtest metrics.
- **Recharts** visualizes price, normalized comparison, strategy return, benchmark return, and drawdown.

---

## Data Source

| Item | Detail |
|------|--------|
| Source | Yahoo Finance via `yfinance` |
| Data type | Daily OHLCV |
| Used fields | `date`, `open`, `high`, `low`, `close`, `volume` |
| Derived metrics | Calculated in Python (MA, RSI, returns, volatility, signal score, backtest metrics) |
| Intended use | Education, demo, and research |
| Not suitable for | Execution-grade live trading or institutional market data requirements |

---

## Current Strategies

### MA Crossover

- If short MA > long MA, hold the asset
- Otherwise stay in cash
- Position is shifted by one period to avoid look-ahead bias
- Transaction cost is applied when the position changes

### Momentum

- If past N-day return > 0, hold the asset
- Otherwise stay in cash
- Position is shifted by one period to avoid look-ahead bias
- Transaction cost is applied when the position changes

---

## Metrics Explained

| Metric | Meaning |
|--------|---------|
| **Daily Return** | One-day percentage price change |
| **20D Return** | Price change over roughly one trading month |
| **60D Return** | Price change over roughly one trading quarter |
| **MA20 / MA60** | 20-day and 60-day moving averages |
| **RSI** | Relative Strength Index; momentum/overbought-oversold gauge |
| **Volatility** | Recent price fluctuation, often annualized from rolling windows |
| **Signal Score** | Rule-based 0–100 score from trend, momentum, RSI, and volatility checks |
| **Total Return** | Strategy cumulative return over the selected period |
| **Benchmark Return** | Buy-and-hold return for the same ticker and period |
| **CAGR** | Compound annual growth rate |
| **Sharpe Ratio** | Return per unit of volatility; higher is generally better |
| **Max Drawdown** | Largest peak-to-trough decline |
| **Win Rate** | Share of positive return periods |
| **Number of Trades** | Count of position changes |
| **Transaction Cost Total** | Total simulated cost drag from trading |
| **Parameter Sensitivity** | Compare multiple fixed parameter pairs to test robustness |
| **Out-of-Sample Validation** | Split history into research and test periods to check generalization |

---

## How to Run Locally

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
cp .env.example .env
python3 -m uvicorn app.main:app --reload --reload-dir app --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

### Open

- Frontend dashboard: [http://localhost:3000](http://localhost:3000)
- FastAPI docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Deployment

Target stack:

- **Frontend**: Vercel
- **Backend**: Render
- **Database (future)**: Supabase Postgres
- **DNS**: Cloudflare

### 1. Deploy Backend on Render

Option A — use the included Blueprint:

- Connect the GitHub repo to Render
- Render reads `render.yaml` at the repo root
- Service root directory: `backend`

Option B — manual Web Service:

| Setting | Value |
|---------|-------|
| Root Directory | `backend` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health` |

Environment variables on Render:

| Variable | Example |
|----------|---------|
| `ALLOWED_ORIGINS` | `https://your-app.vercel.app,https://www.your-domain.com` |
| `PYTHON_VERSION` | `3.11.9` |

After deploy, verify:

```bash
curl https://your-backend.onrender.com/health
```

Expected:

```json
{"status":"ok","service":"ai-quant-signal-backend"}
```

### 2. Deploy Frontend on Vercel

| Setting | Value |
|---------|-------|
| Root Directory | `frontend` |
| Framework Preset | Next.js |
| Build Command | `npm run build` |
| Output | default |

Environment variables on Vercel:

| Variable | Example |
|----------|---------|
| `NEXT_PUBLIC_API_BASE_URL` | `https://your-backend.onrender.com` |

Notes:

- Do **not** include a trailing slash in `NEXT_PUBLIC_API_BASE_URL`
- In production, the frontend requires this variable; localhost fallback is development-only
- Redeploy after changing environment variables so Next.js inlines the public value at build time

### 3. Cloudflare DNS

Typical setup:

- `www.your-domain.com` → CNAME to Vercel
- `api.your-domain.com` → CNAME to Render backend (optional custom domain)

Then update:

- Vercel custom domain
- Render custom domain
- `ALLOWED_ORIGINS` to include your final frontend URL(s)

### 4. Future: Supabase Postgres

Not required for the current demo. When added later:

- Store user settings, saved watchlists, or backtest runs in Supabase
- Keep market data retrieval in the FastAPI service unless you migrate to a managed data pipeline

### Deployment Checklist

- [ ] Render backend `/health` returns `ok`
- [ ] `ALLOWED_ORIGINS` includes the Vercel URL
- [ ] Vercel `NEXT_PUBLIC_API_BASE_URL` points to Render backend
- [ ] Frontend loads and **Check Backend** succeeds
- [ ] Market Watch and Backtesting work from the deployed UI
- [ ] No secrets committed to git (only `.env.example` templates)

---

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/health` | Backend health check |
| `GET` | `/api/price/{ticker}` | Raw daily price history |
| `GET` | `/api/indicators/{ticker}` | Price plus engineered indicators |
| `GET` | `/api/signal/{ticker}` | Latest signal score and components |
| `POST` | `/api/market-watch` | Multi-ticker signal ranking |
| `POST` | `/api/chart/compare` | Normalized multi-ticker comparison series |
| `POST` | `/api/backtest` | MA crossover or momentum backtest |
| `POST` | `/api/backtest/sensitivity` | Parameter sensitivity analysis |
| `POST` | `/api/backtest/oos` | Out-of-sample validation |

---

## Frontend Screens

1. **Header & Demo Overview** — product narrative, bilingual toggle, disclaimer
2. **Backend Health** — verify API availability
3. **Market Watch** — enter tickers and run signal ranking
4. **Data Freshness** — source, lookback window, latest available date
5. **Signal Ranking** — sortable-style table of scores, labels, trend, and risk
6. **Ticker Detail** — metrics, signal components, and reasons
7. **Chart Settings** — date range, selected vs compare mode, Brush zoom charts
8. **Backtesting** — strategy form, metric cards, interpretation, return/drawdown charts
9. **Parameter Sensitivity** — compare fixed MA parameter pairs
10. **Out-of-Sample Validation** — full / in-sample / out-of-sample segment comparison

---

## Testing

```bash
cd backend
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest tests -v
```

Current backend tests include:

- **Sensitivity endpoint tests** — default parameter sets, custom parameter sets, invalid windows, and max parameter set validation
- **Out-of-sample endpoint tests** — valid segment response, invalid split date, invalid end date
- **Momentum backtest tests** — momentum strategy path and validation

---

## Limitations

- Uses **daily historical data only**
- `yfinance` is suitable for demo/research, not institutional-grade execution data
- **No broker integration**
- **No live trading**
- **No order execution**
- **No portfolio-level position sizing yet**
- Backtests are **simplified and educational**
- Strategy results should **not** be interpreted as investment advice

---

## Roadmap

### V1 Completed

- Market data API
- Technical indicators
- Signal score
- Watchlist ranking
- Frontend dashboard

### V2 Completed / In Progress

- Backtesting
- Benchmark comparison
- Drawdown
- Transaction cost
- Parameter sensitivity
- OOS validation
- Bilingual UI

### V3 Planned

More strategy library:

- RSI mean reversion
- Bollinger Bands
- MACD
- Breakout

### V4 Planned

Portfolio backtest:

- Top-N ranking
- Rebalance
- Portfolio metrics
- SPY benchmark

### V5 Planned

ML ranking:

- Logistic Regression baseline
- XGBoost / LightGBM
- TimeSeriesSplit
- SHAP feature explanation

### V6 Planned

LLM research assistant:

- Explain signal
- Summarize risk
- Warn about overfitting
- Suggest next experiments

### V7 Private-only Future

Paper trading sandbox:

- Risk checks
- Position sizing
- Trade journal
- Simulated P&L
- No real broker execution at first

---

## Interview Talking Points

- **End-to-end quant workflow**: I can walk from raw daily OHLCV data to ranked signals, backtests, and robustness checks in one demo.
- **Look-ahead bias awareness**: Strategy positions are lagged by one period so the backtest does not accidentally use future information.
- **Benchmark-first thinking**: Strategy performance is always compared against buy-and-hold, not shown in isolation.
- **Drawdown matters**: Return alone is not enough; I also compare strategy and benchmark drawdowns.
- **Robustness over curve fitting**: Parameter sensitivity and out-of-sample validation help avoid overclaiming from one lucky parameter set.
- **Transparent rules before ML**: The signal score and backtest rules are explainable, which makes the project easier to discuss in interviews.
- **Clear scope boundaries**: This is a research demo with no broker integration, no live trading, and no ML yet — by design.
- **Full-stack implementation**: Next.js frontend, FastAPI backend, pandas analytics, Recharts visualization, and pytest coverage.

---

## Project Structure

```
ai-quant-signal-platform/
├── frontend/          # Next.js dashboard (UI, charts, i18n)
├── backend/           # FastAPI service (data, signals, backtests)
│   ├── app/
│   └── tests/
└── README.md
```

---

## Disclaimer

For educational and portfolio demonstration purposes only. Not financial advice. Not for live trading.
