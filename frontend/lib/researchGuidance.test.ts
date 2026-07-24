import { beforeEach, describe, expect, it } from "vitest";
import {
  buildResearchGuidanceTemplate,
  buildAgentResearchDefinition,
  loadResearchGuidance,
  RESEARCH_GUIDANCE_STORAGE_KEY,
  saveResearchGuidance,
} from "@/lib/researchGuidance";
import {
  CANONICAL_LOW_VOL_FACTOR_RESEARCH_ID,
  CANONICAL_RESEARCH_ID,
  getMockResearchById,
} from "@/lib/mockResearchCatalog";

describe("research guidance templates", () => {
  beforeEach(() => {
    window.localStorage.removeItem(RESEARCH_GUIDANCE_STORAGE_KEY);
  });

  it("builds a falsifiable trend template with same-asset benchmark", () => {
    const research = getMockResearchById(CANONICAL_RESEARCH_ID)!;
    const template = buildResearchGuidanceTemplate(research);
    expect(template.nullHypothesis).toContain("does not produce");
    expect(template.primaryBenchmark).toContain("Buy and Hold");
    expect(template.requiredValidation).toContain(
      "Chronological out-of-sample validation"
    );
    expect(template.successCriteria.every((item) => item.active)).toBe(true);
    expect(
      template.successCriteria.every((item) => item.source === "template")
    ).toBe(true);
  });

  it("documents normalized Q5 direction for low volatility", () => {
    const research = getMockResearchById(
      CANONICAL_LOW_VOL_FACTOR_RESEARCH_ID
    )!;
    const template = buildResearchGuidanceTemplate(research);
    expect(template.mechanism).toContain("negates raw volatility");
    expect(template.primaryBenchmark).toBe("Equal-weight universe return");
  });

  it("persists user edits without overwriting them with a template", () => {
    const research = getMockResearchById(CANONICAL_RESEARCH_ID)!;
    const edited = {
      ...buildResearchGuidanceTemplate(research),
      researchQuestion: "My edited, falsifiable research question?",
    };
    saveResearchGuidance(research.id, edited);
    expect(loadResearchGuidance(research).researchQuestion).toBe(
      "My edited, falsifiable research question?"
    );
  });

  it("migrates legacy text criteria to inactive researcher-owned criteria", () => {
    const research = getMockResearchById(CANONICAL_RESEARCH_ID)!;
    window.localStorage.setItem(
      RESEARCH_GUIDANCE_STORAGE_KEY,
      JSON.stringify({
        [research.id]: {
          ...buildResearchGuidanceTemplate(research),
          successCriteria: ["Old unstructured criterion"],
        },
      })
    );
    const [criterion] = loadResearchGuidance(research).successCriteria;
    expect(criterion.active).toBe(false);
    expect(criterion.source).toBe("user");
    expect(criterion.threshold).toBeNull();
  });

  it("builds Agent input from the latest saved guidance and real run config", () => {
    const research = getMockResearchById(CANONICAL_RESEARCH_ID)!;
    const template = buildResearchGuidanceTemplate(research);
    saveResearchGuidance(research.id, {
      ...template,
      nullHypothesis: "Saved null hypothesis.",
      successCriteria: template.successCriteria.map((item, index) => ({
        ...item,
        active: index === 0,
      })),
    });

    const payload = buildAgentResearchDefinition(research);
    expect(payload.null_hypothesis).toBe("Saved null hypothesis.");
    expect(payload.run_configuration).toEqual(research.runConfiguration);
    expect(payload.success_criteria).toEqual([
      expect.objectContaining({
        metric: template.successCriteria[0].metric,
        active: true,
        status: "active",
      }),
    ]);
    expect(payload.outcome_metrics).toEqual([
      template.successCriteria[0].metric,
    ]);
  });
});
