import { describe, expect, it } from "vitest";
import {
  buildEvaluationOverview,
  buildPaperTradingRuleChecks,
  computeResearchConfidence,
  deriveConfidenceLevel,
  deriveDecisionReadiness,
  filterEvaluationDimensions,
  getEvaluationWeightsTotal,
} from "@/lib/researchEvaluation";
import { getMockEvaluation } from "@/lib/mockEvaluationCatalog";
import { EVALUATION_DIMENSION_WEIGHTS } from "@/types/evaluation";

describe("evaluation weights", () => {
  it("totals 100", () => {
    expect(getEvaluationWeightsTotal()).toBe(100);
    const sum = Object.values(EVALUATION_DIMENSION_WEIGHTS).reduce(
      (acc, weight) => acc + weight,
      0
    );
    expect(sum).toBe(100);
  });
});

describe("computeResearchConfidence", () => {
  it("derives overall score from dimension values for momentum", () => {
    const snapshot = getMockEvaluation("rs-momentum-001");
    expect(snapshot).not.toBeNull();
    const score = computeResearchConfidence(snapshot!.dimensions);
    expect(score).toBe(81);
    expect(score).toBeGreaterThanOrEqual(78);
    expect(score).toBeLessThanOrEqual(84);

    const manual = Math.round(
      snapshot!.dimensions.reduce(
        (sum, dimension) => sum + (dimension.score * dimension.weight) / 100,
        0
      )
    );
    expect(score).toBe(manual);
  });

  it("maps confidence levels", () => {
    expect(deriveConfidenceLevel(95)).toBe("High");
    expect(deriveConfidenceLevel(82)).toBe("Moderate");
    expect(deriveConfidenceLevel(70)).toBe("Low");
    expect(deriveConfidenceLevel(40)).toBe("Insufficient Evidence");
  });
});

describe("deriveDecisionReadiness", () => {
  it("returns Continue Validation for the momentum demo story", () => {
    const snapshot = getMockEvaluation("rs-momentum-001")!;
    const score = computeResearchConfidence(snapshot.dimensions);
    expect(deriveDecisionReadiness(snapshot, score)).toBe("Continue Validation");
  });

  it("critical blocker prevents paper-trading readiness", () => {
    const snapshot = getMockEvaluation("rs-momentum-001")!;
    const score = computeResearchConfidence(snapshot.dimensions);
    const rules = buildPaperTradingRuleChecks(snapshot, score);
    expect(rules.find((rule) => rule.id === "rule-stress")?.passed).toBe(false);
    expect(rules.find((rule) => rule.id === "rule-blocker")?.passed).toBe(false);
    expect(deriveDecisionReadiness(snapshot, score)).not.toBe(
      "Ready for Paper Trading"
    );
  });

  it("returns Ready for Paper Trading when all gates pass", () => {
    const snapshot = getMockEvaluation("rs-pairs-003")!;
    const score = computeResearchConfidence(snapshot.dimensions);
    expect(score).toBeGreaterThanOrEqual(85);
    expect(deriveDecisionReadiness(snapshot, score)).toBe(
      "Ready for Paper Trading"
    );
  });
});

describe("buildEvaluationOverview", () => {
  it("exposes derived confidence and recommendation", () => {
    const overview = buildEvaluationOverview(
      getMockEvaluation("rs-momentum-001")!
    );
    expect(overview.confidenceScore).toBe(81);
    expect(overview.confidenceLevel).toBe("Moderate");
    expect(overview.decisionReadiness).toBe("Continue Validation");
    expect(overview.blockerCount).toBeGreaterThan(0);
  });
});

describe("filterEvaluationDimensions", () => {
  it("filters by status", () => {
    const dimensions = getMockEvaluation("rs-momentum-001")!.dimensions;
    const failed = filterEvaluationDimensions(dimensions, {
      query: "",
      status: "Failed",
    });
    expect(failed).toHaveLength(1);
    expect(failed[0]?.key).toBe("stress_test_resilience");
  });
});
