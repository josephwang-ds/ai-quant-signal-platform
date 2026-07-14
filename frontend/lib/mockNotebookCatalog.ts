/**
 * Research Notebook + timeline — MA Crossover only.
 *
 * Narrative and decisions may be local. Numeric market results must not
 * be invented; refer readers to the Research Execution Engine instead.
 *
 * TODO(backend): GET /api/research/{id}/notebook
 */

import type { NotebookEntry, ResearchTimelineEvent } from "@/types/notebook";
import {
  CANONICAL_RESEARCH_ID,
  METRIC_PENDING_PLACEHOLDER,
} from "@/lib/mockResearchCatalog";

const MA_NOTEBOOK: NotebookEntry[] = [
  {
    id: "nb-ma-001",
    researchId: CANONICAL_RESEARCH_ID,
    entryType: "Observation",
    title: "Frame the research question",
    body: `## Scope\n\nTest whether a **simple MA20/MA60 crossover** on **SPY** outperforms **SPY buy-and-hold** after transaction costs.\n\n- Instrument: SPY\n- Benchmark: SPY Buy & Hold\n- Default window: 2018-01-01 → latest complete trading day\n- Cost: 0.001 per position change\n- No look-ahead: position = signal lagged one trading day`,
    author: "Research Desk",
    createdAt: "2026-03-12T10:00:00.000Z",
    tags: ["scope", "question", "SPY"],
  },
  {
    id: "nb-ma-002",
    researchId: CANONICAL_RESEARCH_ID,
    entryType: "Hypothesis",
    title: "Primary MA crossover hypothesis",
    body: "After a **0.001** cost on each position change and a **one-day lag**, MA20/MA60 on SPY retains a better risk-adjusted profile than buy-and-hold on the research window. This is a testable claim — not a performance guarantee.",
    author: "Research Desk",
    createdAt: "2026-03-14T09:30:00.000Z",
    tags: ["hypothesis", "ma-crossover"],
  },
  {
    id: "nb-ma-003",
    researchId: CANONICAL_RESEARCH_ID,
    entryType: "Decision",
    title: "Approve baseline experiment protocol",
    body: "Approved Experiment **exp-ma-001**: short MA **20**, long MA **60**, signal ∈ {0,1}, position = signal shifted by one trading day, cost **0.001** on Δposition.\n\nMarket metrics are **not** filled in this notebook. They will be produced by the Research Execution Engine from real historical prices.",
    author: "Research Desk",
    createdAt: "2026-03-18T14:15:00.000Z",
    tags: ["experiment", "protocol"],
    relatedArtifact: {
      id: "exp-ma-001",
      label: "exp-ma-001 · MA 20/60 baseline — SPY",
      kind: "experiment",
    },
  },
  {
    id: "nb-ma-004",
    researchId: CANONICAL_RESEARCH_ID,
    entryType: "Observation",
    title: "Metrics policy — no invented results",
    body: `## Policy\n\nDo **not** paste fictional Sharpe, CAGR, drawdown, trade counts, or OOS gates into this notebook.\n\nUntil execution runs: **${METRIC_PENDING_PLACEHOLDER}.**\n\nHistorical performance is not investment advice and is not a forecast of future returns.`,
    author: "Research Desk",
    createdAt: "2026-07-13T11:00:00.000Z",
    tags: ["policy", "authenticity"],
  },
  {
    id: "nb-ma-005",
    researchId: CANONICAL_RESEARCH_ID,
    entryType: "Action",
    title: "Next: Research Execution Engine",
    body: "Action: keep this workspace as the single reference lifecycle. Wire calculated backtest / validation / evaluation from the Research Execution Engine in a later PR — still without fabricating fallback metrics on provider failure.",
    author: "Research Desk",
    createdAt: "2026-07-13T12:00:00.000Z",
    tags: ["next-action", "execution"],
  },
];

export const MOCK_NOTEBOOK_BY_RESEARCH: Record<string, NotebookEntry[]> = {
  [CANONICAL_RESEARCH_ID]: MA_NOTEBOOK,
};

const MA_TIMELINE: ResearchTimelineEvent[] = [
  {
    id: "tl-ma-start",
    researchId: CANONICAL_RESEARCH_ID,
    occurredAt: "2026-03-12T09:20:00.000Z",
    title: "Research entered Running",
    summary: "MA Crossover on SPY framed; fictional sibling projects removed from the workspace.",
    kind: "stage_change",
  },
  {
    id: "tl-ma-protocol",
    researchId: CANONICAL_RESEARCH_ID,
    occurredAt: "2026-03-18T14:15:00.000Z",
    title: "Baseline experiment approved",
    summary: "exp-ma-001 protocol pinned (MA20/60, lag 1 day, cost 0.001). Metrics pending execution.",
    kind: "experiment",
  },
  {
    id: "tl-ma-policy",
    researchId: CANONICAL_RESEARCH_ID,
    occurredAt: "2026-07-13T11:00:00.000Z",
    title: "Authenticity policy recorded",
    summary: METRIC_PENDING_PLACEHOLDER,
    kind: "notebook_entry",
  },
];

export const MOCK_TIMELINE_BY_RESEARCH: Record<string, ResearchTimelineEvent[]> = {
  [CANONICAL_RESEARCH_ID]: MA_TIMELINE,
};

export function getMockNotebookEntries(researchId: string): NotebookEntry[] {
  const entries = MOCK_NOTEBOOK_BY_RESEARCH[researchId] ?? [];
  return entries.map((entry) => ({
    ...entry,
    tags: [...entry.tags],
    relatedArtifact: entry.relatedArtifact
      ? { ...entry.relatedArtifact }
      : undefined,
  }));
}

export function getMockTimelineEvents(researchId: string): ResearchTimelineEvent[] {
  const events = MOCK_TIMELINE_BY_RESEARCH[researchId] ?? [];
  return events.map((event) => ({ ...event }));
}

export class MockNotebookError extends Error {
  constructor(message = "Unable to load the research notebook.") {
    super(message);
    this.name = "MockNotebookError";
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

export async function loadMockNotebookEntries(
  researchId: string,
  options?: { delayMs?: number }
): Promise<NotebookEntry[]> {
  await delay(options?.delayMs ?? 320);
  if (shouldForceMockError()) {
    throw new MockNotebookError(
      "Mock notebook load failed. Remove mockError=1 from the URL or retry."
    );
  }
  return getMockNotebookEntries(researchId);
}
