/**
 * Research Notebook mock 目录（与 Research List / Detail 同源）。
 *
 * TODO(backend): GET /api/research/{id}/notebook
 * TODO(database): 当前无持久化；会话新增条目仅存于客户端状态。
 */

import type { NotebookEntry } from "@/types/notebook";
import type { ResearchTimelineEvent } from "@/types/notebook";

const MOMENTUM_NOTEBOOK: NotebookEntry[] = [
  {
    id: "nb-mom-001",
    researchId: "rs-momentum-001",
    entryType: "Observation",
    title: "Frame the research question",
    body: `## Scope\n\nWe need to test whether **12–1 month cross-sectional momentum** survives realistic costs on a liquid US equity universe.\n\n- Universe: top 500 by ADV\n- Costs: 8 bps round-trip baseline\n- Falsification: net Sharpe < 0.3 on holdout`,
    author: "A. Chen",
    createdAt: "2026-03-12T10:00:00.000Z",
    tags: ["scope", "question"],
  },
  {
    id: "nb-mom-002",
    researchId: "rs-momentum-001",
    entryType: "Hypothesis",
    title: "Primary momentum hypothesis",
    body: "After costs and a liquid-universe filter, 12–1 momentum retains **positive risk-adjusted expectancy** versus equal-weight and value benchmarks.",
    author: "A. Chen",
    createdAt: "2026-03-14T09:30:00.000Z",
    tags: ["hypothesis", "momentum"],
  },
  {
    id: "nb-mom-003",
    researchId: "rs-momentum-001",
    entryType: "Decision",
    title: "Approve first experiment grid",
    body: "Approved Experiment **EXP-MOM-001**: monthly rebalance, lookback 12–1, skip month, top decile long-only.\n\nHold sensitivity grid until baseline completes.",
    author: "A. Chen",
    createdAt: "2026-03-18T14:15:00.000Z",
    tags: ["experiment", "protocol"],
    relatedArtifact: {
      id: "exp-mom-001",
      label: "EXP-MOM-001 · Baseline backtest",
      kind: "experiment",
    },
  },
  {
    id: "nb-mom-004",
    researchId: "rs-momentum-001",
    entryType: "Observation",
    title: "Backtest observation — cost drag visible",
    body: `## In-sample backtest\n\n- Gross Sharpe **0.94** on 2010–2021\n- Net Sharpe **0.78** at 8 bps\n- Turnover ~180% annualized\n\nCost drag is material but edge remains positive on liquid names.`,
    author: "A. Chen",
    createdAt: "2026-04-02T11:20:00.000Z",
    tags: ["backtest", "costs"],
    relatedArtifact: {
      id: "ev-mom-bt",
      label: "Backtest completed",
      kind: "evidence",
    },
  },
  {
    id: "nb-mom-005",
    researchId: "rs-momentum-001",
    entryType: "Result",
    title: "Walk-forward fold 3 OOS result",
    body: "Fold 3/5 OOS net Sharpe **0.51**. 2022 regime attenuates returns but sign holds on liquidity-filtered universe.",
    author: "A. Chen",
    createdAt: "2026-06-20T16:45:00.000Z",
    tags: ["oos", "walk-forward"],
    relatedArtifact: {
      id: "ev-mom-oos",
      label: "Out-of-sample validation",
      kind: "validation",
    },
  },
  {
    id: "nb-mom-006",
    researchId: "rs-momentum-001",
    entryType: "Reflection",
    title: "Weakness — crowding proxy still heuristic",
    body: "Crowding adjustment uses a **heuristic liquidity rank** rather than a published crowding factor. Reviewers may challenge capacity claims until we add an explicit crowding dataset.",
    author: "A. Chen",
    createdAt: "2026-06-28T09:10:00.000Z",
    edited: true,
    updatedAt: "2026-06-29T08:00:00.000Z",
    tags: ["weakness", "capacity"],
  },
  {
    id: "nb-mom-007",
    researchId: "rs-momentum-001",
    entryType: "Action",
    title: "Freeze universe before fold 4",
    body: "Action: freeze equity universe definition and document exclusions **before** running walk-forward fold 4. No parameter changes until universe is version-pinned.",
    author: "A. Chen",
    createdAt: "2026-07-05T13:00:00.000Z",
    tags: ["next-action", "universe"],
  },
  {
    id: "nb-mom-008",
    researchId: "rs-momentum-001",
    entryType: "Reflection",
    title: "Current posture — continue with caution",
    body: "Evidence supports a **thin but positive** edge after costs. Confidence is medium until folds 4–5 complete and stress battery runs. Do not advance to Evaluation early.",
    author: "A. Chen",
    createdAt: "2026-07-10T14:00:00.000Z",
    tags: ["reflection", "confidence"],
  },
];

