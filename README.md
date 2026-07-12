# AI Quant Signal Platform

A full-stack quant research dashboard for signal scoring, strategy backtesting, benchmark comparison, and robustness checks. Built as a **portfolio and research demonstration** project — not a trading bot.

> **Disclaimer**
>
> For **portfolio and research demonstration** only. **Not financial advice.** **Not for live trading.** No broker integration. Uses **daily historical OHLCV** with **auto failover** across free providers (AKShare → Yahoo/`yfinance` → Stooq).

---

## What It Does

Enter stock or ETF tickers, rank rule-based signals, inspect indicators and charts, then run simulated backtests in the **Strategy Lab**:

**Data → Signals → Backtest → Robustness**

| Stage | What you get |
|-------|----------------|
| Market Watch | Multi-ticker signal ranking (0–100 score, labels, risk bucket) |
| Charts | Single-ticker indicators or normalized multi-ticker comparison |
| Strategy Lab | MA crossover, momentum, or combined signal backtests |
| Trade Log | Collapsible BUY/SELL event table with reasons |
| Robustness | MA parameter sensitivity + out-of-sample validation |

The UI supports **English** and **Simplified Chinese**.

---

## Strategy Lab

Three backtest methods share the same metrics, charts, and trade log format. All positions are **lagged by one day** to avoid look-ahead bias; **transaction costs** apply on position changes.

### MA Crossover

- Hold when short moving average > long moving average
- Default windows: 20 / 60

### Momentum

- Hold when past N-day return is positive
- Default window: 60 days

### Combined Signal

Uses both MA crossover and momentum:

| Mode | Rule |
|------|------|
| **Conservative** | Hold only when **both** MA and momentum are positive |
| **Aggressive** | Hold when **either** MA or momentum is positive |

Default combined mode: **conservative**

Parameter sensitivity and out-of-sample validation remain **MA crossover only** in the current version.

---

## Key Features

- Multi-ticker market watch and signal ranking
- Transparent signal components (trend, momentum, RSI, volatility)
- Normalized price comparison chart with Recharts Brush zoom
- Strategy Lab: MA crossover, momentum, combined signal (conservative / aggressive)
- Strategy vs buy-and-hold cumulative return chart with BUY/SELL markers
- Strategy and benchmark drawdown comparison
- Collapsible trade log with trade date, action, price, and reason
- Rule-based backtest interpretation (bilingual)
- MA parameter sensitivity analysis
- Out-of-sample (in-sample vs out-of-sample) validation
- FastAPI + pytest backend tests

---

## Architecture

```
Next.js Frontend
       ↓
FastAPI Backend
       ↓
MarketDataService (data_source=auto|akshare|yahoo|stooq)
       ↓
auto failover: AkshareProvider → YahooProvider → StooqProvider
       ↓
pandas (indicators, signals, backtests)
       ↓
JSON API → Recharts visualization
```

| Layer | Role |
|-------|------|
| **Next.js** | Dashboard UI, forms, i18n, charts |
| **FastAPI** | REST API, Pydantic validation |
| **pandas** | Feature engineering and backtest engine |
| **Recharts** | Price, comparison, return, and drawdown charts |

---

## Data Source

| Item | Detail |
|------|--------|
| Default mode | `auto` failover: **AKShare → Yahoo → Stooq** |
| Manual lock | `data_source=akshare\|yahoo\|stooq` (API + Data Center preference) |
| Abstraction | `MarketDataService` routes all price history requests |
| Status API | `GET /api/data-sources/status` |
| Database status | `GET /api/database/status` |
| Frequency | Daily OHLCV |
| Use case | Research and portfolio demonstration |
| Not suitable for | Live execution or institutional-grade market data |

Local note: install backend deps with `pip install -r requirements.txt` (includes `akshare`). If `akshare` is missing in the active Python env, auto mode skips it and continues to Yahoo/Stooq.

---

## Run Locally

### Prerequisites

- Python 3.9+
- Node.js 18+

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Database setup (optional — Database Preparation v1)

Supabase Postgres stores **durable research assets** (saved backtest runs and trades in a future step). Raw OHLCV is not stored in v1. Cache is postponed.

1. Create a Supabase project.
2. In **Connect**, copy the **Transaction Pooler** URI (not the direct connection if using pooler mode).
3. Set locally in `backend/.env`:
   ```bash
   SUPABASE_DB_URL=postgresql://...
   ```
4. On Render, add `SUPABASE_DB_URL` under **Environment**.
5. In Supabase **SQL Editor**, paste and run `backend/db/schema.sql`.
6. Verify:
   ```bash
   curl http://localhost:8000/api/database/status
   ```

The app starts normally without `SUPABASE_DB_URL`; the status endpoint reports `configured: false`.

**Tip:** If the dev server shows a missing chunk error, stop dev and run `npm run dev:clean` (clears `.next` cache). Do not run `npm run build` while `npm run dev` is active.

---

## Deploy

| Component | Platform |
|-----------|----------|
| Frontend | Vercel |
| Backend | Render (`render.yaml` included) |

**Active Render backend:** `https://ai-quant-signal-platform.onrender.com`

### Backend (Render)

| Setting | Value |
|---------|-------|
| Root Directory | `backend` |
| Build | `pip install -r requirements.txt` |
| Start | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health check | `/health` |

Set `ALLOWED_ORIGINS` to your frontend URL(s), e.g. `https://your-app.vercel.app`.

Optionally set `SUPABASE_DB_URL` (Transaction Pooler URI) for database connectivity and Experiments persistence.

