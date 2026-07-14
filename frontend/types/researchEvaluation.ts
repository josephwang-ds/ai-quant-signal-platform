/**
 * PR-010 Research Evaluation: the governance layer.
 *
 * Evaluation only summarizes PR-009 validation evidence. It never
 * recalculates strategy performance, and it never carries a confidence
 * score, quality rating, or investment recommendation.
 */

export type EvaluationStatus = "completed" | "incomplete" | "blocked";

export type EvidenceSummaryItem = {
  stage: string;
  label: string;
  status: string;
  summary: string;
};

export type EvidenceCoverage = {
  implemented_stage_count: number;
  completed_stage_count: number;
  coverage_percentage: number;
};

export type ResearchEvaluationProvenance = {
  research_id: string;
  validation_generated_at: string | null;
  market_data_provenance: Record<string, unknown> | null;
};

export type ResearchEvaluationResult = {
  research_id: string;
  evaluation_status: EvaluationStatus;
  evidence_summary: EvidenceSummaryItem[];
  evidence_coverage: EvidenceCoverage;
  completed_stages: string[];
  incomplete_stages: string[];
  unavailable_stages: string[];
  blockers: string[];
  limitations: string[];
  outstanding_evidence: string[];
  provenance: ResearchEvaluationProvenance;
  generated_at: string;
};

export type ResearchEvaluationRequestStatus = "idle" | "loading" | "ready" | "error";