const RSI_NOTEBOOK: NotebookEntry[] = [
  {
    id: "nb-rsi-001",
    researchId: "rs-rsi-002",
    entryType: "Hypothesis",
    title: "RSI(14) oversold bounce",
    body: "RSI(14) < 30 on S&P 100 names yields positive 5-day expectancy after costs when avoiding earnings windows.",
    author: "M. Okonkwo",
    createdAt: "2026-02-05T10:00:00.000Z",
    tags: ["RSI", "mean-reversion"],
  },
  {
    id: "nb-rsi-002",
    researchId: "rs-rsi-002",
    entryType: "Result",
    title: "OOS Sharpe 0.41 — thin 2022 sample",
    body: "OOS validation completed with Sharpe **0.41**. 2022 subsample is thin; widen regime stress before Evaluation.",
    author: "M. Okonkwo",
    createdAt: "2026-07-01T15:30:00.000Z",
    tags: ["oos"],
    relatedArtifact: {
      id: "ev-rsi-oos",
      label: "Out-of-sample validation completed",
      kind: "validation",
    },
  },
  {
    id: "nb-rsi-003",
    researchId: "rs-rsi-002",
    entryType: "Decision",
    title: "Request risk review before paper",
    body: "Decision: route to Evaluation only after earnings-calendar stress test is unblocked.",
    author: "M. Okonkwo",
    createdAt: "2026-07-08T16:00:00.000Z",
    tags: ["governance"],
  },
];

const PAIRS_NOTEBOOK: NotebookEntry[] = [
  {
    id: "nb-pairs-001",
    researchId: "rs-pairs-003",
    entryType: "Result",
    title: "Holdout passed at 8 bps",
    body: "Pairs set passed holdout and cost stress. Cointegration break monitor prototype ready for paper book proposal.",
    author: "S. Patel",
    createdAt: "2026-06-15T11:00:00.000Z",
    tags: ["validated"],
    relatedArtifact: {
      id: "ev-pairs-oos",
      label: "Out-of-sample validation completed",
      kind: "validation",
    },
  },
  {
    id: "nb-pairs-002",
    researchId: "rs-pairs-003",
    entryType: "Action",
    title: "Submit Evaluation package",
    body: "Prepare limited paper book proposal with explicit kill criteria on cointegration breaks.",
    author: "S. Patel",
    createdAt: "2026-06-28T09:30:00.000Z",
    tags: ["evaluation"],
  },
];

const VOL_NOTEBOOK: NotebookEntry[] = [
  {
    id: "nb-vol-001",
    researchId: "rs-vol-004",
    entryType: "Reflection",
    title: "Paper day 47 — within gate",
    body: "Paper simulation day 47. Drawdown inside approved gate. Continue to day-90 governance checkpoint.",
    author: "J. Morales",
    createdAt: "2026-07-09T09:00:00.000Z",
    tags: ["paper", "monitoring"],
  },
];

const ETF_NOTEBOOK: NotebookEntry[] = [
  {
    id: "nb-etf-001",
    researchId: "rs-etf-005",
    entryType: "Observation",
    title: "Correlation cluster amber",
    body: "Monitoring flag: sector correlation cluster rising. Track for 10 sessions before escalating to Needs Review.",
    author: "L. Bergström",
    createdAt: "2026-07-07T17:00:00.000Z",
    tags: ["monitoring", "regime"],
  },
];