### Frontend (Vercel)

| Setting | Value |
|---------|-------|
| Root Directory | `frontend` |
| Framework | Next.js |

Recommended `NEXT_PUBLIC_API_BASE_URL` (no trailing slash):

```
https://ai-quant-signal-platform.onrender.com
```

Local development uses `http://localhost:8000` via `frontend/.env.local` (see `frontend/.env.example`). Production builds fall back to the Render URL above if the env var is unset.

### Canonical production endpoints

```bash
curl https://ai-quant-signal-platform.onrender.com/health
curl https://ai-quant-signal-platform.onrender.com/api/data-sources/status
curl https://ai-quant-signal-platform.onrender.com/api/database/status
```

### Checklist

- [ ] `GET https://ai-quant-signal-platform.onrender.com/health` returns `{"status":"ok",...}`
- [ ] `GET https://ai-quant-signal-platform.onrender.com/api/data-sources/status` returns `active_provider: yahoo`
- [ ] `GET https://ai-quant-signal-platform.onrender.com/api/database/status` returns expected `configured` / `connected` state
- [ ] `ALLOWED_ORIGINS` includes the Vercel URL
- [ ] Market Watch and Strategy Lab work from the deployed UI

---

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/health` | Health check |
| `GET` | `/api/data-sources/status` | Active and planned data provider status |
| `GET` | `/api/database/status` | Supabase Postgres config and connectivity |
| `GET` | `/api/price/{ticker}` | Daily price history |
| `GET` | `/api/indicators/{ticker}` | Price + technical indicators |
| `GET` | `/api/signal/{ticker}` | Latest signal score and components |
| `POST` | `/api/market-watch` | Multi-ticker signal ranking |
| `POST` | `/api/chart/compare` | Normalized multi-ticker series |
| `POST` | `/api/backtest` | Backtest (`ma_crossover`, `momentum`, `combined_signal`) |
| `POST` | `/api/backtest/sensitivity` | MA parameter sensitivity |
| `POST` | `/api/backtest/oos` | Out-of-sample validation |
| `POST` | `/api/experiments/backtest-runs` | Save backtest run + trade log |
| `GET` | `/api/experiments/backtest-runs` | List saved experiments |
| `GET` | `/api/experiments/backtest-runs/{id}` | Experiment detail + trades |
| `DELETE` | `/api/experiments/backtest-runs/{id}` | Delete saved experiment |

### Backtest request (example)

```json
{
  "ticker": "AAPL",
  "start_date": "2022-01-01",
  "strategy": "combined_signal",
  "short_window": 20,
  "long_window": 60,
  "momentum_window": 60,
  "combined_mode": "conservative",
  "transaction_cost": 0.001
}
```

Response includes `metrics`, `data`, `trade_log`, `parameters`, and `strategy_config`.

---

## Testing

```bash
cd backend
source .venv/bin/activate
python -m pytest tests -v
```

Coverage includes MA / momentum / combined backtests, trade log, sensitivity, and out-of-sample endpoints.

```bash
cd frontend
npm run build:clean
```

---

## Project Structure

```
ai-quant-signal-platform/
├── frontend/          # Next.js dashboard
├── backend/
│   ├── app/
│   │   ├── backtest/  # engine, metrics, OOS
│   │   ├── db/        # Supabase Postgres client (v1)
│   │   ├── recommendation/
│   │   └── main.py
│   ├── db/
│   │   └── schema.sql # backtest_runs, backtest_trades
│   └── tests/
├── render.yaml
└── README.md
```

---

## Limitations

- Daily historical data only; no intraday timestamps in trade log
- Free providers may be delayed, rate-limited, or blocked on some networks (Yahoo unstable in China; Stooq may hit bot checks)
- Simplified backtest assumptions (no slippage model beyond flat transaction cost)
- No broker, live trading, or authentication
- Database persistence stores saved backtest runs and trade logs (Experiments v1); raw OHLCV is not stored
- No machine learning in the current version

---

## Roadmap

**Done**

- Market data, indicators, signal scoring, bilingual UI
- Multi-source market data with `auto` failover (AKShare / Yahoo / Stooq) and manual lock
- Strategy Lab (MA, momentum, combined signal)
- Trade log, benchmark comparison, drawdown charts
- Parameter sensitivity, out-of-sample validation
- Experiments Persistence v1 (save / list / detail / delete)
- Paper trading + five-level risk engine (in-memory account)

**Next (decision-platform direction — not more indicator widgets)**

1. **Data trust layer** — show hit source, failover trail, freshness, missing bars, adjustment mode
2. **Rigorous research** — walk-forward, parameter stability, regime tests (beyond current OOS/sensitivity)
3. **Decision explanation** — why signal fired, supporting/opposing evidence, invalidation conditions
4. **Portfolio & risk** — position sizing, correlation, risk budget, drawdown limits
5. **Simulated execution** — slippage, fees, order state, strategy drift monitoring
6. **AI research assistant** — explain/compare/summarize experiments; do not invent trade signals

**Later**

- CoinGecko / CSV upload / Tushare providers
- Durable paper-account persistence
- Model Lab (ML)
- Additional rule-based strategies (RSI, MACD, breakout)
- Portfolio-level backtest (top-N, rebalance)
- Compare across saved experiments; watchlist persistence
- ML ranking layer (with proper time-series validation)

---

## License & Use

Open for viewing and learning from the implementation. If you fork or reference this project, keep the disclaimer visible and do not present backtest results as investment advice.

---

## Disclaimer

Portfolio and research demonstration only. Not financial advice. Not for live trading.
