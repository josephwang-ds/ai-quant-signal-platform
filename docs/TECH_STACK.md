# Tech Stack

## Frontend

| Item | Choice |
| --- | --- |
| Framework | Next.js 15 (App Router) |
| UI | React 19 |
| Language | TypeScript |
| Charts | Recharts |
| Tests | Vitest + Testing Library + jsdom |
| Package manager | npm (`frontend/package.json`) |

Primary app path: `frontend/`.

## Backend

| Item | Choice |
| --- | --- |
| Framework | FastAPI |
| Server | Uvicorn |
| Language | Python 3 |
| Validation / models | Pydantic v2 |
| Data | pandas, yfinance, AkShare (A-shares) |
| Tests | pytest (`backend/requirements-dev.txt`) |

Primary runtime path: `backend/`. Target modular layout reference: `apps/api/` (not the deployed path).

## Testing

| Layer | Command |
| --- | --- |
| Frontend unit/UI | `cd frontend && npm test` |
| Frontend types | `cd frontend && npx tsc --noEmit` |
| Frontend production build | `cd frontend && npm run build` |
| Backend | `cd backend && pytest` (see local venv / CI) |

CI workflow: `.github/workflows/ci.yml` (backend tests, `apps/api` tests, frontend build).

## Deployment

| Component | Host |
| --- | --- |
| Frontend | Vercel |
| Backend | Render |
| Database | Supabase Postgres (when configured) |
| Copilot LLM | OpenAI-compatible provider (e.g. DeepSeek) via backend env only |

See [`DEPLOYMENT.md`](DEPLOYMENT.md).

## Libraries (selected)

**Frontend:** `next`, `react`, `react-dom`, `recharts`.

**Backend:** `fastapi`, `uvicorn`, `pydantic`, `pandas`, `yfinance`, plus provider packages as documented in `backend/requirements.txt`.

## Project structure (current)

```text
ai-quant-signal-platform/
├── frontend/                 # Next.js workspace
├── backend/                  # FastAPI demonstrable runtime
├── apps/api/                 # Target modular API reference
├── docs/                     # Product, architecture, slices, ADRs
├── .github/                  # CI, templates, CODEOWNERS
├── .cursor/rules/            # Versioned engineering rules
├── README.md
├── CONTRIBUTING.md
├── LICENSE
└── render.yaml
```

Full layout notes: [`../PROJECT_STRUCTURE.md`](../PROJECT_STRUCTURE.md).
