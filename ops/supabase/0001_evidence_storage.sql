-- Company Lens persistence boundary. Review offline before applying to Supabase/Postgres.
-- Deliberately no vector column: its dimension depends on a selected, evaluated model.
-- Table/index creation and policy replacement are safe to rerun during reviewed setup.

create table if not exists public.documents (
  document_id text primary key,
  owner_id uuid references auth.users(id) on delete cascade,
  ticker text,
  source_type text not null check (
    source_type in ('sec_filing', 'uploaded', 'company_news', 'market_news')
  ),
  title text not null,
  source_url text,
  storage_key text,
  content_hash text not null,
  published_at timestamptz,
  fetched_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists public.document_chunks (
  citation text primary key,
  document_id text not null references public.documents(document_id) on delete cascade,
  chunk_index integer not null check (chunk_index >= 0),
  text text not null,
  metadata jsonb not null default '{}'::jsonb,
  search_vector tsvector generated always as (
    to_tsvector('simple', coalesce(text, ''))
  ) stored,
  unique (document_id, chunk_index)
);

create index if not exists document_chunks_search_idx
  on public.document_chunks using gin (search_vector);

create table if not exists public.headlines (
  headline_id text primary key,
  owner_id uuid references auth.users(id) on delete cascade,
  headline text not null,
  publisher text not null,
  published_at timestamptz not null,
  fetched_at timestamptz,
  url text not null check (url ~ '^https?://'),
  source_type text not null check (source_type in ('company_news', 'market_news')),
  tickers text[] not null default '{}',
  topic text,
  created_at timestamptz not null default now()
);

create index if not exists headlines_tickers_idx
  on public.headlines using gin (tickers);
create index if not exists headlines_published_at_idx
  on public.headlines (published_at desc);

create table if not exists public.rulesets (
  ruleset_id text primary key,
  owner_id uuid references auth.users(id) on delete cascade,
  name text not null,
  rules jsonb not null check (jsonb_typeof(rules) = 'array'),
  trust_policy_version text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.retrieval_runs (
  run_id text primary key,
  owner_id uuid references auth.users(id) on delete cascade,
  query text not null,
  scope jsonb not null,
  selected_citations jsonb not null check (
    jsonb_typeof(selected_citations) = 'array'
  ),
  index_version text not null,
  latency_ms integer not null check (latency_ms >= 0),
  created_at timestamptz not null default now()
);

create table if not exists public.llm_runs (
  run_id text primary key,
  owner_id uuid references auth.users(id) on delete cascade,
  provider text not null,
  model text not null,
  prompt_version text not null,
  evidence_hash text not null,
  validator_status text not null,
  usage jsonb not null default '{}'::jsonb,
  cost jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

alter table public.documents enable row level security;
alter table public.document_chunks enable row level security;
alter table public.headlines enable row level security;
alter table public.rulesets enable row level security;
alter table public.retrieval_runs enable row level security;
alter table public.llm_runs enable row level security;

-- Public reads are limited to approved source metadata. User uploads remain private.
drop policy if exists "public source documents are readable" on public.documents;
create policy "public source documents are readable"
  on public.documents for select
  using (
    owner_id is null
    and source_type in ('sec_filing', 'company_news', 'market_news')
  );

drop policy if exists "owners manage documents" on public.documents;
create policy "owners manage documents"
  on public.documents for all
  using (owner_id = auth.uid())
  with check (owner_id = auth.uid());

drop policy if exists "public source chunks are readable" on public.document_chunks;
drop policy if exists "owners manage document chunks" on public.document_chunks;
create policy "owners manage document chunks"
  on public.document_chunks for all
  using (
    exists (
      select 1
      from public.documents
      where documents.document_id = document_chunks.document_id
        and documents.owner_id = auth.uid()
    )
  )
  with check (
    exists (
      select 1
      from public.documents
      where documents.document_id = document_chunks.document_id
        and documents.owner_id = auth.uid()
    )
  );

drop policy if exists "public headlines are readable" on public.headlines;
create policy "public headlines are readable"
  on public.headlines for select
  using (owner_id is null);

drop policy if exists "owners manage headlines" on public.headlines;
create policy "owners manage headlines"
  on public.headlines for all
  using (owner_id = auth.uid())
  with check (owner_id = auth.uid());

drop policy if exists "owners manage rulesets" on public.rulesets;
create policy "owners manage rulesets"
  on public.rulesets for all
  using (owner_id = auth.uid())
  with check (owner_id = auth.uid());

drop policy if exists "owners manage retrieval runs" on public.retrieval_runs;
create policy "owners manage retrieval runs"
  on public.retrieval_runs for all
  using (owner_id = auth.uid())
  with check (owner_id = auth.uid());

drop policy if exists "owners manage llm runs" on public.llm_runs;
create policy "owners manage llm runs"
  on public.llm_runs for all
  using (owner_id = auth.uid())
  with check (owner_id = auth.uid());

-- Data API privileges are explicit because project setup disables automatic table
-- exposure. RLS still decides which rows anon/authenticated callers may access;
-- backend secret keys map to service_role and intentionally bypass RLS.
grant usage on schema public to anon, authenticated, service_role;

grant select on table
  public.documents,
  public.headlines
to anon;

grant select, insert, update, delete on table
  public.documents,
  public.document_chunks,
  public.headlines,
  public.rulesets,
  public.retrieval_runs,
  public.llm_runs
to authenticated, service_role;

comment on table public.documents is
  'Immutable source metadata; uploaded object bodies remain in private Storage.';
comment on table public.document_chunks is
  'Normalized untrusted evidence chunks with deterministic citations and full-text search.';
comment on table public.headlines is
  'Source-linked headline metadata only; no scraped article bodies.';
comment on table public.rulesets is
  'Reader preferences versioned separately from immutable trust policy.';
comment on table public.retrieval_runs is
  'Enforced retrieval scope and selected citation provenance.';
comment on table public.llm_runs is
  'Provider/model/prompt and validator provenance; never provider keys or raw env data.';
