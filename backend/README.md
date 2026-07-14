# AI Quant Signal Backend

FastAPI service for the AI Quant Signal Platform demo.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

`requirements.txt` includes `akshare` for the default auto failover chain. If it is missing from the active env, `/api/data-sources/status` reports akshare as degraded and auto skips it.

Copy environment template:

```bash
cp .env.example .env
```

## Run (local development)

```bash
uvicorn app.main:app --reload --reload-dir app --port 8000
```

## Run (production-style, no reload)

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

On Render, use:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Production URL:** `https://ai-quant-signal-platform.onrender.com`

```bash
curl https://ai-quant-signal-platform.onrender.com/health
curl https://ai-quant-signal-platform.onrender.com/api/database/status
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ALLOWED_ORIGINS` | Production | Comma-separated frontend URLs for CORS |
| `PORT` | Render | Injected by Render; optional locally |

## Health Check

`GET /health`

```json
{"status": "ok", "service": "ai-quant-signal-backend"}
```

## Tests

```bash
source .venv/bin/activate
# Default CI: excludes live network smoke tests
PYTHONPATH=. python -m pytest tests -v

# Research execution fixture suite only
PYTHONPATH=. python -m pytest tests/test_research_execution.py -v

# Research validation fixture suite only
PYTHONPATH=. python -m pytest tests/test_research_validation.py -v

# Research evaluation fixture suite only
PYTHONPATH=. python -m pytest tests/test_research_evaluation.py -v

# Optional live Yahoo smoke
PYTHONPATH=. python -m pytest tests/test_research_execution_live.py -v -m live
```

Research execution docs: `docs/slices/research-execution.md`.
Endpoint: `POST /api/v1/research/execution`.

Research validation docs: `docs/slices/research-validation.md`.
Endpoint: `POST /api/v1/research/validation`. Saves its result to an
in-memory `ValidationResultStore` and returns a `validation_run_id` in the
response.

Research evaluation docs: `docs/slices/research-evaluation.md`.
Endpoint: `POST /api/v1/research/evaluation`. Requires a `validation_run_id`
from a prior validation call; summarizes that stored evidence only. It
performs no calculations of its own, no market-data reads, and never calls
`ResearchValidationService` — its only dependency is `ValidationResultStore`.

`ValidationResultStore` is in-memory (MVP scope): saved results are lost on
backend restart, and persistent `ValidationRun` storage remains future work.
