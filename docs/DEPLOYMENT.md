# Deployment

## Topology

```text
Browser → Vercel (Next.js) → Render (FastAPI) → Market data providers
                              ↓
                         Supabase Postgres (optional durable stores)
                              ↓
                         LLM provider (Copilot only, backend secrets)
```

Operator evidence notes: [`deployment/`](deployment/), [`reviews/DEPLOYED-E2E-VERIFICATION.md`](reviews/DEPLOYED-E2E-VERIFICATION.md).

---

## Local development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Open `http://localhost:3000`. With `NEXT_PUBLIC_API_BASE_URL` unset, the frontend targets `http://127.0.0.1:8000`.

---

## Vercel (frontend)

1. Import the repository; set the project root to `frontend/` (or configure as required by the monorepo settings).
2. Set `NEXT_PUBLIC_API_BASE_URL` to the absolute Render backend URL (`https://…`).
3. Deploy. Do **not** put LLM keys in Vercel `NEXT_PUBLIC_*` variables.

Production fails closed if `NEXT_PUBLIC_API_BASE_URL` is missing or invalid.

---

## Render (backend)

1. Deploy from `backend/` using `render.yaml` or an equivalent web service.
2. Set environment variables (below).
3. Cold starts on free tiers can take about a minute or longer; wake with `GET /health` before demos. GitHub scheduled warmups are best-effort and do not guarantee an always-on process.
4. For a public portfolio with no intentional sleep, upgrade the existing web service to an always-on instance instead of relying on cron traffic.

CORS must include the exact Vercel origin(s) in `ALLOWED_ORIGINS`. Add `http://localhost:3000` only when intentionally testing a local frontend against the deployed backend.

---

## Environment variables

### Frontend (`frontend/.env.example`)

| Variable | Required | Notes |
| --- | --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | Production yes | Absolute `http`/`https` backend URL |

### Backend (`backend/.env.example`)

| Variable | Required | Notes |
| --- | --- | --- |
| `ALLOWED_ORIGINS` | Production yes | Comma-separated browser origins |
| `SUPABASE_DB_URL` | For durable DB features | Transaction pooler URI; never commit secrets |
| `LLM_PROVIDER` | For Copilot | e.g. `deepseek` or `openai` |
| `LLM_API_KEY` | For Copilot | Backend only |
| `LLM_BASE_URL` | For Copilot | OpenAI-compatible base URL |
| `COPILOT_MODEL` | For Copilot | Model id |
| `OPENAI_API_KEY` | Deprecated fallback | Prefer `LLM_API_KEY` |
| `PORT` | Optional locally | Render injects automatically |

---

## Database migrations

If using Supabase for research durability, apply migrations under `backend/db/migrations/` in order — not only `schema.sql`. See `backend/db/migrations/README.md`.

---

## Smoke checks

```bash
curl "$API/health"
curl "$API/api/data-sources/status"
curl "$API/api/database/status"
```

Scripts: `backend/scripts/verify_deployed_research_api.py`, `docs/deployment/LIVE_DATA_VERIFICATION.md`.
