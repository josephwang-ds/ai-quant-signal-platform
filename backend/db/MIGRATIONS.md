# Database migrations

Optional Supabase / Postgres persistence is applied manually (there is no auto-migrate on boot).

## Order

1. `backend/db/schema.sql` — durable Strategy Studio / Saved Runs tables (`backtest_runs`, `backtest_trades`)
2. `backend/db/migrations/002_research_lifecycle.sql` — research projects, protocol versions, evidence snapshots, validation runs, agent runs/events, approvals, decision records

## Rules

- Frontend never connects to Supabase; only FastAPI uses `SUPABASE_DB_URL`
- Without the database, Research Home stays **browser-local** and backtests still run
- Do not merge browser-local and persisted records without an explicit user confirmation
- Tables intentionally omit raw prompts, chain-of-thought, and API keys

## After applying

Confirm `GET /api/database/status` reports `configured` + `connected` and `persistence_mode` of `persisted`.
User-facing messages must never include the connection string.

Optional lifecycle write/read endpoints (FastAPI only):

- `GET /api/v1/research/persistence/mode`
- `PUT /api/v1/research/persistence/projects`
- `POST /api/v1/research/persistence/protocol-versions` (immutable once published)
- `POST /api/v1/research/persistence/evidence-snapshots`
- `POST /api/v1/research/persistence/validation-runs` (supports `idempotency_key`)
- `POST /api/v1/research/persistence/agent-runs` + event list
- `POST|GET /api/v1/research/persistence/decision-records`

Without DB configuration these return safe HTTP 503 and the UI stays browser-local.
