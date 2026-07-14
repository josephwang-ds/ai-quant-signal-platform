import { describe, expect, it } from "vitest";
import {
  CANONICAL_RESEARCH_ID,
  getMockResearchById,
  getMockResearchProjects,
  MOCK_RESEARCH_DETAILS,
} from "@/lib/mockResearchCatalog";
import { getLifecycleStepState, resolveWorkspaceSection } from "@/lib/researchWorkspace";
import {
  mapLifecycleStatusToProgressStage,
  RESEARCH_WORKSPACE_SECTIONS,
} from "@/types/research";

describe("mock research catalog", () => {
  it("exposes exactly one canonical research project", () => {
    expect(MOCK_RESEARCH_DETAILS).toHaveLength(1);
    expect(MOCK_RESEARCH_DETAILS[0].id).toBe(CANONICAL_RESEARCH_ID);
    expect(MOCK_RESEARCH_DETAILS[0].name).toBe("MA Crossover Research");
  });

  it("keeps list and detail projections consistent by id", () => {
    const list = getMockResearchProjects();
    expect(list).toHaveLength(1);

    for (const item of list) {
      const detail = getMockResearchById(item.id);
      expect(detail).not.toBeNull();
      expect(detail?.name).toBe(item.name);
      expect(detail?.researchQuestion).toBe(item.researchQuestion);
      expect(detail?.status).toBe(item.status);
      expect(detail?.confidenceScore).toBe(item.confidenceScore);
      expect(detail?.currentRecommendation).toBe(item.currentRecommendation);
      expect(detail?.integrity.publicityLabel).toBe(item.integrity.publicityLabel);
    }
  });

  it("returns null for unknown research ids", () => {
    expect(getMockResearchById("does-not-exist")).toBeNull();
  });

  it("selects MA Crossover by route id without a confidence score", () => {
    const detail = getMockResearchById(CANONICAL_RESEARCH_ID);
    expect(detail?.confidenceScore).toBeNull();
    expect(detail?.status).toBe("Data Integration");
    expect(detail?.currentStage).toBe("Planning");
  });
});

describe("lifecycle progress helpers", () => {
  it("marks completed, current, and upcoming stages", () => {
    expect(getLifecycleStepState("Draft", "Running")).toBe("completed");
    expect(getLifecycleStepState("Planning", "Running")).toBe("completed");
    expect(getLifecycleStepState("Running", "Running")).toBe("current");
    expect(getLifecycleStepState("Synthesizing", "Running")).toBe("upcoming");
    expect(getLifecycleStepState("Closed", "Running")).toBe("upcoming");
  });

  it("maps list operational status onto Ch3 progress stages", () => {
    expect(mapLifecycleStatusToProgressStage("Draft")).toBe("Draft");
    expect(mapLifecycleStatusToProgressStage("Data Integration")).toBe("Planning");
    expect(mapLifecycleStatusToProgressStage("Running")).toBe("Running");
    expect(mapLifecycleStatusToProgressStage("Review")).toBe("Reviewed");
    expect(mapLifecycleStatusToProgressStage("Archived")).toBe("Closed");
  });
});

describe("workspace navigation model", () => {
  it("exposes the eight local sections", () => {
    expect(RESEARCH_WORKSPACE_SECTIONS).toEqual([
      "overview",
      "notebook",
      "experiments",
      "validation",
      "evaluation",
      "timeline",
      "files",
      "settings",
    ]);
  });

  it("resolves ?tab= with ?section= fallback", () => {
    expect(resolveWorkspaceSection("notebook", null)).toBe("notebook");
    expect(resolveWorkspaceSection(null, "notebook")).toBe("notebook");
    expect(resolveWorkspaceSection("timeline", "notebook")).toBe("timeline");
    expect(resolveWorkspaceSection(null, null)).toBe("overview");
  });
});
