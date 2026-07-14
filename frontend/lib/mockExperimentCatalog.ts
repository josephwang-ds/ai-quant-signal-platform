/**
 * Research Experiments catalog — MA Crossover only.
 *
 * Market metrics are intentionally null. They must come from the
 * Research Execution Engine over real historical data — never invented here.
 *
 * TODO(backend): GET /api/research/{id}/experiments
 */

import type { ResearchExperiment } from "@/types/experiment";
import {
  CANONICAL_RESEARCH_ID,
  METRIC_PENDING_PLACEHOLDER,
} from "@/lib/mockResearchCatalog";

const MA_CROSSOVER_EXPERIMENTS: ResearchExperiment[] = [
  {
    id: "exp-ma-001",
    researchId: CANONICAL_RESEARCH_ID,
    name: "MA 20/60 baseline — SPY",
    hypothesis:
      "A 20/60 moving-average crossover on SPY, with a one-day lagged position and 0.001 cost per position change, outperforms SPY buy-and-hold after costs on 2018→latest complete trading day.",
    status: "Approved",
    experimentType: "Backtest",
    datasetOrSymbol: "SPY",
    startDate: "2018-01-01",
    endDate: "latest-complete-trading-day",
    benchmark: "SPY Buy & Hold",
    parameters: [
      { key: "short_ma", value: "20" },
      { key: "long_ma", value: "60" },
      { key: "position_lag_days", value: "1" },
      { key: "transaction_cost", value: "0.001" },
      { key: "risk_free_rate", value: "0" },
    ],
    successCriteria:
      "Net strategy beats buy-and-hold on risk-adjusted terms after costs on the full sample; OOS does not reverse the conclusion alone from in-sample noise.",
    falsificationCondition:
      "After costs, net Sharpe is not meaningfully better than buy-and-hold, or OOS and sensitivity collapse the apparent edge.",
    notes:
      "Canonical baseline for this workspace. Execution and metrics deferred to the Research Execution Engine.",
    owner: "Research Desk",
    createdAt: "2026-03-18T14:00:00.000Z",
    updatedAt: "2026-07-13T12:00:00.000Z",
    resultSummary: METRIC_PENDING_PLACEHOLDER,
    metrics: {
      sharpe: null,
      cagr: null,
      maxDrawdown: null,
      volatility: null,
      tradeCount: null,
      winRate: null,
      totalTransactionCost: null,
    },
    linkedNotebookEntryIds: ["nb-ma-003"],
    relatedEvidenceIds: ["ev-ma-protocol", "ev-ma-bt"],
    validationReadiness: "not_ready",
  },
];

export const MOCK_EXPERIMENTS_BY_RESEARCH: Record<string, ResearchExperiment[]> = {
  [CANONICAL_RESEARCH_ID]: MA_CROSSOVER_EXPERIMENTS,
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
  const found = getMockExperiments(researchId).find((item) => item.id === experimentId);
  return found ?? null;
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
