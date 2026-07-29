import type { Language } from "@/lib/i18n";
import type {
  ResearchRunSummaryDto,
  ResearchRunType,
} from "@/lib/intelligence/types";

export const NULLABLE_PLACEHOLDER = "—";

const RUN_TYPE_LABELS: Record<
  ResearchRunType,
  { en: string; zh: string }
> = {
  TREND: { en: "Trend Research", zh: "趋势研究" },
  FACTOR: { en: "Factor Research", zh: "因子研究" },
  MODEL: { en: "Model Research", zh: "模型研究" },
  GENERAL: { en: "General Research", zh: "综合研究" },
};

/** Stable order for run-type filter options. */
export const RUN_TYPE_ORDER: ResearchRunType[] = [
  "TREND",
  "FACTOR",
  "MODEL",
  "GENERAL",
];

export function formatRunType(
  runType: ResearchRunType,
  language: Language = "en"
): string {
  return RUN_TYPE_LABELS[runType][language];
}

/**
 * Presentation-only title. Not a transport field or research identity.
 */
export function derivePublishedRunLabel(
  run: Pick<ResearchRunSummaryDto, "run_type" | "universe">,
  language: Language = "en"
): string {
  const typeLabel = formatRunType(run.run_type, language);
  const universe = summarizeUniverse(run.universe, 3);
  if (universe) {
    return `${typeLabel} · ${universe}`;
  }
  return typeLabel || (language === "zh" ? "已发布研究" : "Published Research");
}

export function summarizeUniverse(
  universe: string | null | undefined,
  maxSymbols = 3
): string | null {
  if (universe == null) return null;
  const cleaned = universe.trim();
  if (!cleaned) return null;

  const parts = cleaned
    .split(/[,|;]+/)
    .map((part) => part.trim())
    .filter(Boolean);

  if (parts.length <= 1) {
    return cleaned.length > 64 ? `${cleaned.slice(0, 61)}…` : cleaned;
  }

  if (parts.length <= maxSymbols) {
    return parts.join(", ");
  }

  const visible = parts.slice(0, maxSymbols).join(", ");
  return `${visible} +${parts.length - maxSymbols}`;
}

export function formatNullableText(
  value: string | null | undefined
): string {
  if (value == null || value.trim() === "") {
    return NULLABLE_PLACEHOLDER;
  }
  return value;
}

export function shortenRunId(runId: string, head = 12, tail = 8): string {
  if (runId.length <= head + tail + 1) return runId;
  return `${runId.slice(0, head)}…${runId.slice(-tail)}`;
}

export function formatPublishedTimestamp(
  value: string | null | undefined,
  language: Language = "en"
): { display: string; dateTime: string | null } {
  if (value == null || value.trim() === "") {
    return { display: NULLABLE_PLACEHOLDER, dateTime: null };
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return { display: NULLABLE_PLACEHOLDER, dateTime: null };
  }
  const display = date.toLocaleString(language === "zh" ? "zh-CN" : "en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZoneName: "short",
  });
  return { display, dateTime: date.toISOString() };
}

export function comparePublishedRuns(
  a: ResearchRunSummaryDto,
  b: ResearchRunSummaryDto
): number {
  const aTime = a.published_at ? Date.parse(a.published_at) : Number.NaN;
  const bTime = b.published_at ? Date.parse(b.published_at) : Number.NaN;
  const aValid = Number.isFinite(aTime);
  const bValid = Number.isFinite(bTime);

  if (aValid && bValid && aTime !== bTime) {
    return bTime - aTime;
  }
  if (aValid && !bValid) return -1;
  if (!aValid && bValid) return 1;
  return a.run_id.localeCompare(b.run_id);
}

export function sortPublishedRuns(
  runs: ResearchRunSummaryDto[]
): ResearchRunSummaryDto[] {
  return [...runs].sort(comparePublishedRuns);
}

/**
 * Defensive published-only filter. Backend list is already published-scoped;
 * unexpected statuses are dropped rather than promoted.
 */
export function filterPublishedOnly(
  runs: ResearchRunSummaryDto[]
): ResearchRunSummaryDto[] {
  return runs.filter((run) => run.status === "PUBLISHED");
}

export function distinctRunTypes(
  runs: ResearchRunSummaryDto[]
): ResearchRunType[] {
  const present = new Set(runs.map((run) => run.run_type));
  return RUN_TYPE_ORDER.filter((type) => present.has(type));
}
