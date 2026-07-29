export const RESEARCH_RUN_STATUSES = [
  "CREATED",
  "RUNNING",
  "VALIDATED",
  "PUBLISHED",
  "FAILED",
  "ARCHIVED",
] as const;

export const RESEARCH_RUN_TYPES = ["TREND", "FACTOR", "MODEL", "GENERAL"] as const;

export const RESEARCH_ARTIFACT_TYPES = [
  "reproducibility_manifest",
  "data_validation_report",
  "factor_metrics",
  "factor_report",
  "model_evaluation",
  "prediction_table",
  "feature_importance",
  "validation_report",
  "generic_json",
  "generic_parquet",
] as const;

export const RESEARCH_SNAPSHOT_TYPES = ["research_summary", "signal"] as const;

export const VALIDATION_STATUSES = [
  "not_started",
  "in_progress",
  "passed",
  "failed",
  "unknown",
] as const;

export const SIGNAL_DIRECTIONS = [
  "strong_negative",
  "negative",
  "neutral",
  "positive",
  "strong_positive",
] as const;

export type ResearchRunStatus = (typeof RESEARCH_RUN_STATUSES)[number];
export type ResearchRunType = (typeof RESEARCH_RUN_TYPES)[number];
export type ResearchArtifactType = (typeof RESEARCH_ARTIFACT_TYPES)[number];
export type ResearchSnapshotType = (typeof RESEARCH_SNAPSHOT_TYPES)[number];
export type ValidationStatus = (typeof VALIDATION_STATUSES)[number];
export type SignalDirection = (typeof SIGNAL_DIRECTIONS)[number];

export type IntelligenceApiErrorDetail = {
  error_code: string;
  message: string;
  run_id?: string | null;
  resource_id?: string | null;
};

export type IntelligenceApiErrorResponse = {
  detail: IntelligenceApiErrorDetail;
};

export type ArtifactReferenceDto = {
  artifact_id: string;
  name: string;
  artifact_type: ResearchArtifactType;
  schema_version: string;
  media_type: string | null;
  checksum_algorithm: string;
  checksum: string;
  size_bytes: number;
  row_count: number | null;
  created_at: string;
};

export type SnapshotReferenceDto = {
  snapshot_id: string;
  name: string;
  snapshot_type: ResearchSnapshotType;
  schema_version: string;
  media_type: string | null;
  checksum_algorithm: string;
  checksum: string;
  size_bytes: number;
  created_at: string;
  as_of: string | null;
  source_artifact_ids: string[];
};

export type ValidationRecordDto = {
  ok: boolean;
  checks: string[];
};

export type ResearchRunSummaryDto = {
  run_id: string;
  run_type: ResearchRunType;
  status: ResearchRunStatus;
  created_at: string;
  updated_at: string;
  published_at: string | null;
  universe: string | null;
  dataset_version: string | null;
  feature_version: string | null;
  model_version: string | null;
  git_commit: string | null;
  artifact_count: number;
  snapshot_count: number;
};

export type ResearchRunDetailDto = ResearchRunSummaryDto & {
  generator: string | null;
  environment: string | null;
  random_seed: number | null;
  training_window: string | null;
  prediction_window: string | null;
  notes: string | null;
  validation: ValidationRecordDto;
  errors: string[];
  artifacts: ArtifactReferenceDto[];
  snapshots: SnapshotReferenceDto[];
};

export type RunListDto = {
  items: ResearchRunSummaryDto[];
  count: number;
};

export type ArtifactListDto = {
  run_id: string;
  items: ArtifactReferenceDto[];
  count: number;
};

export type SnapshotListDto = {
  run_id: string;
  items: SnapshotReferenceDto[];
  count: number;
};

export type SnapshotFinding = {
  code: string | null;
  statement: string;
  category: string | null;
};

export type SnapshotLimitation = {
  code: string | null;
  statement: string;
};

export type ArtifactSummaryItem = {
  artifact_id: string;
  name: string;
  artifact_type: string;
};

export type SnapshotContentProvenance = {
  source_artifact_ids: string[];
  builder: string;
  notes: string | null;
};

export type ResearchSummarySnapshot = {
  schema_version: "research-summary-snapshot/v1";
  generated_at: string;
  as_of: string | null;
  research_title: string | null;
  research_objective: string | null;
  run_type: ResearchRunType | null;
  universe: string | null;
  analysis_window: string | null;
  validation_status: ValidationStatus;
  key_findings: SnapshotFinding[];
  limitations: SnapshotLimitation[];
  artifact_summary: ArtifactSummaryItem[];
  provenance: SnapshotContentProvenance;
};

export type SignalRecord = {
  symbol: string;
  signal_name: string;
  direction: SignalDirection;
  score: number | null;
  confidence: number | null;
  horizon: string | null;
  evidence_artifact_ids: string[];
  metadata: Record<string, unknown>;
};

export type SignalSnapshot = {
  schema_version: "signal-snapshot/v1";
  generated_at: string;
  as_of: string | null;
  universe: string | null;
  signals: SignalRecord[];
  provenance: SnapshotContentProvenance;
};

export type SnapshotContentDto = {
  run_id: string;
  reference: SnapshotReferenceDto;
  content: ResearchSummarySnapshot | SignalSnapshot;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

export function isIntelligenceApiErrorResponse(
  value: unknown
): value is IntelligenceApiErrorResponse {
  if (!isRecord(value) || !isRecord(value.detail)) {
    return false;
  }
  return (
    typeof value.detail.error_code === "string" &&
    typeof value.detail.message === "string" &&
    (value.detail.run_id == null || typeof value.detail.run_id === "string") &&
    (value.detail.resource_id == null || typeof value.detail.resource_id === "string")
  );
}
