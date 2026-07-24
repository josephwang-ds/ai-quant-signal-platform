/** Factor Validation API result types (frontend). */

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
  warnings: string[];
  provenance: Record<string, unknown>;
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
