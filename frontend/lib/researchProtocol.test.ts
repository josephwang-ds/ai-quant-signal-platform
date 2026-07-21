import { describe, expect, it } from "vitest";
import { getMockResearchById } from "@/lib/mockResearchCatalog";
import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";
import {
  buildResearchProtocolParts,
  formatResearchProtocolLine,
} from "@/lib/researchProtocol";

describe("researchProtocol", () => {
  it("formats the configured MA crossover protocol without invented values", () => {
    const research = getMockResearchById(CANONICAL_RESEARCH_ID);
    expect(research).not.toBeNull();

    const parts = buildResearchProtocolParts(research!, null, "en");
    const line = formatResearchProtocolLine(parts, "en");

    expect(line).toContain("SPY");
    expect(line).toContain("MA20/MA60");
    expect(line).not.toContain("repository");
  });
});
