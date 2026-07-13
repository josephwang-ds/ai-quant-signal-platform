/**
 * Research Evaluation 领域投影（前端 mock；对齐 Governance Evaluation 语义）。
 *
 * TODO(backend): 替换为 Evaluation Application 用例与 Research Evaluation Engine。
 * AI 不得计算 Research Confidence / Readiness / Eligibility。
 */

export const EVALUATION_DIMENSION_KEYS = [
  "historical_backtest_quality",
  "out_of_sample_performance",
  "parameter_stability",
  "stress_test_resilience",
  "transaction_cost_resilience",
  "risk_review",
  "trade_statistics",
  "data_quality",
  "experiment_coverage",
  "evidence_traceability",
] as const;

export type EvaluationDimensionKey = (typeof EVALUATION_DIMENSION_KEYS)[number];

/** Demo-only weights (must total 100). */
export const EVALUATION_DIMENSION_WEIGHTS: Record<
  EvaluationDimensionKey,
  number
> = {
  historical_backtest_quality: 15,
  out_of_sample_performance: 20,
  parameter_stability: 15,
  stress_test_resilience: 15,
  transaction_cost_resilience: 10,
  risk_review: 10,
  trade_statistics: 5,
  data_quality: 5,
  experiment_coverage: 3,
  evidence_traceability: 2,
};

export const EVALUATION_DIMENSION_STATUSES = [
  "Strong",
  "Acceptable",
  "Weak",
  "Failed",
  "Missing",
  "Inconclusive",
] as const;

export type EvaluationDimensionStatus =
  (typeof EVALUATION_DIMENSION_STATUSES)[number];

export type ConfidenceLevel =
  | "High"
  | "Moderate"
  | "Low"
  | "Insufficient Evidence";

export type ResearchHealth =
  | "Healthy"
  | "Watch"
  | "Degraded"
  | "Blocked";

export type DecisionReadiness =
  | "Ready for Paper Trading"
  | "Ready for Evaluation Review"
  | "Continue Validation"
  | "Continue Research"
  | "Rework Required"
  | "Archive Research";

export type EvaluationRecommendation = DecisionReadiness;

export type EvaluationStatus =
  | "Draft"
  | "Completed"
  | "Superseded"
  | "Blocked"
  | "Missing Validation";

export type EvaluationIssueSeverity = "critical" | "warning" | "info";

export type EvaluationIssueKind = "blocker" | "warning" | "missing_evidence";

export type EvaluationEvidenceLink = {
  id: string;
  claim: string;
  evidenceRef: string;
  detail: string;
};

export type EvaluationDimension = {
  key: EvaluationDimensionKey;
  name: string;
  /** 0–100 raw dimension score (deterministic mock). */
  score: number;
  weight: number;
  status: EvaluationDimensionStatus;
  evidenceRefs: string[];
  evidenceLinks: EvaluationEvidenceLink[];
  limitations: string[];
  blocking: boolean;
  lastUpdatedAt: string;
  summary: string;
};

export type EvaluationIssue = {
  id: string;
  kind: EvaluationIssueKind;
  severity: EvaluationIssueSeverity;
  sourceDimensionKey: EvaluationDimensionKey | null;
  sourceDimensionName: string;
  reason: string;
  evidenceRef: string;
  requiredNextAction: string;
  owner: string;
  dueAt: string | null;
};

export type EvaluationStrengthWeakness = {
  id: string;
  kind: "strength" | "weakness";
  text: string;
  sourceDimensionKey: EvaluationDimensionKey;
  evidenceRef: string;
};

export type EvaluationRuleCheck = {
  id: string;
  rule: string;
  passed: boolean;
  observed: string;
};

export type EvaluationRecommendationPanel = {
  recommendation: EvaluationRecommendation;
  why: string;
  blockingConditions: string[];
  requiredNextActions: string[];
  eligibleNextTransition: string;
  reviewOwner: string;
  reassessmentAt: string;
  ruleChecks: EvaluationRuleCheck[];
};

export type EvaluationHistorySnapshot = {
  id: string;
  evaluatedAt: string;
  confidenceScore: number;
  recommendation: EvaluationRecommendation;
  mainChange: string;
  trigger: string;
  superseded: boolean;
};

export type EvaluationSnapshot = {
  researchId: string;
  evaluationId: string;
  status: EvaluationStatus;
  evaluatedAt: string | null;
  lifecycleStage: string;
  dataConfidence: "high" | "medium" | "low" | "degraded";
  researchHealth: ResearchHealth;
  dimensions: EvaluationDimension[];
  issues: EvaluationIssue[];
  strengthsWeaknesses: EvaluationStrengthWeakness[];
  recommendation: EvaluationRecommendationPanel;
  history: EvaluationHistorySnapshot[];
  evidenceCoveragePct: number;
  hasValidationData: boolean;
  superseded: boolean;
};

export type EvaluationOverviewStats = {
  confidenceScore: number;
  confidenceLevel: ConfidenceLevel;
  researchHealth: ResearchHealth;
  decisionReadiness: DecisionReadiness;
  recommendation: EvaluationRecommendation;
  evaluationStatus: EvaluationStatus;
  lastEvaluatedAt: string | null;
  lifecycleStage: string;
  dataConfidence: "high" | "medium" | "low" | "degraded";
  blockerCount: number;
  evidenceCoveragePct: number;
};

export type EvaluationDimensionStatusFilter =
  | EvaluationDimensionStatus
  | "all";

export type EvaluationFilters = {
  query: string;
  status: EvaluationDimensionStatusFilter;
};

export const DEFAULT_EVALUATION_FILTERS: EvaluationFilters = {
  query: "",
  status: "all",
};
