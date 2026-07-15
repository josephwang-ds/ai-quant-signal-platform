# AI Quant Research Workspace

**A research operating system for moving quantitative ideas into evidence and governed decisions.**

[Architecture](docs/PROJECT_BIBLE.md) · [Roadmap](ROADMAP.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Changelog](CHANGELOG.md)

> **Research First. AI Second. Decisions Last.**

AI Quant Research Workspace is a Strategy-centric environment for quantitative research, validation, review, risk governance, portfolio analysis, simulation, and monitoring. It is not a trading bot, stock prediction model, broker, or live execution platform.

The repository is evolving from a working quant-research demonstration into a production-quality modular platform. Existing runtime behavior remains available while the frozen architecture is adopted through deliberate vertical slices.

## Why this exists

Quant research rarely fails because one more chart is missing. It fails when hypotheses, datasets, assumptions, experiments, validation, reviews, and decisions become disconnected.

This workspace keeps the full chain visible:

```text
Idea → Research → Validation → Paper Simulation → Monitoring → Review → Retirement
```

Every durable conclusion should trace to metrics, evidence, and source provenance. AI can explain and compare that evidence; deterministic quantitative and risk rules retain authority.

## Product overview

The intended workspace connects nine research capabilities:

```mermaid
flowchart TB
  MI["Market Intelligence"] --> RL["Research Lab"] --> VC["Validation Center"]
  VC --> RR["Research Review"] --> RG["Risk Governance"] --> SR["Strategy Registry"]
  SR --> PR["Portfolio Review"] --> SC["Simulation Center"] --> RN["Research Notebook"]
  RN -.evidence and iteration.-> RL
```

Current implementation includes a Next.js research interface and a FastAPI backend for market data, rule-based backtests, robustness checks, experiment records, risk monitoring, and paper simulation. The canonical MA Crossover research is connected to real backend evidence through four vertical slices: execution (`POST /api/v1/research/execution`), validation (`POST /api/v1/research/validation`), evaluation (`POST /api/v1/research/evaluation`), and the evidence-grounded Research Copilot (`POST /api/v1/research/copilot/query`) — evaluation summarizes validation evidence into a governance status (`completed` / `incomplete` / `blocked`) and never recalculates, scores, or recommends; the Copilot explains existing evidence only and never calculates or recommends trades. Research market data routes by asset class behind one `MarketDataPort` (Yahoo for global assets, AkShare for mainland A-shares) — see `docs/slices/multi-provider-market-data.md`. See `docs/slices/`. The newer `apps/api/` tree is an early reference slice for the target architecture, not yet the complete production runtime.

## Screenshots

| Workspace view | Publication slot |
|---|---|
| Research List | Capture the Strategy-linked research portfolio with lifecycle, owner, and evidence confidence. |
| Research Workspace | Capture hypothesis, experiments, validation state, and next governed action. |
| Decision Review | Capture quantitative evidence, AI interpretation, risk gate, and decision provenance. |

Screenshots will be added after the workspace information architecture stabilizes; the descriptions above are intentional capture requirements, not missing product specifications.

## Architecture

The frozen architecture combines a **modular monolith**, **Domain-Driven Design**, **Clean Architecture**, **vertical slices**, and **event-driven workflows**.

```mermaid
flowchart TB
  User["Researcher / Reviewer"] --> Web["Next.js workspace"]
  Web --> API["FastAPI presentation"] --> Application["Application use cases"]
  Application --> Domain["Domain aggregates and policies"]
  Infrastructure["Persistence, market data, LLM, scheduler adapters"] --> Application
  Infrastructure --> Domain
  Application --> Events["Domain events"] --> Application
```

Strict dependency direction:

```text
Presentation → Application → Domain
Infrastructure ───────────→ inward-owned ports
```

Bounded contexts are Research, Validation, Governance, Portfolio, and Market Intelligence. Strategy is the central lifecycle identity; contexts own their records and integrate through stable contracts and events.

Read the [Project Bible](docs/PROJECT_BIBLE.md) for the engineering constitution and the [Architecture Bible](docs/Architecture-Bible/) for the detailed product, domain, state-machine, and runtime design.

## Tech stack

| Area | Current technology | Architectural role |
|---|---|---|
| Web | Next.js 15, React 19, TypeScript 5 | workspace presentation |
| Visualization | Recharts | research charts and quantitative views |
| API | FastAPI, Pydantic | HTTP boundary and composition |
| Quantitative computation | pandas | indicators, backtests, and metrics |
| Persistence | PostgreSQL via psycopg; Supabase-compatible configuration | durable research assets |
| Market data | AKShare, Yahoo/yfinance, Stooq | external provider adapters |
| Testing | pytest | domain, service, and API verification |
| Deployment | Vercel-compatible web, Render descriptor for current backend | current operational topology |

Technology is an adapter choice. Domain behavior must remain independent of FastAPI, databases, providers, schedulers, and LLM SDKs.

## Getting started

### Prerequisites

- Python 3.9 or newer for the current backend
- Node.js 18 or newer and npm for the web application

### 1. Start the current backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

The backend runs without a database connection; persistence-dependent capabilities report their unavailable state. Never commit real credentials.

### 2. Start the web application

In a second terminal:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The current API documentation is at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 3. Run checks

