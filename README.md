# AI Quant Signal Platform

A full-stack quant research dashboard for signal scoring, strategy backtesting, benchmark comparison, and robustness checks. Built as a **portfolio and research demonstration** project — not a trading bot.

> **Disclaimer**
>
> For **portfolio and research demonstration** only. **Not financial advice.** **Not for live trading.** No broker integration. Uses **daily historical market data** from Yahoo Finance via `yfinance`.

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
yfinance (Yahoo Finance daily OHLCV)
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
| Provider | Yahoo Finance via `yfinance` |
| Frequency | Daily OHLCV |
| Use case | Research and portfolio demonstration |
| Not suitable for | Live execution or institutional-grade market data |

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

**Tip:** If the dev server shows a missing chunk error, stop dev and run `npm run dev:clean` (clears `.next` cache). Do not run `npm run build` while `npm run dev` is active.

---

## Deploy

| Component | Platform |
|-----------|----------|
| Frontend | Vercel |
| Backend | Render (`render.yaml` included) |

### Backend (Render)

| Setting | Value |
|---------|-------|
| Root Directory | `backend` |
| Build | `pip install -r requirements.txt` |
| Start | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health check | `/health` |

Set `ALLOWED_ORIGINS` to your frontend URL(s), e.g. `https://your-app.vercel.app`.

### Frontend (Vercel)

| Setting | Value |
|---------|-------|
| Root Directory | `frontend` |
| Framework | Next.js |

Set `NEXT_PUBLIC_API_BASE_URL` to your Render backend URL (no trailing slash).

### Checklist

- [ ] `GET /health` returns `{"status":"ok",...}`
- [ ] `ALLOWED_ORIGINS` includes the Vercel URL
- [ ] Market Watch and Strategy Lab work from the deployed UI

---

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/health` | Health check |
| `GET` | `/api/price/{ticker}` | Daily price history |
| `GET` | `/api/indicators/{ticker}` | Price + technical indicators |
| `GET` | `/api/signal/{ticker}` | Latest signal score and components |
| `POST` | `/api/market-watch` | Multi-ticker signal ranking |
| `POST` | `/api/chart/compare` | Normalized multi-ticker series |
| `POST` | `/api/backtest` | Backtest (`ma_crossover`, `momentum`, `combined_signal`) |
| `POST` | `/api/backtest/sensitivity` | MA parameter sensitivity |
| `POST` | `/api/backtest/oos` | Out-of-sample validation |

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
│   │   ├── recommendation/
│   │   └── main.py
│   └── tests/
├── render.yaml
└── README.md
```

---

## Limitations

- Daily historical data only; no intraday timestamps in trade log
- `yfinance` data may be delayed or incomplete for some symbols
- Simplified backtest assumptions (no slippage model beyond flat transaction cost)
- No broker, live trading, authentication, or database persistence
- No machine learning in the current version

---

## Roadmap

**Done**

- Market data, indicators, signal scoring, bilingual UI
- Strategy Lab (MA, momentum, combined signal)
- Trade log, benchmark comparison, drawdown charts
- Parameter sensitivity, out-of-sample validation

**Planned**

- Additional rule-based strategies (RSI, MACD, breakout)
- Portfolio-level backtest (top-N, rebalance)
- Optional persistence (saved watchlists / runs)
- ML ranking layer (with proper time-series validation)

---

## License & Use

Open for viewing and learning from the implementation. If you fork or reference this project, keep the disclaimer visible and do not present backtest results as investment advice.

---

## Disclaimer

Portfolio and research demonstration only. Not financial advice. Not for live trading.
