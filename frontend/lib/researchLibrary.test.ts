import { describe, expect, it } from "vitest";
import {
  getCurrentLibraryStage,
  getLibraryLifecycleProgress,
  getLibraryProgressRatio,
  getLibraryRecentActivity,
  getLibraryRecentActivityForResearchIds,
  hasExecutableProtocol,
  getOverviewWorkflowProgress,
  getWorkspaceOverviewStats,
  overviewWorkflowTab,
  selectContinueResearch,
  selectGuidedReviewResearch,
} from "@/lib/researchLibrary";
import {
  CANONICAL_RESEARCH_ID,
  getMockResearchProjects,
} from "@/lib/mockResearchCatalog";
import type { ResearchListItem } from "@/types/research";

function item(
  overrides: Partial<ResearchListItem> & Pick<ResearchListItem, "id" | "name">
): ResearchListItem {
  return {
    researchQuestion: "q",
    status: "Draft",
    confidenceScore: null,
    owner: "owner",
    tags: [],
    createdAt: "2026-07-01T00:00:00.000Z",
    updatedAt: "2026-07-01T00:00:00.000Z",
    experimentCount: 0,
    evidenceSummary: "none",
    lastValidation: "Not Started",
    currentRecommendation: "pending",
    integrity: {
      dataStatus: "n",
      metricsStatus: "n",
      validationStatus: "n",
      evaluationStatus: "n",
      publicityLabel: "n",
      explanatoryText: "n",
      evaluationPendingMessage: "n",
    },
    configuration: {
      symbol: "SPY",
      benchmark: "SPY Buy & Hold",
      strategyName: "Moving Average Crossover",
      parameterLines: [],
      dataRequirements: [],
    },
    ...overrides,
  };
}

describe("researchLibrary", () => {
  it("selects the most recently updated research", () => {
    const continueItem = selectContinueResearch([
      item({ id: "a", name: "A", updatedAt: "2026-07-01T00:00:00.000Z" }),
      item({ id: "b", name: "B", updatedAt: "2026-07-10T00:00:00.000Z" }),
    ]);
    expect(continueItem?.id).toBe("b");
  });

  it("returns null continue target when the catalog is empty", () => {
    expect(selectContinueResearch([])).toBeNull();
  });

  it("keeps the guided review on the canonical study", () => {
    const canonical = item({
      id: CANONICAL_RESEARCH_ID,
      name: "Canonical",
      updatedAt: "2026-07-01T00:00:00.000Z",
    });
    const newerLocalStudy = item({
      id: "newer-local",
      name: "Newer local",
      updatedAt: "2026-07-20T00:00:00.000Z",
    });

    expect(
      selectGuidedReviewResearch(
        [newerLocalStudy, canonical],
        CANONICAL_RESEARCH_ID
      )?.id
    ).toBe(CANONICAL_RESEARCH_ID);
    expect(
      selectGuidedReviewResearch([newerLocalStudy], CANONICAL_RESEARCH_ID)?.id
    ).toBe("newer-local");
  });

  it("keeps legacy unconfigured drafts out of portfolio focus", () => {
    const configured = item({ id: "configured", name: "Configured" });
    const legacyDraft = item({
      id: "legacy-draft",
      name: "Legacy draft",
      configuration: {
        symbol: "—",
        benchmark: "—",
        strategyName: "Not configured",
        parameterLines: [],
        dataRequirements: [],
      },
    });

    expect(hasExecutableProtocol(configured)).toBe(true);
    expect(hasExecutableProtocol(legacyDraft)).toBe(false);
  });

  it("marks only completed lifecycle stages for Validated research", () => {
    const progress = getLibraryLifecycleProgress("Validated");
    expect(progress.completed).toEqual([
      "research",
      "experiment",
      "validation",
    ]);
    expect(progress.current).toBe("robustness");
    expect(getCurrentLibraryStage("Validated")).toBe("robustness");
  });

  it("marks every stage completed when Archived", () => {
    const progress = getLibraryLifecycleProgress("Archived");
    expect(progress.completed).toHaveLength(6);
    expect(progress.current).toBeNull();
  });

  it("reuses canonical timeline activity and invents none for unknown ids", () => {
    const canonical = getLibraryRecentActivity(CANONICAL_RESEARCH_ID);
    expect(canonical.length).toBeGreaterThan(0);
    expect(getLibraryRecentActivity("unknown-research")).toEqual([]);
    expect(getLibraryRecentActivity(null)).toEqual([]);
  });

  it("merges activity across research ids without fabricating events", () => {
    const merged = getLibraryRecentActivityForResearchIds([
      CANONICAL_RESEARCH_ID,
      "unknown-research",
    ]);
    expect(merged.length).toBe(
      getLibraryRecentActivity(CANONICAL_RESEARCH_ID).length
    );
  });

  it("maps operational status onto the 4-stage homepage workflow", () => {
    const validated = getOverviewWorkflowProgress("Validated");
    expect(validated.completed).toEqual(["research", "validation"]);
    expect(validated.current).toBe("risk_review");
    expect(overviewWorkflowTab("risk_review")).toBe("robustness");
  });

  it("computes progress ratio and workspace stats from real items only", () => {
    expect(getLibraryProgressRatio("Draft")).toBe(0);
    expect(getLibraryProgressRatio("Validated")).toBeCloseTo(3 / 6);
    expect(getLibraryProgressRatio("Archived")).toBe(1);

    const stats = getWorkspaceOverviewStats([
      item({ id: "a", name: "A", status: "Review", experimentCount: 2 }),
      item({
        id: "b",
        name: "B",
        status: "Paper Trading",
        experimentCount: 1,
      }),
    ]);
    expect(stats).toEqual({
      active: 2,
      inReview: 1,
      experiments: 3,
    });
  });

  it("uses the real mock catalog without fabricating projects", () => {
    const projects = getMockResearchProjects();
    expect(projects.length).toBe(1);
    expect(projects[0].id).toBe(CANONICAL_RESEARCH_ID);
    expect(selectContinueResearch(projects)?.id).toBe(CANONICAL_RESEARCH_ID);
  });
});
