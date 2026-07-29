import type { Language } from "@/lib/i18n";
import {
  formatNullableText,
  formatPublishedTimestamp,
  formatRunType,
  NULLABLE_PLACEHOLDER,
  shortenRunId,
} from "@/lib/intelligence/display";
import type {
  ResearchSnapshotType,
  ResearchSummarySnapshot,
  SignalDirection,
  SignalRecord,
  SignalSnapshot,
  SnapshotReferenceDto,
  ValidationStatus,
} from "@/lib/intelligence/types";
import {
  SIGNAL_DIRECTIONS,
  VALIDATION_STATUSES,
} from "@/lib/intelligence/types";

export {
  formatNullableText,
  formatPublishedTimestamp,
  formatRunType,
  NULLABLE_PLACEHOLDER,
  shortenRunId,
};

export type WorkspaceView = "overview" | "signals" | "evidence" | "validation";

export const WORKSPACE_VIEWS: WorkspaceView[] = [
  "overview",
  "signals",
  "evidence",
  "validation",
];

export function resolveWorkspaceView(raw: string | null | undefined): WorkspaceView {
  if (raw === "signals" || raw === "evidence" || raw === "validation") {
    return raw;
  }
  return "overview";
}

export function workspaceViewHref(runId: string, view: WorkspaceView): string {
  const base = `/research/${encodeURIComponent(runId)}`;
  return view === "overview" ? base : `${base}?view=${view}`;
}

/**
 * Deterministic snapshot selection:
 * 1. exact supported snapshot_type
 * 2. newest created_at
 * 3. snapshot_id ascending tie-break
 * Never infers type from name / media type / schema substring.
 */
export function selectSnapshotReference(
  refs: SnapshotReferenceDto[],
  snapshotType: ResearchSnapshotType
): SnapshotReferenceDto | null {
  const matches = refs.filter((ref) => ref.snapshot_type === snapshotType);
  if (matches.length === 0) return null;
  return [...matches].sort((a, b) => {
    const aTime = Date.parse(a.created_at);
    const bTime = Date.parse(b.created_at);
    const aValid = Number.isFinite(aTime);
    const bValid = Number.isFinite(bTime);
    if (aValid && bValid && aTime !== bTime) {
      return bTime - aTime;
    }
    if (aValid && !bValid) return -1;
    if (!aValid && bValid) return 1;
    return a.snapshot_id.localeCompare(b.snapshot_id);
  })[0];
}

export function formatSignalDirection(
  direction: SignalDirection,
  language: Language = "en"
): string {
  const labels: Record<SignalDirection, { en: string; zh: string }> = {
    strong_negative: { en: "Strong negative", zh: "强负向" },
    negative: { en: "Negative", zh: "负向" },
    neutral: { en: "Neutral", zh: "中性" },
    positive: { en: "Positive", zh: "正向" },
    strong_positive: { en: "Strong positive", zh: "强正向" },
  };
  return labels[direction][language];
}

export function formatValidationStatus(
  status: ValidationStatus,
  language: Language = "en"
): string {
  const labels: Record<ValidationStatus, { en: string; zh: string }> = {
    not_started: { en: "Not started", zh: "未开始" },
    in_progress: { en: "In progress", zh: "进行中" },
    passed: { en: "Passed", zh: "通过" },
    failed: { en: "Failed", zh: "未通过" },
    unknown: { en: "Unknown", zh: "未知" },
  };
  return labels[status][language];
}

export function truncateChecksum(checksum: string, head = 6, tail = 6): string {
  if (checksum.length <= head + tail + 1) return checksum;
  return `${checksum.slice(0, head)}…${checksum.slice(-tail)}`;
}

