# AGENTS.md

## Cursor Cloud specific instructions

This repo is the **AI Quant Research Workspace** (see `docs/PROJECT_BIBLE.md`, `README.md`, `PROJECT_STRUCTURE.md`). It has three code trees:

- `backend/` — FastAPI monolith, the real product API (Python). **Required service.**
- `frontend/` — Next.js 15 / React 19 web UI (Node). **Required service.** Talks to the backend.
- `apps/api/` — a non-deployed *reference* modular-monolith skeleton (in-memory stubs). Only needs its own unit tests to pass; not part of the end-to-end product.

### Environment notes (already provisioned by the update script)

- Python venvs live at `backend/.venv` and `apps/api/.venv`; frontend deps at `frontend/node_modules`. All are gitignored.
- The repo targets Python 3.11 (CI) but runs fine on the VM's Python 3.12. `python3-venv` is required to create the venvs (installed via apt).
- `.env` files are copied from each `.env.example` by the update script. No secrets are needed for local dev — the app degrades gracefully without them (see below).

### Running the services (dev)

Backend (port 8000) — must activate the venv and set `PYTHONPATH`:

```bash
cd backend && source .venv/bin/activate
PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app
```

Health check: `GET http://127.0.0.1:8000/health`. DB status: `GET /api/database/status`.

Frontend (port 3000): `cd frontend && npm run dev`. It reads `NEXT_PUBLIC_API_BASE_URL` (defaults to `http://127.0.0.1:8000`, set in `frontend/.env`).

### Lint / test / build

- Backend tests: `cd backend && source .venv/bin/activate && PYTHONPATH=. python -m pytest tests -m "not live" -q`. `pytest.ini` already excludes `live`-marked tests (which hit Yahoo/AkShare over the network); offline tests inject deterministic data.
- apps/api tests: `cd apps/api && source .venv/bin/activate && PYTHONPATH=src python -m pytest -q`.
- Frontend: `npm test` (Vitest), `npx tsc --noEmit` (typecheck), `npm run build` (Next build). Playwright e2e (`npm run test:e2e`) uses its own server on port 3010 and needs `npx playwright install` first.
- Do NOT run `npm run lint` in automation: `next lint` is **interactive** (there is no committed ESLint config, so it prompts for setup and blocks). CI does not run lint either — see `.github/workflows/ci.yml`.

### Non-obvious gotchas

- Postgres/Supabase (`SUPABASE_DB_URL`), LLM providers (`LLM_API_KEY`), and Finnhub (`FINNHUB_API_KEY`) are all optional. Without them the app runs in "browser-local" mode; persistence and AI/copilot endpoints return HTTP 503 by design, not as an error.
- Some research-pipeline stages in the UI (e.g. Portfolio Construction / Backtesting, and the Factor Study "Run Research" action) may be unimplemented and can return 404. That is a product-state limitation, not an environment problem.
- Features that fetch live market data (e.g. the AI Watchlist / Market Watch page) require outbound network access to Yahoo/AkShare.
