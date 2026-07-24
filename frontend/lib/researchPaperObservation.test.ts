import { beforeEach, describe, expect, it } from "vitest";
import {
  addPaperObservationEntry,
  completePaperObservationSession,
  getPaperObservationSession,
  PAPER_OBSERVATION_STORAGE_KEY,
  startPaperObservationSession,
} from "@/lib/researchPaperObservation";

describe("paper observation records", () => {
  beforeEach(() => {
    window.localStorage.removeItem(PAPER_OBSERVATION_STORAGE_KEY);
  });

  it("persists a bounded observation plan without fabricating trades", () => {
    const session = startPaperObservationSession({
      researchId: "study-1",
      cadence: "weekly",
      minimumDays: 30,
      exitCriteria: " Stop if the benchmark gap widens for two reviews. ",
      now: "2026-07-24T08:00:00.000Z",
    });

    expect(session.status).toBe("active");
    expect(session.exitCriteria).toBe(
      "Stop if the benchmark gap widens for two reviews."
    );
    expect(getPaperObservationSession("study-1")).toEqual(session);
    expect(session).not.toHaveProperty("pnl");
    expect(session).not.toHaveProperty("orders");
  });

  it("appends human notes and completes the session", () => {
    startPaperObservationSession({
      researchId: "study-1",
      cadence: "daily",
      minimumDays: 5,
      exitCriteria: "Review after five sessions.",
      now: "2026-07-24T08:00:00.000Z",
    });

    const withEntry = addPaperObservationEntry({
      researchId: "study-1",
      note: " Signal stayed flat during the sell-off. ",
      now: "2026-07-25T08:00:00.000Z",
    });
    expect(withEntry.entries[0].note).toBe(
      "Signal stayed flat during the sell-off."
    );

    const completed = completePaperObservationSession(
      "study-1",
      "2026-07-30T08:00:00.000Z"
    );
    expect(completed.status).toBe("completed");
    expect(completed.completedAt).toBe("2026-07-30T08:00:00.000Z");
    expect(completed.entries).toHaveLength(1);
  });
});
