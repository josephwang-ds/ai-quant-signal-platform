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
| `GET` | `/api/database/status` | Postgres connectivity + `persistence_mode` when optional DB is used |

---

## Research spine (v1)

Prefix: `/api/v1/research`

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/research/execution` | Historical MA crossover execution + benchmark metrics |
| `POST` | `/api/v1/research/validation` | Deterministic validation evidence (includes fixed-parameter chronological walk-forward for the canonical trend study) |
| `POST` | `/api/v1/research/evaluation` | Summarise validation evidence (no new calculations) |
| `GET` | `/api/v1/research/persistence/mode` | Browser-local / persisted / unavailable mode label |
| `PUT` | `/api/v1/research/persistence/projects` | Optional durable research project upsert |
| `POST` | `/api/v1/research/persistence/protocol-versions` | Publish immutable protocol version |
| `POST` | `/api/v1/research/persistence/evidence-snapshots` | Persist evidence snapshot + hash |
| `POST` | `/api/v1/research/persistence/validation-runs` | Persist validation run (idempotency key supported) |
| `POST` | `/api/v1/research/persistence/agent-runs` | Persist agent run + ordered events |
| `POST` | `/api/v1/research/persistence/decision-records` | Persist human decision record |
| `GET` | `/api/v1/research/persistence/decision-records` | List decision records for a research id |
| `POST` | `/api/v1/research/copilot/query` | Evidence-grounded Copilot Q&A |
| `POST` | `/api/v1/research/guidance/definition` | Template-first research definition; optional constrained LLM refinement |
| `POST` | `/api/v1/research/reviewer/draft-definition` | Strict-JSON AI research-definition draft; criteria remain inactive |
| `POST` | `/api/v1/research/reviewer/review-hypothesis` | Testability and falsifiability review |
| `POST` | `/api/v1/research/reviewer/review-evidence` | Interpretation of a supplied deterministic evidence snapshot |
| `POST` | `/api/v1/research/reviewer/identify-missing-steps` | Research-completion gap review |
| `POST` | `/api/v1/research/agent/runs` | Start a bounded Governance Agent review |
| `GET` | `/api/v1/research/agent/runs/{agent_run_id}` | Read run state, evidence gaps, trace, and pending approval |
| `POST` | `/api/v1/research/agent/runs/{agent_run_id}/resume` | Approve/skip tools or record a human decision |
| `POST` | `/api/v1/research/agent/runs/{agent_run_id}/cancel` | Cancel a non-terminal Agent run |

Rules:

- Provider failures return error statuses; they do not invent metrics
- Evaluation requires a prior validation run id in the request contract used by the workspace
- Definition guidance with `use_llm=false` requires no provider and returns an editable deterministic template
- Definition guidance with `use_llm=true` and Copilot require backend `LLM_*` configuration; without it the route fails honestly
- Reviewer endpoints reuse the same backend provider adapter as Copilot, return
  provider/model/timestamp metadata, and never calculate or persist evidence
- Agent tool plans, completeness, and Promote/Hold/Reject suggestions are
  deterministic; DeepSeek only explains validated structured context
- Agent execution tools require approval and call the existing execution or
  validation services with the workspace's saved run configuration

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
| Invalid parameters | `400` / `422` |
| Request body too large | `413` |
| Demo rate limit exceeded | `429` with `Retry-After` (friendly message; no limiter internals) |
| Upstream market-data / provider failure | `502` (no fabricated series) |
| Copilot provider / config unavailable, or LLM concurrency full | `503` / structured error — no fake answer |
| LLM or long validation timeout | `504` |

Public-demo protection knobs (`AGENT_RATE_LIMIT`, `LLM_MAX_CONCURRENCY`, `MAX_REQUEST_BODY_BYTES`, timeouts, `TRUSTED_PROXY_IPS`) are documented in [`backend/.env.example`](../backend/.env.example). The in-memory rate limiter is single-instance only.

For request/response schemas, use the live OpenAPI docs or the Pydantic models under `backend/app/research_*/schemas.py`.
