import { describe, expect, it } from "vitest";
import {
  getCurrentLibraryStage,
  getLibraryLifecycleProgress,
  getLibraryRecentActivity,
  selectContinueResearch,
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
    expect(progress.completed).toHaveLength(7);
    expect(progress.current).toBeNull();
  });

  it("reuses canonical timeline activity and invents none for unknown ids", () => {
    const canonical = getLibraryRecentActivity(CANONICAL_RESEARCH_ID);
    expect(canonical.length).toBeGreaterThan(0);
    expect(getLibraryRecentActivity("unknown-research")).toEqual([]);
    expect(getLibraryRecentActivity(null)).toEqual([]);
  });

  it("uses the real mock catalog without fabricating projects", () => {
    const projects = getMockResearchProjects();
    expect(projects.length).toBe(1);
    expect(projects[0].id).toBe(CANONICAL_RESEARCH_ID);
    expect(selectContinueResearch(projects)?.id).toBe(CANONICAL_RESEARCH_ID);
  });
});
