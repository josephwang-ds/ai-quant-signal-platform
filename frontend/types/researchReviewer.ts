export type ResearchReviewerAction =
  | "draft_definition"
  | "review_hypothesis"
  | "review_evidence"
  | "identify_missing_steps";

export type ResearchReviewerResponse<T> = {
  action: ResearchReviewerAction;
  provider: string;
  model: string;
  generated_at: string;
  evidence_snapshot_timestamp: string | null;
  result: T;
};

export type ReviewerProposedCriterion = {
  criterion_id: string;
  metric: string;
  operator: "gte" | "lte" | "gt" | "lt" | "positive" | "non_negative";
  threshold: null;
  severity: "core" | "supporting" | "guardrail";
  description: string;
  source: "ai_proposed";
  threshold_guidance: string;
  reason: string;
};

export type DraftResearchDefinitionResult = {
  research_question: string;
  hypothesis: string;
  null_hypothesis: string;
  mechanism: string;
  primary_benchmark: { name: string; reason: string };
  proposed_success_criteria: ReviewerProposedCriterion[];
  failure_criteria: Array<{ condition: string; reason: string }>;
  required_validation: string[];
  known_limitations: string[];
  clarifications_needed: string[];
};

export type HypothesisReviewResult = {
  is_testable: boolean;
  is_falsifiable: boolean;
  benchmark_is_defined: boolean;
  outcome_metrics_are_defined: boolean;
  strengths: string[];
  problems: string[];
  missing_elements: string[];
  suggested_revision: {
    research_question: string;
    hypothesis: string;
    null_hypothesis: string;
  };
  warnings: string[];
};

export type CompletionReviewResult = {
  readiness_summary: string;
  completed_items: string[];
  missing_items: string[];
  blocking_issues: string[];
  non_blocking_issues: string[];
  recommended_next_steps: string[];
};

export type EvidenceReviewResult = {
  executive_summary: string;
  hypothesis_assessment:
    | "supported"
    | "partially_supported"
    | "not_supported"
    | "inconclusive";
  benchmark_assessment: string;
  supporting_evidence: Array<{
    claim: string;
    evidence_reference: string;
  }>;
  contradicting_evidence: Array<{
    claim: string;
    evidence_reference: string;
  }>;
  robustness_concerns: string[];
  data_quality_concerns: string[];
  decision_considerations: string[];
  recommended_additional_validation: string[];
  limitations: string[];
};
