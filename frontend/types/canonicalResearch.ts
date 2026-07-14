/**
 * Layered research package types for authenticity-first Research Workspace.
 *
 * Static definition may be local. Runtime market data, calculated evidence,
 * and evaluation results must remain unavailable until the Research Execution
 * Engine integrates real historical data (PR-008B+).
 */

export type ResearchParameter = {
  key: string;
  label: string;
  value: string;
};

export type PlannedValidationStage = {
  id: string;
  name: string;
  status: "not_started" | "awaiting_data";
  description: string;
};

/** 1. Static research definition — allowed in the public demo. */
export type StaticResearchDefinition = {
  id: string;
  name: string;
  researchQuestion: string;
  hypothesis: string;
  researchObjective: string;
  strategyName: string;
  symbol: string;
  benchmark: string;
  parameters: ResearchParameter[];
  tags: string[];
  ownerLabel: string;
  publicityLabel: string;
  explanatoryText: string;
  dataRequirements: string[];
};

/** 2. Planned experiments — protocol only; no calculated metrics. */
export type PlannedExperimentDefinition = {
  id: string;
  name: string;
  experimentType: string;
  hypothesis: string;
  successCriteria: string;
  falsificationCondition: string;
  notes: string;
  parameters: ResearchParameter[];
};

/** 3–5. Runtime / calculated / evaluation slots — null until real engine. */
export type RuntimeMarketDataSlot = null;
export type CalculatedEvidenceSlot = null;
export type EvaluationResultSlot = null;

export type CanonicalResearchPackage = {
  definition: StaticResearchDefinition;
  plannedExperiments: PlannedExperimentDefinition[];
  plannedValidationStages: PlannedValidationStage[];
  designNotes: Array<{
    id: string;
    entryType:
      | "Observation"
      | "Hypothesis"
      | "Decision"
      | "Action"
      | "Result"
      | "Reflection";
    title: string;
    body: string;
    tags: string[];
  }>;
  timelineEvents: Array<{
    id: string;
    title: string;
    summary: string;
    kind: "notebook_entry" | "stage_change" | "validation" | "experiment";
    occurredAt: string;
  }>;
  runtimeMarketData: RuntimeMarketDataSlot;
  calculatedEvidence: CalculatedEvidenceSlot;
  evaluationResult: EvaluationResultSlot;
  integrity: {
    operationalStatus: "Data Integration";
    progressStage: "Planning";
    dataStatus: string;
    metricsStatus: string;
    validationStatus: string;
    evaluationStatus: string;
    evaluationPendingMessage: string;
  };
};

export const PROHIBITED_FICTIONAL_RESEARCH_NAMES = [
  "Macro Allocation",
  "Momentum Strategy",
  "Volatility Breakout",
  "Pairs Trading",
  "ETF Rotation",
  "Factor Timing",
  "Sector Momentum",
  "RSI Mean Reversion",
  "Factor Rotation",
  "Sector Rotation",
] as const;
