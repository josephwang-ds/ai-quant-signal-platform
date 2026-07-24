/**
 * Research Workspace catalog — projections from canonical research packages.
 *
 * TODO(backend): 替换为 GET /api/research 与 GET /api/research/{id}。
 */

import {
  CANONICAL_MA_CROSSOVER,
  CANONICAL_RESEARCH_ID,
  getCanonicalResearchPackage,
} from "@/lib/canonicalMaCrossover";
import {
  CANONICAL_CROSS_SECTIONAL_FACTOR,
  CANONICAL_FACTOR_RESEARCH_ID,
  CANONICAL_FACTOR_RUN_CONFIGURATION,
  getCanonicalFactorResearchPackage,
} from "@/lib/canonicalCrossSectionalFactor";
import {
  toResearchListItem,
  type ResearchDetail,
  type ResearchListItem,
  type ResearchRunConfiguration,
} from "@/types/research";
import type { CanonicalResearchPackage } from "@/types/canonicalResearch";

export { CANONICAL_RESEARCH_ID, CANONICAL_FACTOR_RESEARCH_ID };

function buildDetailFromPackage(
  pkg: CanonicalResearchPackage,
  runConfiguration: ResearchRunConfiguration,
  extras: {
    keyStrengths: string[];
    knownWeaknesses: string[];
    openQuestions: string[];
    nextActions: string[];
  }
): ResearchDetail {
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
    runConfiguration,
    hypothesis: def.hypothesis,
    researchObjective: def.researchObjective,
    researchSummary: def.explanatoryText,
    evidenceSummary:
      "No calculated evidence yet. Evidence packages will be produced by the research validation engines from real historical prices.",
    validationSummary: `Validation status: ${integrity.validationStatus}. Stages remain Not Started or Awaiting Data until market data arrives.`,
    keyStrengths: extras.keyStrengths,
    knownWeaknesses: extras.knownWeaknesses,
    openQuestions: extras.openQuestions,
    nextActions: extras.nextActions,
    evidenceItems: plannedValidationStages.map((stage) => ({
      id: stage.id,
      label: stage.name,
      status: "pending" as const,
      result: `${stage.status === "awaiting_data" ? "Awaiting Data" : "Not Started"} — ${stage.description}`,
    })),
  };
}

function buildCanonicalMaDetail(): ResearchDetail {
  return buildDetailFromPackage(
    getCanonicalResearchPackage(),
    {
      templateId: "trend_following",
      symbol: CANONICAL_MA_CROSSOVER.definition.symbol,
      benchmark: CANONICAL_MA_CROSSOVER.definition.symbol,
      startDate: "2018-01-01",
      endDate: null,
      shortWindow: 20,
      longWindow: 60,
      transactionCost: 0.001,
      riskFreeRate: 0,
    },
    {
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
    }
  );
}

function buildCanonicalFactorDetail(): ResearchDetail {
  return buildDetailFromPackage(
    getCanonicalFactorResearchPackage(),
    { ...CANONICAL_FACTOR_RUN_CONFIGURATION },
    {
      keyStrengths: [
        "Factor validation framing — not a trading strategy",
        "Deterministic RankIC and equal-weight Q1–Q5 protocol",
        "Value factor explicitly deferred (Coming Soon)",
      ],
      knownWeaknesses: [
        "Sector-ETF universe is a demo cross-section, not a production equity book",
        "No fundamentals → Value unavailable in v1",
        "No portfolio optimization or risk model by design",
      ],
      openQuestions: [
        "Is mean RankIC for Momentum / Low Volatility distinguishable from zero?",
        "Does Q5−Q1 survive stated turnover costs?",
        "How stable is rolling IC across the sample?",
      ],
      nextActions: [
        "Run Factor Validation for Momentum and Low Volatility",
        "Review RankIC, ICIR, quantile, and long–short evidence before any decision",
        "Keep Value marked Coming Soon until a fundamentals panel exists",
      ],
    }
  );
}

export const MOCK_RESEARCH_DETAILS: ResearchDetail[] = [
  buildCanonicalMaDetail(),
  buildCanonicalFactorDetail(),
];

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
    runConfiguration: item.runConfiguration
      ? ({ ...item.runConfiguration } as ResearchRunConfiguration)
      : undefined,
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
    setTimeout(() => {
      resolve();
    }, ms);
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

/** Guarantees catalog remains keyed to the canonical packages. */
export function assertCanonicalCatalog(): void {
  if (CANONICAL_MA_CROSSOVER.definition.id !== CANONICAL_RESEARCH_ID) {
    throw new Error("Canonical research id mismatch.");
  }
  if (CANONICAL_CROSS_SECTIONAL_FACTOR.definition.id !== CANONICAL_FACTOR_RESEARCH_ID) {
    throw new Error("Canonical factor research id mismatch.");
  }
  if (MOCK_RESEARCH_DETAILS.length !== 2) {
    throw new Error(
      "Public research catalog must contain Trend Following and Cross-Sectional Factor studies."
    );
  }
}
