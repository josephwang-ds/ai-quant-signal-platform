import { describe, expect, it } from "vitest";
import {
  buildValidationOverview,
  deriveValidationReadiness,
  filterValidationStages,
  getValidationStageById,
} from "@/lib/researchValidation";
import { getMockValidationPipeline } from "@/lib/mockValidationCatalog";
import type { ValidationStage } from "@/types/validation";

describe("deriveValidationReadiness", () => {
  it("returns Continue Validation for the momentum demo story", () => {
    const snapshot = getMockValidationPipeline("rs-momentum-001");
    expect(deriveValidationReadiness(snapshot.stages, snapshot.blockers)).toBe(
      "Continue Validation"
    );
  });

  it("returns Ready for Evaluation when all stages passed without blockers", () => {
    const stages: ValidationStage[] = getMockValidationPipeline(
      "rs-momentum-001"
    ).stages.map((stage) => ({
      ...stage,
      status: "Passed",
      warnings: [],
    }));
    expect(deriveValidationReadiness(stages, [])).toBe("Ready for Evaluation");
  });

  it("returns Blocked when evidence is thin and blockers prevent progress", () => {
    const snapshot = getMockValidationPipeline("rs-rsi-002");
    expect(deriveValidationReadiness(snapshot.stages, snapshot.blockers)).toBe(
      "Blocked"
    );
  });
});

describe("buildValidationOverview", () => {
  it("aggregates counts from the momentum pipeline", () => {
    const overview = buildValidationOverview(
      getMockValidationPipeline("rs-momentum-001")
    );
    expect(overview.passedCount).toBe(6);
    expect(overview.failedCount).toBe(1);
    expect(overview.inconclusiveCount).toBe(1);
    expect(overview.blockingCount).toBe(1);
    expect(overview.readiness).toBe("Continue Validation");
    expect(overview.overallStatus).toBe("Failed");
  });
});

describe("filterValidationStages", () => {
  it("filters by status and search query", () => {
    const stages = getMockValidationPipeline("rs-momentum-001").stages;
    const failed = filterValidationStages(stages, {
      query: "",
      status: "Failed",
    });
    expect(failed).toHaveLength(1);
    expect(failed[0]?.name).toBe("Stress Testing");

    const searched = filterValidationStages(stages, {
      query: "regime",
      status: "all",
    });
    expect(searched.some((stage) => stage.name === "Regime Analysis")).toBe(
      true
    );
  });
});

describe("getValidationStageById", () => {
  it("returns null for unknown ids", () => {
    const stages = getMockValidationPipeline("rs-momentum-001").stages;
    expect(getValidationStageById(stages, "missing")).toBeNull();
    expect(getValidationStageById(stages, "val-mom-stress")?.name).toBe(
      "Stress Testing"
    );
  });
});
