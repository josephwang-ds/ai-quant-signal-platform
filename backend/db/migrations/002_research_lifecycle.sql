-- Migration 002: Research lifecycle persistence (optional Supabase)
-- Apply in Supabase SQL Editor after schema.sql (v1 backtest_runs).
-- Frontend never connects directly; FastAPI uses SUPABASE_DB_URL.

create extension if not exists "pgcrypto";

create table if not exists research_projects (
  id text primary key,
  research_type text not null,
  name text not null,
  question text not null,
  hypothesis text,
  null_hypothesis text,
  mechanism text,
  benchmark text,
  status text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists research_protocol_versions (
  id uuid primary key default gen_random_uuid(),
  research_id text not null references research_projects(id) on delete restrict,
  version integer not null,
  parameters jsonb not null,
  success_criteria jsonb not null default '[]'::jsonb,
  limitations jsonb not null default '[]'::jsonb,
  protocol_hash text not null,
  created_at timestamptz not null default now(),
  unique (research_id, version)
);

create index if not exists idx_research_protocol_hash
  on research_protocol_versions (protocol_hash);

create table if not exists evidence_snapshots (
  id text primary key,
  research_id text not null references research_projects(id) on delete restrict,
  schema_version text not null,
  evidence jsonb not null,
  evidence_hash text not null,
  reproducibility_manifest jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_evidence_snapshots_research
  on evidence_snapshots (research_id, created_at desc);
create index if not exists idx_evidence_snapshots_hash
  on evidence_snapshots (evidence_hash);

create table if not exists validation_runs (
  id text primary key,
  research_id text not null references research_projects(id) on delete restrict,
  protocol_version_id uuid references research_protocol_versions(id) on delete restrict,
  status text not null,
  evidence_snapshot_id text references evidence_snapshots(id) on delete restrict,
  reproducibility_manifest jsonb,
  idempotency_key text,
  created_at timestamptz not null default now(),
  completed_at timestamptz
);

create unique index if not exists idx_validation_runs_idempotency
  on validation_runs (research_id, idempotency_key)
  where idempotency_key is not null;

create table if not exists agent_runs (
  id text primary key,
  research_id text not null references research_projects(id) on delete restrict,
  validation_run_id text references validation_runs(id) on delete restrict,
  status text not null,
  rulebook_version text,
  llm_used boolean not null default false,
  llm_provider text,
  llm_model text,
  deterministic_suggestion text,
  created_at timestamptz not null default now(),
  completed_at timestamptz
);

create table if not exists agent_run_events (
  id uuid primary key default gen_random_uuid(),
  agent_run_id text not null references agent_runs(id) on delete cascade,
  sequence integer not null,
  authority text not null,
  node text not null,
  status text not null,
  summary text not null,
  evidence_ids jsonb not null default '[]'::jsonb,
  methodology_citations jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  unique (agent_run_id, sequence)
);

create table if not exists approval_events (
  id uuid primary key default gen_random_uuid(),
  agent_run_id text not null references agent_runs(id) on delete cascade,
  tool_name text,
  requested_at timestamptz not null default now(),
  resolved_at timestamptz,
  resolution text,
  reviewer_note text
);

create table if not exists decision_records (
  id uuid primary key default gen_random_uuid(),
  research_id text not null references research_projects(id) on delete restrict,
  evidence_snapshot_id text references evidence_snapshots(id) on delete restrict,
  agent_run_id text references agent_runs(id) on delete restrict,
  suggested_outcome text,
  human_outcome text not null,
  override_reason text,
  rationale text not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_decision_records_research
  on decision_records (research_id, created_at desc);

-- Notes:
-- * No raw prompts / chain-of-thought columns by design.
-- * No API keys stored.
-- * Apply only when optional persistence is desired.
