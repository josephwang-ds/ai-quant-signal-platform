/**
 * Research Workspace catalog — one canonical project only.
 *
 * Authenticity over quantity: inventing multiple unfinished “projects”
 * is forbidden. Market-derived metrics stay null until the Research
 * Execution Engine loads real historical data (separate PR).
 *
 * TODO(backend): 替换为 GET /api/research 与 GET /api/research/{id}。
 */

import {
  toResearchListItem,
  type ResearchDetail,
  type ResearchListItem,
} from "@/types/research";

/** Canonical Research Workspace project id. */
export const CANONICAL_RESEARCH_ID = "rs-ma-crossover-001";

export const METRIC_PENDING_PLACEHOLDER =
  "Real market data will be loaded by the Research Execution Engine";

export const MOCK_RESEARCH_DETAILS: ResearchDetail[] = [
  {
    id: CANONICAL_RESEARCH_ID,
    name: "MA Crossover Research",
    researchQuestion:
      "Does a simple MA20/MA60 crossover outperform buy-and-hold after transaction costs?",
    status: "Running",
    currentStage: "Running",
    confidenceScore: null,
    owner: "Research Desk",
    tags: ["ma-crossover", "SPY", "trend-following"],
    createdAt: "2026-03-12T09:20:00.000Z",
    updatedAt: "2026-07-13T12:00:00.000Z",
    experimentCount: 1,
    lastValidation:
      "Pending — real market data will be loaded by the Research Execution Engine",
    currentRecommendation:
      "Design and document the MA20/MA60 protocol; do not claim performance until execution results exist.",
    hypothesis:
      "A 20/60 moving-average crossover on SPY, with positions lagged by one trading day and a 0.001 transaction cost on position changes, can improve risk-adjusted returns versus SPY buy-and-hold after costs.",
    researchObjective:
      "Run one reproducible, cost-aware historical evaluation of MA20/MA60 on SPY versus buy-and-hold, with chronological out-of-sample and sensitivity checks — without inventing metrics in the UI.",
    researchSummary:
      "This workspace holds a single end-to-end research lifecycle for MA Crossover on SPY. Strategy narrative and protocol metadata are local. Sharpe, CAGR, drawdown, trade statistics, validation outcomes, and evaluation scores are not fabricated here; they require the Research Execution Engine.",
    evidenceSummary:
      "Evidence packages are scaffolded only. Quantitative evidence will be produced from real historical prices by the Research Execution Engine — not hardcoded.",
    validationSummary:
      "Validation stages (historical backtest, benchmark comparison, chronological OOS, sensitivity, transaction-cost review, data quality) are planned. Pass/fail will derive from calculated series, not mock gates.",
    keyStrengths: [
      "Single clear research question and falsification criteria",
      "Explicit instrument (SPY) and benchmark (SPY buy-and-hold)",
      "Protocol parameters documented before execution",
    ],
    knownWeaknesses: [
      "No calculated metrics until the Research Execution Engine runs",
      "Single-asset demo — not a cross-sectional study",
      "Yahoo/research-grade history is not an exchange-grade feed",
    ],
    openQuestions: [
      "Does MA20/MA60 beat SPY buy-and-hold after 0.001 costs on the full sample?",
      "Does the chronological OOS window preserve the sign of net expectancy?",
      "How fragile is the edge across a bounded short/long MA grid?",
    ],
    nextActions: [
      "Keep protocol parameters frozen (MA 20/60, lag 1 day, cost 0.001)",
      "Connect Research Execution Engine for real historical metrics",
      "Review calculated validation before any Evaluation recommendation",
    ],
    evidenceItems: [
      {
        id: "ev-ma-protocol",
        label: "Protocol defined",
        status: "completed",
        result:
          "MA20/MA60 on SPY; position = signal lagged 1 day; cost 0.001 on position change; benchmark SPY buy-and-hold",
      },
      {
        id: "ev-ma-bt",
        label: "Historical backtest",
        status: "pending",
        result: METRIC_PENDING_PLACEHOLDER,
      },
      {
        id: "ev-ma-bench",
        label: "Benchmark comparison",
        status: "pending",
        result: METRIC_PENDING_PLACEHOLDER,
      },
      {
        id: "ev-ma-oos",
        label: "Out-of-sample validation",
        status: "pending",
        result: METRIC_PENDING_PLACEHOLDER,
      },
      {
        id: "ev-ma-sens",
        label: "Parameter sensitivity",
        status: "pending",
        result: METRIC_PENDING_PLACEHOLDER,
      },
      {
        id: "ev-ma-cost",
        label: "Transaction-cost review",
        status: "pending",
        result: METRIC_PENDING_PLACEHOLDER,
      },
    ],
  },
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
  }));
}

export function getMockResearchProjects(): ResearchListItem[] {
  return getMockResearchDetails().map(toResearchListItem);
}

export function getMockResearchById(researchId: string): ResearchDetail | null {
  const found = MOCK_RESEARCH_DETAILS.find((item) => item.id === researchId);
  if (!found) {
    return null;
  }
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
