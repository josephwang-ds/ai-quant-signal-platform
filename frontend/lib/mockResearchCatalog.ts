/**
 * Research Workspace catalog — projections from the canonical MA Crossover package.
 *
 * TODO(backend): 替换为 GET /api/research 与 GET /api/research/{id}。
 */

import {
  CANONICAL_MA_CROSSOVER,
  CANONICAL_RESEARCH_ID,
  getCanonicalResearchPackage,
} from "@/lib/canonicalMaCrossover";
import {
  toResearchListItem,
  type ResearchDetail,
  type ResearchListItem,
} from "@/types/research";

export { CANONICAL_RESEARCH_ID };

function buildCanonicalDetail(): ResearchDetail {
  const pkg = getCanonicalResearchPackage();
  const { definition: def, integrity, plannedExperiments, plannedValidationStages } =
    pkg;

  return {
    id: def.id,
    name: def.name,
    researchQuestion: def.researchQuestion,
    status: integrity.operationalStatus,
    currentStage: integrity.progressStage,
    confidenceScore: null,
    owner: def.ownerLabel,
    tags: [...def.tags],
    createdAt: pkg.timelineEvents[0]?.occurredAt ?? "2026-07-14T04:00:00.000Z",
    updatedAt: pkg.timelineEvents[0]?.occurredAt ?? "2026-07-14T04:00:00.000Z",
    experimentCount: plannedExperiments.length,
    lastValidation: integrity.validationStatus,
    currentRecommendation: integrity.evaluationPendingMessage,
    integrity: {
      dataStatus: integrity.dataStatus,
      metricsStatus: integrity.metricsStatus,
      validationStatus: integrity.validationStatus,
      evaluationStatus: integrity.evaluationStatus,
      publicityLabel: def.publicityLabel,
      explanatoryText: def.explanatoryText,
      evaluationPendingMessage: integrity.evaluationPendingMessage,
    },
    configuration: {
      symbol: def.symbol,
      benchmark: def.benchmark,
      strategyName: def.strategyName,
      parameterLines: def.parameters.map(
        (parameter) => `${parameter.label}: ${parameter.value}`
      ),
      dataRequirements: [...def.dataRequirements],
    },
    hypothesis: def.hypothesis,
    researchObjective: def.researchObjective,
    researchSummary: def.explanatoryText,
    evidenceSummary:
      "No calculated evidence yet. Evidence packages will be produced by the Research Execution Engine from real historical prices.",
    validationSummary: `Validation status: ${integrity.validationStatus}. Stages remain Not Started or Awaiting Data until market data arrives.`,
    keyStrengths: [
      "Single clear research question and frozen protocol parameters",
      "Explicit SPY instrument and SPY buy-and-hold benchmark",
      "Separation of design metadata from calculated results",
    ],
    knownWeaknesses: [
      "No calculated metrics until real historical data is integrated",
      "Single-asset reference study — not a multi-strategy portfolio",
      "Provider-grade research data is not an exchange feed",
    ],
    openQuestions: [
      "Does MA20/MA60 beat SPY buy-and-hold after 0.001 costs on the planned window?",
      "Does chronological OOS preserve the sign of any apparent edge?",
      "How fragile is the protocol across a bounded short/long MA grid?",
    ],
    nextActions: [
      "Keep protocol parameters frozen until execution exists",
      "Integrate Research Execution Engine with real historical prices",
      "Populate validation before any Evaluation recommendation",
    ],
    evidenceItems: plannedValidationStages.map((stage) => ({
      id: stage.id,
      label: stage.name,
      status: "pending" as const,
      result: `${stage.status === "awaiting_data" ? "Awaiting Data" : "Not Started"} — ${stage.description}`,
    })),
  };
}

export const MOCK_RESEARCH_DETAILS: ResearchDetail[] = [buildCanonicalDetail()];

export function getMockResearchDetails(): ResearchDetail[] {
  return MOCK_RESEARCH_DETAILS.map((item) => ({
    ...item,
    tags: [...item.tags],
    keyStrengths: [...item.keyStrengths],
    knownWeaknesses: [...item.knownWeaknesses],
    openQuestions: [...item.openQuestions],
    nextActions: [...item.nextActions],
    evidenceItems: item.evidenceItems.map((evidence) => ({ ...evidence })),
    integrity: { ...item.integrity },
    configuration: {
      ...item.configuration,
      parameterLines: [...item.configuration.parameterLines],
      dataRequirements: [...item.configuration.dataRequirements],
    },
  }));
}

export function getMockResearchProjects(): ResearchListItem[] {
  return getMockResearchDetails().map(toResearchListItem);
}

export function getMockResearchById(researchId: string): ResearchDetail | null {
  return getMockResearchDetails().find((item) => item.id === researchId) ?? null;
}

export class MockResearchError extends Error {
  constructor(message = "Unable to load research.") {
    super(message);
    this.name = "MockResearchError";
  }
}

/** @deprecated Prefer MockResearchError — kept for list page compatibility. */
export class MockResearchListError extends MockResearchError {
  constructor(message = "Unable to load research projects.") {
    super(message);
    this.name = "MockResearchListError";
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

export async function loadMockResearchProjects(options?: {
  delayMs?: number;
}): Promise<ResearchListItem[]> {
  await delay(options?.delayMs ?? 280);
  if (shouldForceMockError()) {
    throw new MockResearchListError(
      "Mock research list failed. Remove mockError=1 from the URL or retry."
    );
  }
  return getMockResearchProjects();
}

export async function loadMockResearchById(
  researchId: string,
  options?: { delayMs?: number }
): Promise<ResearchDetail | null> {
  await delay(options?.delayMs ?? 280);
  if (shouldForceMockError()) {
    throw new MockResearchError(
      "Mock research detail failed. Remove mockError=1 from the URL or retry."
    );
  }
  return getMockResearchById(researchId);
}

export const MOCK_RESEARCH_PROJECTS: ResearchListItem[] =
  MOCK_RESEARCH_DETAILS.map(toResearchListItem);

/** Guarantees catalog remains keyed to the canonical package. */
export function assertCanonicalCatalog(): void {
  if (CANONICAL_MA_CROSSOVER.definition.id !== CANONICAL_RESEARCH_ID) {
    throw new Error("Canonical research id mismatch.");
  }
  if (MOCK_RESEARCH_DETAILS.length !== 1) {
    throw new Error("Public research catalog must contain exactly one project.");
  }
}