export function formatByteSize(sizeBytes: number): string {
  if (!Number.isFinite(sizeBytes) || sizeBytes < 0) return NULLABLE_PLACEHOLDER;
  if (sizeBytes < 1024) return `${sizeBytes} B`;
  if (sizeBytes < 1024 * 1024) return `${(sizeBytes / 1024).toFixed(1)} KB`;
  return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** Map run-detail validation.ok to presentation Passed/Failed only. */
export function mapRunValidationOk(
  ok: boolean
): Extract<ValidationStatus, "passed" | "failed"> {
  return ok ? "passed" : "failed";
}

/**
 * Discrepancy only when summary status is passed/failed and differs from
 * run validation.ok mapped to passed/failed.
 */
export function hasSummaryValidationDiscrepancy(
  runValidationOk: boolean,
  summaryStatus: ValidationStatus
): boolean {
  if (summaryStatus !== "passed" && summaryStatus !== "failed") {
    return false;
  }
  return summaryStatus !== mapRunValidationOk(runValidationOk);
}

export function sortSignalRecords(signals: SignalRecord[]): SignalRecord[] {
  return [...signals].sort((a, b) => {
    const symbolCmp = a.symbol.localeCompare(b.symbol);
    if (symbolCmp !== 0) return symbolCmp;
    return a.signal_name.localeCompare(b.signal_name);
  });
}

export function countSignalsByDirection(
  signals: SignalRecord[]
): Record<SignalDirection, number> {
  const counts = Object.fromEntries(
    SIGNAL_DIRECTIONS.map((direction) => [direction, 0])
  ) as Record<SignalDirection, number>;
  for (const signal of signals) {
    counts[signal.direction] += 1;
  }
  return counts;
}

export function formatNullableNumber(
  value: number | null | undefined
): string {
  if (value == null || !Number.isFinite(value)) return NULLABLE_PLACEHOLDER;
  return String(value);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function isNullableString(value: unknown): value is string | null {
  return value === null || typeof value === "string";
}

function isNullableNumber(value: unknown): value is number | null {
  return value === null || (typeof value === "number" && !Number.isNaN(value));
}

function isFinding(value: unknown): boolean {
  if (!isRecord(value)) return false;
  if (typeof value.statement !== "string") return false;
  if (value.code != null && typeof value.code !== "string") return false;
  if (value.category != null && typeof value.category !== "string") return false;
  return true;
}

function isLimitation(value: unknown): boolean {
  if (!isRecord(value)) return false;
  if (typeof value.statement !== "string") return false;
  if (value.code != null && typeof value.code !== "string") return false;
  return true;
}

function isArtifactSummaryItem(value: unknown): boolean {
  if (!isRecord(value)) return false;
  return (
    typeof value.artifact_id === "string" &&
    typeof value.name === "string" &&
    typeof value.artifact_type === "string"
  );
}

function isProvenance(value: unknown): boolean {
  if (!isRecord(value)) return false;
  if (typeof value.builder !== "string") return false;
  if (!Array.isArray(value.source_artifact_ids)) return false;
  if (!value.source_artifact_ids.every((id) => typeof id === "string")) {
    return false;
  }
  if (value.notes != null && typeof value.notes !== "string") return false;
  return true;
}

/** Narrow runtime guard for ResearchSummarySnapshot (no Zod). */
export function isResearchSummarySnapshot(
  value: unknown
): value is ResearchSummarySnapshot {
  if (!isRecord(value)) return false;
  if (value.schema_version !== "research-summary-snapshot/v1") return false;
  if (typeof value.generated_at !== "string") return false;
  if (!isNullableString(value.as_of)) return false;
  if (!isNullableString(value.research_title)) return false;
  if (!isNullableString(value.research_objective)) return false;
  if (
    value.run_type != null &&
    value.run_type !== "TREND" &&
    value.run_type !== "FACTOR" &&
    value.run_type !== "MODEL" &&
    value.run_type !== "GENERAL"
  ) {
    return false;
  }
  if (!isNullableString(value.universe)) return false;
  if (!isNullableString(value.analysis_window)) return false;
  if (
    typeof value.validation_status !== "string" ||
    !VALIDATION_STATUSES.includes(value.validation_status as ValidationStatus)
  ) {
    return false;
  }
  if (!Array.isArray(value.key_findings) || !value.key_findings.every(isFinding)) {
    return false;
  }
  if (
    !Array.isArray(value.limitations) ||
    !value.limitations.every(isLimitation)
  ) {
    return false;
  }
  if (
    !Array.isArray(value.artifact_summary) ||
    !value.artifact_summary.every(isArtifactSummaryItem)
  ) {
    return false;
  }
  return isProvenance(value.provenance);
}

/** Narrow runtime guard for SignalSnapshot (no Zod). */
export function isSignalSnapshot(value: unknown): value is SignalSnapshot {
  if (!isRecord(value)) return false;
  if (value.schema_version !== "signal-snapshot/v1") return false;
  if (typeof value.generated_at !== "string") return false;
  if (!isNullableString(value.as_of)) return false;
  if (!isNullableString(value.universe)) return false;
  if (!isProvenance(value.provenance)) return false;
  if (!Array.isArray(value.signals)) return false;
  return value.signals.every((item) => {
    if (!isRecord(item)) return false;
    if (typeof item.symbol !== "string") return false;
    if (typeof item.signal_name !== "string") return false;
    if (
      typeof item.direction !== "string" ||
      !SIGNAL_DIRECTIONS.includes(item.direction as SignalDirection)
    ) {
      return false;
    }
    if (!isNullableNumber(item.score)) return false;
    if (!isNullableNumber(item.confidence)) return false;
    if (!isNullableString(item.horizon)) return false;
    if (
      !Array.isArray(item.evidence_artifact_ids) ||
      !item.evidence_artifact_ids.every((id) => typeof id === "string")
    ) {
      return false;
    }
    if (!isRecord(item.metadata)) return false;
    return true;
  });
}
