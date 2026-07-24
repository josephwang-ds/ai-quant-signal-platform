export type ResearchDecisionOutcome =
  | "promote"
  | "hold"
  | "reject"
  | "archive";

/** Legacy stored value mapped to promote on read. */
type LegacyDecisionOutcome = ResearchDecisionOutcome | "advance";

export type ResearchDecisionRecord = {
  researchId: string;
  outcome: ResearchDecisionOutcome;
  rationale: string;
  decidedAt: string;
  /** When calculated evidence was last observed (optional). */
  evidenceTimestamp: string | null;
  /** Human-selected metric summary / evidence references — not invented metrics. */
  evidenceSummary: string | null;
  reviewerNote: string | null;
};

export const RESEARCH_DECISION_STORAGE_KEY =
  "quant.research.decision-records.v1";

type DecisionRecordMap = Record<string, ResearchDecisionRecord>;

function normalizeOutcome(raw: unknown): ResearchDecisionOutcome | null {
  if (raw === "advance" || raw === "promote") return "promote";
  if (raw === "hold" || raw === "reject" || raw === "archive") return raw;
  return null;
}

function normalizeRecord(
  raw: Partial<ResearchDecisionRecord> & {
    outcome?: LegacyDecisionOutcome;
  }
): ResearchDecisionRecord | null {
  if (!raw || typeof raw.researchId !== "string") return null;
  const outcome = normalizeOutcome(raw.outcome);
  if (!outcome || typeof raw.rationale !== "string" || !raw.rationale.trim()) {
    return null;
  }
  return {
    researchId: raw.researchId,
    outcome,
    rationale: raw.rationale.trim(),
    decidedAt:
      typeof raw.decidedAt === "string"
        ? raw.decidedAt
        : new Date().toISOString(),
    evidenceTimestamp:
      typeof raw.evidenceTimestamp === "string" ? raw.evidenceTimestamp : null,
    evidenceSummary:
      typeof raw.evidenceSummary === "string" ? raw.evidenceSummary : null,
    reviewerNote:
      typeof raw.reviewerNote === "string" ? raw.reviewerNote : null,
  };
}

function readAll(): DecisionRecordMap {
  if (typeof window === "undefined") return {};
  try {
    const raw = window.localStorage.getItem(RESEARCH_DECISION_STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as unknown;
    if (!parsed || typeof parsed !== "object") return {};
    const out: DecisionRecordMap = {};
    for (const [key, value] of Object.entries(
      parsed as Record<string, unknown>
    )) {
      const normalized = normalizeRecord(
        value as Partial<ResearchDecisionRecord>
      );
      if (normalized) out[key] = normalized;
    }
    return out;
  } catch {
    return {};
  }
}

function writeAll(records: DecisionRecordMap): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(
    RESEARCH_DECISION_STORAGE_KEY,
    JSON.stringify(records)
  );
}

export function getResearchDecisionRecord(
  researchId: string
): ResearchDecisionRecord | null {
  return readAll()[researchId] ?? null;
}

export function saveResearchDecisionRecord(input: {
  researchId: string;
  outcome: ResearchDecisionOutcome;
  rationale: string;
  evidenceTimestamp?: string | null;
  evidenceSummary?: string | null;
  reviewerNote?: string | null;
  now?: string;
}): ResearchDecisionRecord {
  const rationale = input.rationale.trim();
  if (!rationale) {
    throw new Error("Decision rationale is required.");
  }
  const outcome = normalizeOutcome(input.outcome);
  if (!outcome) {
    throw new Error("Decision outcome is invalid.");
  }
  const record: ResearchDecisionRecord = {
    researchId: input.researchId,
    outcome,
    rationale,
    decidedAt: input.now ?? new Date().toISOString(),
    evidenceTimestamp: input.evidenceTimestamp?.trim() || null,
    evidenceSummary: input.evidenceSummary?.trim() || null,
    reviewerNote: input.reviewerNote?.trim() || null,
  };
  writeAll({ ...readAll(), [input.researchId]: record });
  return record;
}

export const RESEARCH_DECISION_OUTCOMES: ResearchDecisionOutcome[] = [
  "promote",
  "hold",
  "reject",
  "archive",
];
