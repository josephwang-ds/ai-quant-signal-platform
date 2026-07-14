/**
 * Planned experiments for the canonical MA Crossover research.
 * Metrics remain null — Research Execution Engine only (PR-008B+).
 */

import {
  CANONICAL_RESEARCH_ID,
  getCanonicalResearchPackage,
} from "@/lib/canonicalMaCrossover";
import {
  EMPTY_EXPERIMENT_METRICS,
  type ExperimentType,
  type ResearchExperiment,
} from "@/types/experiment";

const METRICS_PENDING =
  "Metrics not calculated — real market data will be loaded by the Research Execution Engine.";

function toExperimentType(value: string): ExperimentType {
  const allowed: ExperimentType[] = [
    "Backtest",
    "Parameter Test",
    "Feature Test",
    "Regime Test",
    "Cost Test",
    "Model Comparison",
  ];
  return (allowed.find((item) => item === value) ?? "Backtest") as ExperimentType;
}

function buildPlannedExperiments(): ResearchExperiment[] {
  const pkg = getCanonicalResearchPackage();
  const def = pkg.definition;
  const documentedAt =
    pkg.timelineEvents[0]?.occurredAt ?? "2026-07-14T04:00:00.000Z";

  return pkg.plannedExperiments.map((planned) => ({
    id: planned.id,
    researchId: CANONICAL_RESEARCH_ID,
    name: planned.name,
    hypothesis: planned.hypothesis,
    status: "Designed",
    experimentType: toExperimentType(planned.experimentType),
    datasetOrSymbol: def.symbol,
    startDate: "2018-01-01",
    endDate: "latest-complete-trading-day",
    benchmark: def.benchmark,
    parameters: planned.parameters.map((parameter) => ({
      key: parameter.key,
      value: parameter.value,
    })),
    successCriteria: planned.successCriteria,
    falsificationCondition: planned.falsificationCondition,
    notes: planned.notes,
    owner: def.ownerLabel,
    createdAt: documentedAt,
    updatedAt: documentedAt,
    resultSummary: METRICS_PENDING,
    metrics: { ...EMPTY_EXPERIMENT_METRICS },
    linkedNotebookEntryIds: ["nb-ma-003"],
    relatedEvidenceIds: [],
    validationReadiness: "not_ready",
  }));
}

export const MOCK_EXPERIMENTS_BY_RESEARCH: Record<string, ResearchExperiment[]> = {
  [CANONICAL_RESEARCH_ID]: buildPlannedExperiments(),
};

function cloneExperiment(item: ResearchExperiment): ResearchExperiment {
  return {
    ...item,
    parameters: item.parameters.map((parameter) => ({ ...parameter })),
    linkedNotebookEntryIds: [...item.linkedNotebookEntryIds],
    relatedEvidenceIds: [...item.relatedEvidenceIds],
    metrics: { ...item.metrics },
  };
}

export function getMockExperiments(researchId: string): ResearchExperiment[] {
  return (MOCK_EXPERIMENTS_BY_RESEARCH[researchId] ?? []).map(cloneExperiment);
}

export function getMockExperimentById(
  researchId: string,
  experimentId: string
): ResearchExperiment | null {
  return getMockExperiments(researchId).find((item) => item.id === experimentId) ?? null;
}

export class MockExperimentError extends Error {
  constructor(message = "Unable to load research experiments.") {
    super(message);
    this.name = "MockExperimentError";
  }
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

function shouldForceMockError(): boolean {
  if (typeof window === "undefined") {
    return false;
  }
  return new URLSearchParams(window.location.search).get("mockError") === "1";
}

export async function loadMockExperiments(
  researchId: string,
  options?: { delayMs?: number }
): Promise<ResearchExperiment[]> {
  await delay(options?.delayMs ?? 340);
  if (shouldForceMockError()) {
    throw new MockExperimentError(
      "Mock experiment load failed. Remove mockError=1 from the URL or retry."
    );
  }
  return getMockExperiments(researchId);
}
