# Development

## Install

### Prerequisites

- Node.js 20+ (for Next.js 15)
- Python 3.11+ recommended
- npm

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
```

---

## Run

Terminal 1 — API:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Terminal 2 — workspace:

```bash
cd frontend
npm run dev
```

Useful frontend scripts:

| Script | Purpose |
| --- | --- |
| `npm run dev` | Dev server |
| `npm run dev:clean` | Kill port 3000, clear `.next`, restart |
| `npm run build` | Production build |
| `npm test` | Vitest |

---

## Test

```bash
# Frontend
cd frontend
npm test
npx tsc --noEmit
npm run build

# Backend
cd backend
source .venv/bin/activate
pytest
```

CI runs backend tests, `apps/api` tests, and frontend build via `.github/workflows/ci.yml`.

---

## Coding conventions

- Follow [`PROJECT_BIBLE.md`](PROJECT_BIBLE.md) and accepted ADRs before changing contracts
- Prefer vertical slices; do not couple bounded contexts through internals
- AI interprets evidence; it does not create quantitative truth ([`AUTHENTICITY.md`](AUTHENTICITY.md))
- Keep changes scoped; update slice notes / ADRs when behaviour or contracts change
- Do not commit secrets (`.env`, credentials)
- Contribution flow: [`../CONTRIBUTING.md`](../CONTRIBUTING.md), [`../DEVELOPMENT_WORKFLOW.md`](../DEVELOPMENT_WORKFLOW.md)

Visual language: [`STYLE_GUIDE.md`](STYLE_GUIDE.md). Cursor rules: `.cursor/rules/`.

---

## Folder structure (working tree)

```text
frontend/
  app/                 # Next.js routes
  components/          # UI and feature modules
  lib/                 # Clients, policies, i18n, workflow helpers
  types/               # Shared TypeScript contracts

backend/
  app/
    api/routes/        # HTTP routers
    research_*/        # Execution, validation, evaluation, copilot
    data_providers/    # Market data adapters
    main.py            # App entry + legacy lab routes
  db/                  # Schema and migrations
  tests/               # Pytest suite
  scripts/             # Operator / verification scripts

docs/
  Architecture-Bible/  # Frozen architecture chapters
  adr/                 # Decision records
  slices/              # Delivery notes per capability
  *.md                 # Portfolio-facing guides (this set)
```

See also [`../PROJECT_STRUCTURE.md`](../PROJECT_STRUCTURE.md).
