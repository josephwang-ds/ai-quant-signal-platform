export type ResearchDecisionOutcome = "advance" | "hold" | "reject";

export type ResearchDecisionRecord = {
  researchId: string;
  outcome: ResearchDecisionOutcome;
  rationale: string;
  decidedAt: string;
};

export const RESEARCH_DECISION_STORAGE_KEY =
  "quant.research.decision-records.v1";

type DecisionRecordMap = Record<string, ResearchDecisionRecord>;

function readAll(): DecisionRecordMap {
  if (typeof window === "undefined") return {};
  try {
    const raw = window.localStorage.getItem(RESEARCH_DECISION_STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as unknown;
    return parsed && typeof parsed === "object"
      ? (parsed as DecisionRecordMap)
      : {};
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
  now?: string;
}): ResearchDecisionRecord {
  const rationale = input.rationale.trim();
  if (!rationale) {
    throw new Error("Decision rationale is required.");
  }
  const record: ResearchDecisionRecord = {
    researchId: input.researchId,
    outcome: input.outcome,
    rationale,
    decidedAt: input.now ?? new Date().toISOString(),
  };
  writeAll({ ...readAll(), [input.researchId]: record });
  return record;
}
