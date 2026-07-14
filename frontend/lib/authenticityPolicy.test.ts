import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import {
  CANONICAL_MA_CROSSOVER,
  CANONICAL_RESEARCH_ID,
  getCanonicalResearchPackage,
} from "@/lib/canonicalMaCrossover";
import {
  getMockResearchById,
  getMockResearchProjects,
  MOCK_RESEARCH_DETAILS,
} from "@/lib/mockResearchCatalog";
import { getMockExperiments } from "@/lib/mockExperimentCatalog";
import { getMockNotebookEntries, getMockTimelineEvents } from "@/lib/mockNotebookCatalog";
import { PROHIBITED_FICTIONAL_RESEARCH_NAMES } from "@/types/canonicalResearch";
import { METRIC_NOT_CALCULATED } from "@/lib/researchExperiments";

function collectFrontendFixtureFiles(root: string): string[] {
  const out: string[] = [];
  function walk(dir: string) {
    for (const entry of readdirSync(dir)) {
      if (
        entry === "node_modules" ||
        entry === ".next" ||
        entry === "coverage" ||
        entry === "dist"
      ) {
        continue;
      }
      const full = join(dir, entry);
      const st = statSync(full);
      if (st.isDirectory()) {
        walk(full);
        continue;
      }
      if (
        /\.(ts|tsx)$/.test(entry) &&
        (full.includes(`${join("lib", "mock")}`) ||
          full.includes(`${join("lib", "canonical")}`))
      ) {
        out.push(full);
      }
    }
  }
  walk(root);
  return out;
}

describe("PR-008A authenticity — canonical research", () => {
  it("publishes exactly one MA Crossover research project", () => {
    const list = getMockResearchProjects();
    expect(list).toHaveLength(1);
    expect(list[0].id).toBe(CANONICAL_RESEARCH_ID);
    expect(list[0].name).toBe("MA Crossover Research");
    expect(list[0].configuration.symbol).toBe("SPY");
    expect(list[0].configuration.benchmark).toBe("SPY Buy & Hold");
    expect(list[0].status).toBe("Data Integration");
    expect(list[0].confidenceScore).toBeNull();
    expect(list[0].integrity.metricsStatus).toBe("Not Calculated");
    expect(list[0].integrity.validationStatus).toBe("Not Started");
    expect(list[0].integrity.evaluationStatus).toBe("Not Available");
  });

  it("keeps list/detail/notebook/experiments/validation/timeline on one id", () => {
    const detail = getMockResearchById(CANONICAL_RESEARCH_ID);
    expect(detail).not.toBeNull();
    expect(detail?.hypothesis).toContain("transaction costs");
    expect(getMockExperiments(CANONICAL_RESEARCH_ID).length).toBe(5);
    expect(
      getMockExperiments(CANONICAL_RESEARCH_ID).every(
        (item) => item.researchId === CANONICAL_RESEARCH_ID
      )
    ).toBe(true);
    expect(
      getMockNotebookEntries(CANONICAL_RESEARCH_ID).every(
        (item) => item.researchId === CANONICAL_RESEARCH_ID
      )
    ).toBe(true);
    expect(
      getMockTimelineEvents(CANONICAL_RESEARCH_ID).every(
        (item) => item.researchId === CANONICAL_RESEARCH_ID
      )
    ).toBe(true);
    expect(CANONICAL_MA_CROSSOVER.plannedValidationStages.every((s) =>
      ["not_started", "awaiting_data"].includes(s.status)
    )).toBe(true);
    expect(getCanonicalResearchPackage().runtimeMarketData).toBeNull();
    expect(getCanonicalResearchPackage().calculatedEvidence).toBeNull();
    expect(getCanonicalResearchPackage().evaluationResult).toBeNull();
  });

  it("does not expose invented performance metrics on planned experiments", () => {
    for (const experiment of getMockExperiments(CANONICAL_RESEARCH_ID)) {
      expect(experiment.status).toBe("Designed");
      expect(experiment.metrics.sharpe).toBeNull();
      expect(experiment.metrics.cagr).toBeNull();
      expect(experiment.metrics.maxDrawdown).toBeNull();
      expect(experiment.metrics.winRate).toBeNull();
      expect(experiment.resultSummary.toLowerCase()).toContain("not calculated");
    }
    expect(METRIC_NOT_CALCULATED).toBe("Not calculated");
  });

  it("keeps notebook as design notes without claimed completed performance", () => {
    const bodies = getMockNotebookEntries(CANONICAL_RESEARCH_ID)
      .map((entry) => `${entry.title}\n${entry.body}`)
      .join("\n")
      .toLowerCase();
    expect(bodies).toContain("research design notes");
    expect(bodies).not.toMatch(/oos sharpe|net sharpe \d|is sharpe/);
  });

  it("timeline contains only definition / methodology / data-integration events", () => {
    const titles = getMockTimelineEvents(CANONICAL_RESEARCH_ID).map((e) => e.title);
    expect(titles).toEqual(
      expect.arrayContaining([
        "Research Definition Created",
        "Research Methodology Documented",
        "Real Data Integration Planned",
      ])
    );
    expect(titles.join(" ")).not.toMatch(/ValidationPassed|ExperimentCompleted|StrategyPublished/i);
  });
});

describe("PR-008A authenticity — prohibited fictional titles", () => {
  it("scan research fixture modules for prohibited project names", () => {
    const frontendRoot = join(process.cwd());
    const files = collectFrontendFixtureFiles(frontendRoot);
    expect(files.length).toBeGreaterThan(0);

    const hits: string[] = [];
    for (const file of files) {
      const text = readFileSync(file, "utf8");
      for (const name of PROHIBITED_FICTIONAL_RESEARCH_NAMES) {
        if (text.includes(`"${name}"`) || text.includes(`'${name}'`)) {
          hits.push(`${file}: ${name}`);
        }
      }
    }
    expect(hits).toEqual([]);
    expect(MOCK_RESEARCH_DETAILS.map((item) => item.name)).toEqual([
      "MA Crossover Research",
    ]);
  });
});
