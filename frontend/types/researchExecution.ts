/** Research Execution API types (PR-008B). */

export type DataProvenance = {
  provider: string;
  symbol: string;
  source: string;
  retrieved_at: string;
  requested_start: string;
  requested_end: string | null;
  actual_start: string;
  actual_end: string;
  interval: string;
  cache_hit: boolean;
  cache_stale: boolean;
  currency: string | null;
  adapter?: string;
  requested_symbol?: string;
  canonical_symbol?: string;
  provider_symbol?: string;
  asset_class?: string;
  exchange?: string | null;
  adjustment?: string;
  row_count?: number;
};

export type ExecutionMetrics = {
  total_return: number | null;
  cagr: number | null;
  annualized_volatility: number | null;
  sharpe_ratio: number | null;
  maximum_drawdown: number | null;
  trade_count: number | null;
  win_rate: number | null;
  turnover: number | null;
  total_transaction_costs: number | null;
  observation_count: number;
  start_date: string | null;
  end_date: string | null;
};

export type SupportedEvidence = {
  historical_backtest: string;
  benchmark_comparison: string;
  out_of_sample: string;
  parameter_sensitivity: string;
  transaction_cost_review: string;
  data_quality_review: string;
  evaluation: string;
};

export type ResearchExecutionResult = {
  research_id: string;
  strategy: Record<string, unknown>;
  provenance: DataProvenance;
  metrics: ExecutionMetrics;
  benchmark_metrics: ExecutionMetrics;
  series: Array<Record<string, unknown>>;
  warnings: string[];
  generated_at: string;
  supported_evidence: SupportedEvidence;
};

export type ResearchExecutionStatus =
  | "idle"
  | "loading"
  | "ready"
  | "error";
