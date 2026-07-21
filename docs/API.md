# API

Documents **currently implemented** HTTP endpoints in the `backend/` FastAPI app.  
Future or Architecture-Bible-only APIs are omitted.

Base URL (local): `http://127.0.0.1:8000`  
OpenAPI: `http://127.0.0.1:8000/docs` when the server is running.

---

## Health and infrastructure

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Process liveness |
| `GET` | `/api/data-sources/status` | Configured data-source status (not a live ping of every provider) |
| `GET` | `/api/database/status` | Postgres connectivity when `SUPABASE_DB_URL` is set |

---

## Research spine (v1)

Prefix: `/api/v1/research`

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/research/execution` | Historical MA crossover execution + benchmark metrics |
| `POST` | `/api/v1/research/validation` | Deterministic validation evidence |
| `POST` | `/api/v1/research/evaluation` | Summarise validation evidence (no new calculations) |
| `POST` | `/api/v1/research/copilot/query` | Evidence-grounded Copilot Q&A |

Rules:

- Provider failures return error statuses; they do not invent metrics
- Evaluation requires a prior validation run id in the request contract used by the workspace
- Copilot requires backend `LLM_*` configuration; without it the route fails honestly

---

## Experiments (saved backtest runs)

Prefix: `/api/experiments`

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/experiments/backtest-runs` | Persist a backtest run record |
| `GET` | `/api/experiments/backtest-runs` | List saved runs |
| `GET` | `/api/experiments/backtest-runs/{run_id}` | Fetch one run |

Availability depends on database configuration.

---

## Paper trading (legacy API surface)

Prefix: `/api/paper`

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/paper/account` | Paper account state |
| `POST` | `/api/paper/dashboard` | Paper dashboard payload |
| `POST` | `/api/paper/execute` | Execute a paper action |
| `POST` | `/api/paper/reset` | Reset paper account |

The Research Workspace Paper Trading center is observation staging UI; it must not fabricate session data when no real session exists.

---

## Market / strategy lab routes (legacy demo)

Defined primarily in `backend/app/main.py`:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/price/{ticker}` | Price series |
| `GET` | `/api/indicators/{ticker}` | Indicators |
| `GET` | `/api/signal/{ticker}` | Signal payload |
| `POST` | `/api/market-watch` | Market watch ranking |
| `POST` | `/api/chart/compare` | Chart comparison |
| `POST` | `/api/backtest` | Strategy lab backtest |
| `POST` | `/api/backtest/compare-strategies` | Multi-strategy compare |
| `POST` | `/api/backtest/sensitivity` | Sensitivity analysis |
| `POST` | `/api/backtest/oos` | Out-of-sample check |

---

## Error behaviour (research routes)

| Situation | Typical response |
| --- | --- |
| Invalid parameters | `400` |
| Upstream market-data / provider failure | `502` (no fabricated series) |
| Copilot provider / config unavailable | `503` / structured error — no fake answer |

For request/response schemas, use the live OpenAPI docs or the Pydantic models under `backend/app/research_*/schemas.py`.
