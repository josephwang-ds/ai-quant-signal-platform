export type BenchmarkVerdict =
  | "pass"
  | "partial"
  | "fail"
  | "inconclusive"
  | "unavailable";

export type DeterministicCheckStatus =
  | "pass"
  | "fail"
  | "inconclusive"
  | "unavailable";

export type DeterministicEvidenceCheck = {
  check_id: string;
  name: string;
  status: DeterministicCheckStatus;
  observed_value: number | null;
  configured_threshold: number | null;
  threshold?: number | null;
  operator?: string;
  metric_unit?: string;
  explanation: string;
  evidence_source: string;
  severity: string;
  evidence_timestamp?: string | null;
};

export type BenchmarkEvaluation = {
  benchmark_type: string;
  primary_benchmark: string;
  why_appropriate: string;
  comparison_period: Record<string, string | number | boolean | null>;
  cost_assumption: string;
  risk_adjusted_method: string;
  ranking_convention?: {
    raw_direction: string;
    normalization: string;
    q5_meaning: string;
    q1_meaning: string;
  };
  configured_success_criteria: Record<string, number>;
  comparison: Record<string, number | boolean | null>;
  checks: DeterministicEvidenceCheck[];
  verdict: BenchmarkVerdict;
  rationale: string;
  passed_criteria?: string[];
  failed_criteria?: string[];
  inconclusive_criteria?: string[];
  unavailable_criteria?: string[];
  supporting_metrics?: Record<string, unknown>;
  cash_reference?: Record<string, string | number>;
};