const FACTOR_NOTEBOOK: NotebookEntry[] = [
  {
    id: "nb-fac-001",
    researchId: "rs-factor-006",
    entryType: "Action",
    title: "Write falsification criteria",
    body: "Draft falsification criteria and pin factor definitions before any Approved Experiment.",
    author: "A. Chen",
    createdAt: "2026-07-06T12:00:00.000Z",
    tags: ["draft", "planning"],
  },
];

const MACRO_NOTEBOOK: NotebookEntry[] = [
  {
    id: "nb-mac-001",
    researchId: "rs-macro-007",
    entryType: "Observation",
    title: "CPI revision lag sensitivity open",
    body: "Lag specification materially changes 2010–2015 overlay results. Finish grid before synthesis.",
    author: "H. Nakamura",
    createdAt: "2026-07-11T07:30:00.000Z",
    tags: ["macro", "sensitivity"],
  },
  {
    id: "nb-mac-002",
    researchId: "rs-macro-007",
    entryType: "Action",
    title: "Complete lag robustness grid",
    body: "Action: lock vintage CPI series and complete lag robustness before starting synthesis.",
    author: "H. Nakamura",
    createdAt: "2026-07-11T08:00:00.000Z",
    tags: ["next-action"],
  },
];

const SECTOR_NOTEBOOK: NotebookEntry[] = [
  {
    id: "nb-sec-001",
    researchId: "rs-sector-008",
    entryType: "Result",
    title: "Capacity stress rejected edge",
    body: "Capacity stress decisive — edge disappears under realistic participation. Archive with published negative result.",
    author: "M. Okonkwo",
    createdAt: "2026-05-19T11:00:00.000Z",
    tags: ["archived", "negative-result"],
  },
];

export const MOCK_NOTEBOOK_BY_RESEARCH: Record<string, NotebookEntry[]> = {
  "rs-momentum-001": MOMENTUM_NOTEBOOK,
  "rs-rsi-002": RSI_NOTEBOOK,
  "rs-pairs-003": PAIRS_NOTEBOOK,
  "rs-vol-004": VOL_NOTEBOOK,
  "rs-etf-005": ETF_NOTEBOOK,
  "rs-factor-006": FACTOR_NOTEBOOK,
  "rs-macro-007": MACRO_NOTEBOOK,
  "rs-sector-008": SECTOR_NOTEBOOK,
};

const BASELINE_TIMELINE: ResearchTimelineEvent[] = [
  {
    id: "tl-mom-stage",
    researchId: "rs-momentum-001",
    occurredAt: "2026-03-12T09:20:00.000Z",
    title: "Research entered Running",
    summary: "Planning complete; baseline experiment grid approved.",
    kind: "stage_change",
  },
  {
    id: "tl-mom-bt",
    researchId: "rs-momentum-001",
    occurredAt: "2026-04-02T11:20:00.000Z",
    title: "Backtest evidence captured",
    summary: "IS Sharpe 0.78 net of 8 bps; cost drag documented.",
    kind: "validation",
  },
  {
    id: "tl-mom-oos",
    researchId: "rs-momentum-001",
    occurredAt: "2026-06-20T16:45:00.000Z",
    title: "Walk-forward fold 3 completed",
    summary: "OOS Sharpe 0.51; 2022 regime noted.",
    kind: "validation",
  },
];

export const MOCK_TIMELINE_BY_RESEARCH: Record<string, ResearchTimelineEvent[]> = {
  "rs-momentum-001": BASELINE_TIMELINE,
  "rs-rsi-002": [
    {
      id: "tl-rsi-review",
      researchId: "rs-rsi-002",
      occurredAt: "2026-07-08T16:40:00.000Z",
      title: "Research reviewed",
      summary: "Awaiting earnings-calendar stress before Evaluation.",
      kind: "stage_change",
    },
  ],
  "rs-pairs-003": [
    {
      id: "tl-pairs-validated",
      researchId: "rs-pairs-003",
      occurredAt: "2026-06-28T10:12:00.000Z",
      title: "Validation passed",
      summary: "Holdout + cost stress at 8 bps.",
      kind: "validation",
    },
  ],
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

/** 模拟异步 notebook 加载。 */
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
