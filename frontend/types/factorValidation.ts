/** Factor Validation API result types (frontend). */
import type { BenchmarkEvaluation } from "@/types/researchBenchmark";
import type { ReproducibilityManifest } from "@/types/reproducibility";

export type FactorIcPoint = {
  date: string;
  value: number;
};

export type FactorIcSummary = {
  mean_rank_ic: number | null;
  median_rank_ic: number | null;
  positive_ic_ratio: number | null;
  icir: number | null;
  n_periods: number;
};

export type FactorSeriesPoint = {
  date: string;
  value: number;
};

export type CapmRegression = {
  alpha: number | null;
  alpha_annualized: number | null;
  alpha_annualized_ci_low: number | null;
  alpha_annualized_ci_high: number | null;
  beta: number | null;
  t_stat_alpha: number | null;
  r_squared: number | null;
  n_observations: number;
};

export type PortfolioRiskStats = {
  sharpe_ratio_net: number | null;
  max_drawdown_net: number | null;
};

export type CapmDecomposition = {
  dates: string[];
  cumulative_beta_contribution: FactorSeriesPoint[];
  cumulative_residual_alpha: FactorSeriesPoint[];
  cumulative_cost_drag: FactorSeriesPoint[];
  methodology: string;
};

export type CapmResult = {
  benchmark_symbol: string;
  regression: CapmRegression;
  decomposition: CapmDecomposition;
};

export type FactorValidationProvenance = {
  universe_symbols: string[];
  symbols_used: string[];
  symbol_series: Array<{ symbol: string; provider: string | null; rows: number }>;
  start_date: string;
  end_date: string | null;
  n_factor_periods: number;
  benchmark_symbol: string;
};

export type FactorValidationResult = {
  research_id: string;
  template: string;
  universe_id: string;
  factor_id: string;
  rebalance_frequency: string;
  holding_period_months: number;
  ic: {
    series: FactorIcPoint[];
    rolling_series: FactorIcPoint[];
    summary: FactorIcSummary;
  };
  quantiles: {
    period_returns: Record<string, FactorSeriesPoint[]>;
    cumulative_returns: Record<string, FactorSeriesPoint[]>;
    turnover: { series: FactorSeriesPoint[]; mean: number | null };
    transaction_cost: {
      series: FactorSeriesPoint[];
      total: number | null;
      cost_rate: number;
    };
    n_rebalances: number;
  };
  long_short: {
    period_returns: FactorSeriesPoint[];
    cumulative_returns: FactorSeriesPoint[];
    cumulative_final: number | null;
    period_returns_net_of_cost?: FactorSeriesPoint[];
    cumulative_returns_net_of_cost?: FactorSeriesPoint[];
    cumulative_final_net_of_cost?: number | null;
    note?: string;
  };
  benchmark?: BenchmarkEvaluation;
  capm: CapmResult;
  portfolio_risk: PortfolioRiskStats;
  warnings: string[];
  provenance: FactorValidationProvenance;
  reproducibility_manifest?: ReproducibilityManifest | null;
  generated_at: string;
  validation_run_id: string;
  evidence_kind?: string;
  validation_status?: string;
};

export type FactorValidationStatus =
  | "idle"
  | "loading"
  | "ready"
  | "error";
