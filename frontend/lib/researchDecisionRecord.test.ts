import { beforeEach, describe, expect, it } from "vitest";
import {
  getResearchDecisionHistory,
  getResearchDecisionRecord,
  RESEARCH_DECISION_STORAGE_KEY,
  saveResearchDecisionRecord,
} from "@/lib/researchDecisionRecord";

describe("research decision records", () => {
  beforeEach(() => {
    window.localStorage.removeItem(RESEARCH_DECISION_STORAGE_KEY);
  });

  it("persists a human-authored outcome and rationale", () => {
    const record = saveResearchDecisionRecord({
      researchId: "study-1",
      outcome: "hold",
      rationale: " Wait for data-quality remediation. ",
      now: "2026-07-24T09:00:00.000Z",
    });

    expect(record.rationale).toBe("Wait for data-quality remediation.");
    expect(getResearchDecisionRecord("study-1")).toEqual(record);
  });

  it("rejects empty rationale", () => {
    expect(() =>
      saveResearchDecisionRecord({
        researchId: "study-1",
        outcome: "promote",
        rationale: "   ",
      })
    ).toThrow("Decision rationale is required.");
  });

  it("appends evidence-snapshot decisions instead of overwriting history", () => {
    saveResearchDecisionRecord({
      researchId: "study-history",
      outcome: "hold",
      rationale: "First evidence snapshot is incomplete.",
      evidenceSnapshotReference: "snapshot-one",
      now: "2026-07-24T09:00:00.000Z",
    });
    const latest = saveResearchDecisionRecord({
      researchId: "study-history",
      outcome: "reject",
      rationale: "A later core criterion failed.",
      evidenceSnapshotReference: "snapshot-two",
      benchmarkVerdict: "fail",
      reviewer: "Research lead",
      now: "2026-07-24T10:00:00.000Z",
    });

    expect(getResearchDecisionHistory("study-history")).toHaveLength(2);
    expect(getResearchDecisionRecord("study-history")).toEqual(latest);
    expect(latest.reviewer).toBe("Research lead");
    expect(latest.benchmarkVerdict).toBe("fail");
  });
});
