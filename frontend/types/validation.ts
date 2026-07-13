/** Research Validation Pipeline 领域投影（前端 mock；对齐 Ch3 ValidationRun 结果语义）。 */

export const VALIDATION_STAGE_KEYS = [
  "historical_backtest",
  "benchmark_comparison",
  "out_of_sample",
  "parameter_sensitivity",
  "stress_testing",
  "regime_analysis",
  "transaction_cost_review",
  "data_quality_review",
] as const;

export type ValidationStageKey = (typeof VALIDATION_STAGE_KEYS)[number];

export const VALIDATION_STATUSES = [
  "Not Started",
  "Ready",
  "Running",
  "Passed",
  "Failed",
  "Inconclusive",
  "Invalidated",
] as const;

export type ValidationStatus = (typeof VALIDATION_STATUSES)[number];

export type ValidationReadinessLabel =
  | "Insufficient Evidence"
  | "Continue Validation"
  | "Ready for Evaluation"
  | "Blocked";

export type GateSeverity = "info" | "warning" | "blocking";

export type ValidationGate = {
  id: string;
  rule: string;
  threshold: string;
  observed: string;
  passed: boolean;
  severity: GateSeverity;
  evidenceRef: string;
};

export type ValidationMetric = {
  key: string;
  label: string;
  value: string;
  /** historical | simulated — never forward-looking claim */
  basis: "historical" | "simulated";
};

export type ValidationRunHistoryItem = {
  id: string;
  ranAt: string;
  outcome: ValidationStatus;
  note: string;
};

export type ValidationStage = {
  id: string;
  researchId: string;
  stageKey: ValidationStageKey;
  name: string;
  status: ValidationStatus;
  purpose: string;
  method: string;
  dataset: string;
  dateRange: string;
  benchmark: string;
  successCriteria: string;
  falsificationCriteria: string;
  lastRunAt: string | null;
  owner: string;
  evidenceCount: number;
  keyResult: string;
  warnings: string[];
  nextAction: string;
  result: string;
  metrics: ValidationMetric[];
  gates: ValidationGate[];
  evidenceRefs: string[];
  dataConfidence: "high" | "medium" | "low" | "degraded";
  limitations: string[];
  recommendation: string;
  runHistory: ValidationRunHistoryItem[];
};

export type ValidationBlocker = {
  id: string;
  researchId: string;
  severity: GateSeverity;
  reason: string;
  affectedStageId: string;
  affectedStageName: string;
  requiredNextAction: string;
};

export type ValidationPipelineSnapshot = {
  researchId: string;
  stages: ValidationStage[];
  blockers: ValidationBlocker[];
  lastValidationAt: string | null;
};

export type ValidationOverviewStats = {
  overallStatus: ValidationStatus | "Mixed";
  completedCount: number;
  passedCount: number;
  failedCount: number;
  inconclusiveCount: number;
  notStartedCount: number;
  runningCount: number;
  blockingCount: number;
  lastValidationAt: string | null;
  readiness: ValidationReadinessLabel;
};

export type ValidationStatusFilter = ValidationStatus | "all";

export type ValidationFilters = {
  query: string;
  status: ValidationStatusFilter;
};

export const DEFAULT_VALIDATION_FILTERS: ValidationFilters = {
  query: "",
  status: "all",
};
