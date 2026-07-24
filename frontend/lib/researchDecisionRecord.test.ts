import { beforeEach, describe, expect, it } from "vitest";
import {
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
        outcome: "advance",
        rationale: "   ",
      })
    ).toThrow("Decision rationale is required.");
  });
});
