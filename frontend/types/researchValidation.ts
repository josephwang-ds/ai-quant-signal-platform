import type { DataProvenance, ExecutionMetrics } from "@/types/researchExecution";

export type ValidationStageStatus =
  | "completed"
  | "incomplete"
  | "failed"
  | "unavailable";

export type ValidationStage = {
  stage: string;
  label: string;
  status: ValidationStageStatus;
  summary: string;
  evidence: Record<string, unknown>;
  rules: string[];
  warnings: string[];
  blockers: string[];
  generated_at: string | null;
  provenance: DataProvenance | null;
};

export type OutOfSampleValidation = {
  status: ValidationStageStatus;
  split_date: string | null;
  in_sample_ratio: number | null;
  minimum_oos_observations: number | null;
  in_sample_metrics: ExecutionMetrics | null;
  out_of_sample_metrics: ExecutionMetrics | null;
  oos_benchmark_metrics: ExecutionMetrics | null;
  in_sample_observation_count: number | null;
  out_of_sample_observation_count: number | null;
  warnings: string[];
  boundary_convention: string | null;
};

export type ParameterSensitivityResult = {
  short_window: number | null;
  long_window: number | null;
  total_return: number | null;
  cagr: number | null;
  sharpe_ratio: number | null;
  maximum_drawdown: number | null;
  annualized_volatility: number | null;
  trade_count: number | null;
  total_transaction_costs: number | null;
  status: ValidationStageStatus;
  warnings: string[];
  is_canonical: boolean;
};

export type ParameterSensitivity = {
  status: ValidationStageStatus;
  results: ParameterSensitivityResult[];
  valid_combination_count: number | null;
  profitable_combination_count: number | null;
  positive_sharpe_count: number | null;
  median_sharpe: number | null;
  sharpe_range: [number | null, number | null];
  median_max_drawdown: number | null;
  canonical_percentile_by_sharpe: number | null;
  warnings: string[];
};

export type TransactionCostSensitivityResult = {
  transaction_cost: number | null;
  total_return: number | null;
  cagr: number | null;
  sharpe_ratio: number | null;
  maximum_drawdown: number | null;
  trade_count: number | null;
  total_transaction_costs: number | null;
  return_degradation_from_zero: number | null;
  sharpe_degradation_from_zero: number | null;
  mathematically_valid: boolean;
  warnings: string[];
};

export type TransactionCostSensitivity = {
  status: ValidationStageStatus;
  results: TransactionCostSensitivityResult[];
  canonical_cost: number | null;
  canonical_cost_result: TransactionCostSensitivityResult | null;
  warnings: string[];
};

export type DataQualityCheck = {
  name: string;
  severity: string;
  status: string;
  summary: string;
};

export type DataQualityValidation = {
  status: ValidationStageStatus;
  fatal_issues: string[];
  warnings: string[];
  informational: Record<string, unknown>;
  checks: DataQualityCheck[];
};

export type ResearchValidationResult = {
  research_id: string;
  strategy: Record<string, unknown>;
  provenance: DataProvenance;
  validation_status: ValidationStageStatus;
  evidence_complete: boolean;
  stages: ValidationStage[];
  oos: OutOfSampleValidation;
  parameter_sensitivity: ParameterSensitivity;
  transaction_cost_sensitivity: TransactionCostSensitivity;
  data_quality: DataQualityValidation;
  warnings: string[];
  generated_at: string;
  // Opaque id under which the backend saved this exact result. Evaluation
  // loads evidence by this id instead of re-running Validation.
  validation_run_id: string;
};

export type ResearchValidationStatus = "idle" | "loading" | "ready" | "error";
