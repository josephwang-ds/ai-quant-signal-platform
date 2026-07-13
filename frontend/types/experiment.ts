/** Research Experiments 领域投影类型（前端 mock；对齐 Ch3 Experiment 状态机）。 */

export const EXPERIMENT_STATUSES = [
  "Designed",
  "Approved",
  "Running",
  "Completed",
  "Failed",
  "Invalidated",
] as const;

export type ExperimentStatus = (typeof EXPERIMENT_STATUSES)[number];

/** 主路径进度阶段（不含 Failed / Invalidated 终态旁路）。 */
export const EXPERIMENT_PROGRESS_STAGES = [
  "Designed",
  "Approved",
  "Running",
  "Completed",
] as const;

export type ExperimentProgressStage = (typeof EXPERIMENT_PROGRESS_STAGES)[number];

export const EXPERIMENT_TYPES = [
  "Backtest",
  "Parameter Test",
  "Feature Test",
  "Regime Test",
  "Cost Test",
  "Model Comparison",
] as const;

export type ExperimentType = (typeof EXPERIMENT_TYPES)[number];

export type ValidationReadiness =
  | "not_ready"
  | "partial"
  | "ready"
  | "blocked";

export type ExperimentMetrics = {
  sharpe: number | null;
  cagr: number | null;
  maxDrawdown: number | null;
  volatility: number | null;
  tradeCount: number | null;
  winRate: number | null;
  totalTransactionCost: number | null;
};

export type ExperimentParameter = {
  key: string;
  value: string;
};

export type ResearchExperiment = {
  id: string;
  researchId: string;
  name: string;
  hypothesis: string;
  status: ExperimentStatus;
  experimentType: ExperimentType;
  datasetOrSymbol: string;
  startDate: string;
  endDate: string;
  benchmark: string;
  parameters: ExperimentParameter[];
  successCriteria: string;
  falsificationCondition: string;
  notes: string;
  owner: string;
  createdAt: string;
  updatedAt: string;
  resultSummary: string;
  metrics: ExperimentMetrics;
  linkedNotebookEntryIds: string[];
  relatedEvidenceIds: string[];
  validationReadiness: ValidationReadiness;
};

export type ExperimentStatusFilter = ExperimentStatus | "all";
export type ExperimentTypeFilter = ExperimentType | "all";
export type ExperimentSort = "updated" | "created" | "result";

export type ExperimentFilters = {
  query: string;
  status: ExperimentStatusFilter;
  experimentType: ExperimentTypeFilter;
  sort: ExperimentSort;
};

export const DEFAULT_EXPERIMENT_FILTERS: ExperimentFilters = {
  query: "",
  status: "all",
  experimentType: "all",
  sort: "updated",
};

export type ExperimentComposerValues = {
  name: string;
  hypothesis: string;
  experimentType: ExperimentType | "";
  datasetOrSymbol: string;
  startDate: string;
  endDate: string;
  benchmark: string;
  parameters: string;
  successCriteria: string;
  falsificationCondition: string;
  notes: string;
};

export const EMPTY_EXPERIMENT_COMPOSER: ExperimentComposerValues = {
  name: "",
  hypothesis: "",
  experimentType: "",
  datasetOrSymbol: "",
  startDate: "",
  endDate: "",
  benchmark: "",
  parameters: "",
  successCriteria: "",
  falsificationCondition: "",
  notes: "",
};

export const EMPTY_EXPERIMENT_METRICS: ExperimentMetrics = {
  sharpe: null,
  cagr: null,
  maxDrawdown: null,
  volatility: null,
  tradeCount: null,
  winRate: null,
  totalTransactionCost: null,
};
