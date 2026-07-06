-- AI Quant Research Workspace — Database Preparation v1
-- Run in Supabase SQL Editor. Stores durable research assets only (no raw OHLCV).

create extension if not exists "pgcrypto";

create table if not exists backtest_runs (
  id uuid primary key default gen_random_uuid(),
  ticker text not null,
  market text,
  data_source text not null default 'yahoo',
  strategy text not null,
  strategy_config jsonb not null,
  start_date date not null,
  end_date date,
  transaction_cost numeric,
  metrics jsonb not null,
  notes text,
  created_at timestamptz not null default now()
);

create table if not exists backtest_trades (
  id uuid primary key default gen_random_uuid(),
  backtest_run_id uuid not null references backtest_runs(id) on delete cascade,
  trade_date date not null,
  action text not null,
  price numeric,
  signal numeric,
  position_after numeric,
  reason text,
  created_at timestamptz not null default now()
);

create index if not exists idx_backtest_runs_created_at on backtest_runs (created_at desc);
create index if not exists idx_backtest_runs_ticker on backtest_runs (ticker);
create index if not exists idx_backtest_runs_strategy on backtest_runs (strategy);
create index if not exists idx_backtest_trades_run_id on backtest_trades (backtest_run_id);
create index if not exists idx_backtest_trades_trade_date on backtest_trades (trade_date);

alter table backtest_runs enable row level security;
alter table backtest_trades enable row level security;

-- RLS policies are not created in v1.
-- FastAPI backend writes using SUPABASE_DB_URL; frontend does not connect directly.