```bash
cd backend
source .venv/bin/activate
PYTHONPATH=. python -m pytest tests -m "not live" -q
```

```bash
cd apps/api
source .venv/bin/activate
python -m pytest -q
```

```bash
cd frontend
npm test -- --run
npx tsc --noEmit
npm run build
```

GitHub Actions runs the same offline gates on every pull request and push to
`main` via [`.github/workflows/ci.yml`](.github/workflows/ci.yml): backend
offline tests, `apps/api` tests, frontend tests/typecheck/build, and
repository authenticity policy checks. Live Yahoo and AkShare verification is
optional and manual only — see
[`docs/deployment/LIVE_DATA_VERIFICATION.md`](docs/deployment/LIVE_DATA_VERIFICATION.md).

The target API reference slice lives under `apps/api/`. See [`apps/api/README.md`](apps/api/README.md) for dependencies, entrypoint, startup, and development commands.

## Environment

| Variable | Scope | Purpose |
|---|---|---|
| `ALLOWED_ORIGINS` | backend | comma-separated browser origins for CORS |
| `SUPABASE_DB_URL` | backend | optional PostgreSQL transaction-pooler connection |
| `NEXT_PUBLIC_API_BASE_URL` | frontend | required production backend URL; local development falls back to `http://127.0.0.1:8000` |

Use the checked-in `.env.example` files as the source for variable names. Keep secrets in local or deployment environment configuration only.
Production has no hardcoded API fallback. See the
[Production API Wiring runbook](docs/deployment/PRODUCTION_API_WIRING.md) for
Vercel, Render CORS, timeout, endpoint-semantics, and troubleshooting details.

## Repository structure

```text
.
├── apps/api/                  # target modular-monolith reference slices
├── backend/                   # current FastAPI runtime
├── frontend/                  # current Next.js workspace
├── docs/
│   ├── Architecture-Bible/    # frozen architecture
│   ├── adr/                   # architectural decisions
│   ├── slices/                # vertical-slice notes
│   ├── PROJECT_BIBLE.md       # single source of truth
│   └── STYLE_GUIDE.md
├── .cursor/rules/             # repository-aware AI engineering rules
├── CONTRIBUTING.md
├── ROADMAP.md
└── PROJECT_STRUCTURE.md
```

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for folder ownership, naming, dependency rules, and the staged target layout.

## Roadmap

The roadmap advances through engineering foundation, domain core, research workspace, validation and governance, portfolio and monitoring, governed AI, and production readiness.

Near-term engineering priorities are:

1. establish repeatable quality gates and dependency-boundary checks;
2. normalize the reference `apps/api/` slice and migration contract;
3. encode the frozen lifecycle state machines in the Domain layer;
4. connect research artifacts through Strategy identity and Evidence provenance; and
5. preserve current runtime behavior during incremental migration.

See the complete [ROADMAP.md](ROADMAP.md). Planned work is not implemented behavior.

## Engineering principles

- Strategy-centric, not page-centric
- Research-first, not execution-first
- Quantitative evidence before AI interpretation
- Deterministic validation before probabilistic explanation
- Domain rules independent of frameworks and providers
- Explicit lifecycle transitions and immutable history
- Small, complete vertical slices
- Secure, observable, reversible change

## Contributing

Start with [CONTRIBUTING.md](CONTRIBUTING.md). All changes should identify their bounded context, preserve inward dependencies, include proportionate tests, and update documentation or ADRs when decisions change.

The AI-assisted handoff is documented in [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md): ChatGPT frames, Codex implements and verifies, Cursor supports local refinement, reviewers validate, and maintainers merge.

Use the repository’s structured GitHub forms for [bug reports](https://github.com/josephwang-ds/ai-quant-signal-platform/issues/new?template=bug_report.yml), [feature requests](https://github.com/josephwang-ds/ai-quant-signal-platform/issues/new?template=feature_request.yml), epics, and stories. Every participant must follow the [Code of Conduct](CODE_OF_CONDUCT.md). Security-sensitive findings belong in the private process described by [SECURITY.md](SECURITY.md), never in a public issue.

## Governance

| Document | Purpose |
|---|---|
| [Project Bible](docs/PROJECT_BIBLE.md) | product and engineering constitution |
| [Architecture Decision Records](docs/adr/) | durable decisions and consequences |
| [Roadmap](ROADMAP.md) | capability sequence and milestone outcomes |
| [Contributing Guide](CONTRIBUTING.md) | issue, branch, review, and Definition of Done |
| [Code of Conduct](CODE_OF_CONDUCT.md) | community participation and enforcement |
| [Security Policy](SECURITY.md) | private vulnerability reporting and disclosure |
| [Changelog](CHANGELOG.md) | notable repository changes and release history |

## Project status

This repository is under active architectural migration. The `backend/` and `frontend/` paths contain the current demonstrable runtime; `apps/api/` begins the production-shaped modular structure. See [MIGRATION_REPORT.md](MIGRATION_REPORT.md) before moving, renaming, or deleting legacy assets.

## Responsible use

This software supports research and paper simulation. It is not financial advice, does not guarantee results, and is not designed for live order execution. Historical and simulated performance can differ materially from real outcomes.

## License

This repository is licensed under the [MIT License](LICENSE). Copyright (c) 2026 Joseph Wang.
