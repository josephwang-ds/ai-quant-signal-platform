/**
 * Research Experiments mock 目录（与 List / Detail / Notebook 同源）。
 *
 * TODO(backend): GET /api/research/{id}/experiments
 * TODO(database): 当前无持久化；会话新建仅存客户端状态。
 */

import type { ResearchExperiment } from "@/types/experiment";

const MOMENTUM_EXPERIMENTS: ResearchExperiment[] = [
  {
    id: "exp-mom-001",
    researchId: "rs-momentum-001",
    name: "MA 20/60 baseline",
    hypothesis:
      "A 20/60 moving-average crossover on liquid US equities retains positive expectancy after 8 bps costs versus buy-and-hold.",
    status: "Completed",
    experimentType: "Backtest",
    datasetOrSymbol: "US Large Cap Liquid Panel",
    startDate: "2010-01-01",
    endDate: "2021-12-31",
    benchmark: "Equal-weight buy & hold",
    parameters: [
      { key: "fast_ma", value: "20" },
      { key: "slow_ma", value: "60" },
      { key: "rebalance", value: "daily" },
      { key: "cost_bps", value: "8" },
    ],
    successCriteria: "Net Sharpe ≥ 0.5 and max DD better than benchmark by ≥ 2pp.",
    falsificationCondition: "Net Sharpe < 0.3 after costs on the liquid universe.",
    notes: "Baseline protocol version pinned as EXP-MOM-001.",
    owner: "A. Chen",
    createdAt: "2026-03-18T14:00:00.000Z",
    updatedAt: "2026-04-02T11:20:00.000Z",
    resultSummary:
      "IS net Sharpe 0.78; cost drag material but edge positive. Research demo only — not a performance guarantee.",
    metrics: {
      sharpe: 0.78,
      cagr: 0.092,
      maxDrawdown: -0.142,
      volatility: 0.118,
      tradeCount: 214,
      winRate: 0.54,
      totalTransactionCost: 8.0,
    },
    linkedNotebookEntryIds: ["nb-mom-003", "nb-mom-004"],
    relatedEvidenceIds: ["ev-mom-bt"],
    validationReadiness: "partial",
  },
  {
    id: "exp-mom-002",
    researchId: "rs-momentum-001",
    name: "MA 10/50 parameter variant",
    hypothesis:
      "Shortening the MA pair to 10/50 improves responsiveness without destroying risk-adjusted returns after costs.",
    status: "Completed",
    experimentType: "Parameter Test",
    datasetOrSymbol: "US Large Cap Liquid Panel",
    startDate: "2010-01-01",
    endDate: "2021-12-31",
    benchmark: "MA 20/60 baseline",
    parameters: [
      { key: "fast_ma", value: "10" },
      { key: "slow_ma", value: "50" },
      { key: "cost_bps", value: "8" },
    ],
    successCriteria: "Net Sharpe within 0.1 of baseline with lower max DD.",
    falsificationCondition: "Turnover rises enough that net Sharpe falls below 0.4.",
    notes: "Parameter grid cell selected from sensitivity package.",
    owner: "A. Chen",
    createdAt: "2026-04-05T09:00:00.000Z",
    updatedAt: "2026-04-12T16:30:00.000Z",
    resultSummary:
      "Higher turnover; net Sharpe 0.61. Prefer 20/60 for baseline. Demo metrics only.",
    metrics: {
      sharpe: 0.61,
      cagr: 0.081,
      maxDrawdown: -0.155,
      volatility: 0.124,
      tradeCount: 312,
      winRate: 0.51,
      totalTransactionCost: 11.4,
    },
    linkedNotebookEntryIds: ["nb-mom-004"],
    relatedEvidenceIds: ["ev-mom-sens"],
    validationReadiness: "partial",
  },
  {
    id: "exp-mom-003",
    researchId: "rs-momentum-001",
    name: "RSI-filtered crossover",
    hypothesis:
      "Adding RSI(14) > 40 as an entry filter reduces whipsaws without removing the momentum edge.",
    status: "Completed",
    experimentType: "Feature Test",
    datasetOrSymbol: "US Large Cap Liquid Panel",
    startDate: "2010-01-01",
    endDate: "2021-12-31",
    benchmark: "MA 20/60 baseline",
    parameters: [
      { key: "fast_ma", value: "20" },
      { key: "slow_ma", value: "60" },
      { key: "rsi_filter", value: "14 > 40" },
      { key: "cost_bps", value: "8" },
    ],
    successCriteria: "Trade count ↓ ≥ 15% with net Sharpe ≥ baseline − 0.05.",
    falsificationCondition: "Filter removes edge (net Sharpe < 0.4).",
    notes: "Feature test only; not promoted to primary protocol.",
    owner: "A. Chen",
    createdAt: "2026-04-20T10:15:00.000Z",
    updatedAt: "2026-05-02T13:40:00.000Z",
    resultSummary:
      "Fewer trades; Sharpe 0.72. Mixed benefit — retain as optional overlay. Demo only.",
    metrics: {
      sharpe: 0.72,
      cagr: 0.088,
      maxDrawdown: -0.138,
      volatility: 0.115,
      tradeCount: 168,
      winRate: 0.56,
      totalTransactionCost: 6.2,
    },
    linkedNotebookEntryIds: [],
    relatedEvidenceIds: ["ev-mom-sens"],
    validationReadiness: "partial",
  },
  {
    id: "exp-mom-004",
    researchId: "rs-momentum-001",
    name: "Transaction-cost stress test",
    hypothesis:
      "The 20/60 edge remains positive under 12–16 bps round-trip cost stress.",
    status: "Completed",
    experimentType: "Cost Test",
    datasetOrSymbol: "US Large Cap Liquid Panel",
    startDate: "2010-01-01",
    endDate: "2021-12-31",
    benchmark: "MA 20/60 @ 8 bps",
    parameters: [
      { key: "fast_ma", value: "20" },
      { key: "slow_ma", value: "60" },
      { key: "cost_bps_grid", value: "8,12,16" },
    ],
    successCriteria: "Net Sharpe > 0.4 at 12 bps; document break-even cost.",
    falsificationCondition: "Edge disappears at ≤ 12 bps.",
    notes: "Cost stress completed before OOS folds.",
    owner: "A. Chen",
    createdAt: "2026-05-08T08:30:00.000Z",
    updatedAt: "2026-05-15T17:00:00.000Z",
    resultSummary:
      "Break-even near 15 bps. At 12 bps Sharpe ~0.52. Thin but positive. Demo only.",
    metrics: {
      sharpe: 0.52,
      cagr: 0.071,
      maxDrawdown: -0.149,
      volatility: 0.119,
      tradeCount: 214,
      winRate: 0.54,
      totalTransactionCost: 12.0,
    },
    linkedNotebookEntryIds: ["nb-mom-004"],
    relatedEvidenceIds: ["ev-mom-bt"],
    validationReadiness: "ready",
  },
  {
    id: "exp-mom-005",
    researchId: "rs-momentum-001",
    name: "Out-of-sample 2022–2025 walk-forward",
    hypothesis:
      "Walk-forward folds on 2022–2025 preserve sign of net expectancy under frozen 20/60 protocol.",
    status: "Running",
    experimentType: "Backtest",
    datasetOrSymbol: "US Large Cap Liquid Panel",
    startDate: "2022-01-01",
    endDate: "2025-12-31",
    benchmark: "Equal-weight buy & hold",
    parameters: [
      { key: "protocol", value: "EXP-MOM-001 frozen" },
      { key: "folds", value: "5" },
      { key: "current_fold", value: "3/5" },
      { key: "cost_bps", value: "8" },
    ],
    successCriteria: "OOS net Sharpe ≥ 0.4 across completed folds.",
    falsificationCondition: "Majority of folds net Sharpe < 0.2.",
    notes: "Fold 3/5 in progress. Universe freeze required before fold 4.",
    owner: "A. Chen",
    createdAt: "2026-05-20T09:00:00.000Z",
    updatedAt: "2026-07-10T14:05:00.000Z",
    resultSummary:
      "Partial OOS Sharpe ~0.51 through fold 3. Incomplete — not a final claim.",
    metrics: {
      sharpe: 0.51,
      cagr: 0.064,
      maxDrawdown: -0.168,
      volatility: 0.132,
      tradeCount: 89,
      winRate: 0.49,
      totalTransactionCost: 8.0,
    },
    linkedNotebookEntryIds: ["nb-mom-005", "nb-mom-007"],
    relatedEvidenceIds: ["ev-mom-oos"],
    validationReadiness: "partial",
  },
  {
    id: "exp-mom-006",
    researchId: "rs-momentum-001",
    name: "Sideways-market regime test",
    hypothesis:
      "In low-trend / high-chop regimes, 20/60 underperforms buy-and-hold but stays within DD gate.",
    status: "Approved",
    experimentType: "Regime Test",
    datasetOrSymbol: "US Large Cap Liquid Panel",
    startDate: "2015-01-01",
    endDate: "2019-12-31",
    benchmark: "Equal-weight buy & hold",
    parameters: [
      { key: "regime_def", value: "ADX < 20 & realized vol mid-quintile" },
      { key: "fast_ma", value: "20" },
      { key: "slow_ma", value: "60" },
    ],
    successCriteria: "Document underperformance magnitude; DD within −20%.",
    falsificationCondition: "Regime filter cannot be reproduced from published rules.",
    notes: "Approved; queued after OOS fold 4. No silent start from UI.",
    owner: "A. Chen",
    createdAt: "2026-06-25T11:00:00.000Z",
    updatedAt: "2026-07-01T10:00:00.000Z",
    resultSummary: "Not started — Approved awaiting governed start.",
    metrics: {
      sharpe: null,
      cagr: null,
      maxDrawdown: null,
      volatility: null,
      tradeCount: null,
      winRate: null,
      totalTransactionCost: null,
    },
    linkedNotebookEntryIds: ["nb-mom-008"],
    relatedEvidenceIds: [],
    validationReadiness: "not_ready",
  },
];

const RSI_EXPERIMENTS: ResearchExperiment[] = [
  {
    id: "exp-rsi-001",
    researchId: "rs-rsi-002",
    name: "RSI(14) 5-day exit baseline",
    hypothesis:
      "RSI(14) < 30 entries on S&P 100 with 5-day exit deliver positive expectancy after costs.",
    status: "Completed",
    experimentType: "Backtest",
    datasetOrSymbol: "S&P 100 constituents",
    startDate: "2012-01-01",
    endDate: "2021-12-31",
    benchmark: "Buy & hold large-cap sleeve",
    parameters: [
      { key: "rsi", value: "14" },
      { key: "entry", value: "< 30" },
      { key: "exit_days", value: "5" },
    ],
    successCriteria: "Net expectancy > 0 with OOS Sharpe ≥ 0.4.",
    falsificationCondition: "OOS Sharpe < 0.2 or earnings leakage unexplained.",
    notes: "Review flagged thin 2022 coverage.",
    owner: "M. Okonkwo",
    createdAt: "2026-02-10T10:00:00.000Z",
    updatedAt: "2026-07-01T15:30:00.000Z",
    resultSummary: "OOS Sharpe 0.41; thin 2022 sample. Demo only.",
    metrics: {
      sharpe: 0.41,
      cagr: 0.048,
      maxDrawdown: -0.112,
      volatility: 0.095,
      tradeCount: 406,
      winRate: 0.54,
      totalTransactionCost: 9.5,
    },
    linkedNotebookEntryIds: ["nb-rsi-002"],
    relatedEvidenceIds: ["ev-rsi-oos"],
    validationReadiness: "blocked",
  },
];

const PAIRS_EXPERIMENTS: ResearchExperiment[] = [
  {
    id: "exp-pairs-001",
    researchId: "rs-pairs-003",
    name: "Sector ETF pairs holdout",
    hypothesis:
      "Selected cointegrated sector ETF pairs remain tradable post-2020 after 8 bps costs.",
    status: "Completed",
    experimentType: "Backtest",
    datasetOrSymbol: "Sector ETF pairs set v3",
    startDate: "2016-01-01",
    endDate: "2024-12-31",
    benchmark: "Cash + sector-neutral",
    parameters: [
      { key: "z_entry", value: "2.0" },
      { key: "z_stop", value: "3.5" },
      { key: "cost_bps", value: "8" },
    ],
    successCriteria: "Holdout half-life 5–12 days; net Sharpe ≥ 0.7.",
    falsificationCondition: "Cointegration breaks without recovery within gate.",
    notes: "Passed holdout; ready for Evaluation package.",
    owner: "S. Patel",
    createdAt: "2025-12-01T09:00:00.000Z",
    updatedAt: "2026-06-15T11:00:00.000Z",
    resultSummary: "Net Sharpe 0.92 on selected set. Demo only.",
    metrics: {
      sharpe: 0.92,
      cagr: 0.076,
      maxDrawdown: -0.088,
      volatility: 0.082,
      tradeCount: 154,
      winRate: 0.58,
      totalTransactionCost: 8.0,
    },
    linkedNotebookEntryIds: ["nb-pairs-001"],
    relatedEvidenceIds: ["ev-pairs-oos"],
    validationReadiness: "ready",
  },
];

const FACTOR_EXPERIMENTS: ResearchExperiment[] = [
  {
    id: "exp-fac-001",
    researchId: "rs-factor-006",
    name: "Value–momentum timing draft",
    hypothesis:
      "Relative strength between value and momentum can time tilts under a 40% turnover ceiling.",
    status: "Designed",
    experimentType: "Feature Test",
    datasetOrSymbol: "Factor portfolio candidates (TBD)",
    startDate: "2005-01-01",
    endDate: "2024-12-31",
    benchmark: "Static 50/50 value–momentum",
    parameters: [{ key: "status", value: "definitions not pinned" }],
    successCriteria: "Falsification criteria must be written before approval.",
    falsificationCondition: "TBD — Draft stage.",
    notes: "Cannot approve until falsification criteria exist.",
    owner: "A. Chen",
    createdAt: "2026-07-02T08:00:00.000Z",
    updatedAt: "2026-07-06T12:10:00.000Z",
    resultSummary: "Designed only — no run.",
    metrics: {
      sharpe: null,
      cagr: null,
      maxDrawdown: null,
      volatility: null,
      tradeCount: null,
      winRate: null,
      totalTransactionCost: null,
    },
    linkedNotebookEntryIds: ["nb-fac-001"],
    relatedEvidenceIds: [],
    validationReadiness: "not_ready",
  },
];

const MACRO_EXPERIMENTS: ResearchExperiment[] = [
  {
    id: "exp-mac-001",
    researchId: "rs-macro-007",
    name: "CPI revision lag sensitivity",
    hypothesis:
      "Growth/inflation overlay remains useful after accounting for CPI revision lag.",
    status: "Running",
    experimentType: "Parameter Test",
    datasetOrSymbol: "Multi-asset futures + vintage CPI",
    startDate: "2000-01-01",
    endDate: "2024-12-31",
    benchmark: "Static risk parity",
    parameters: [
      { key: "lag_grid", value: "0–6 months" },
      { key: "status", value: "unfinished" },
    ],
    successCriteria: "Stable sign across lag grid before synthesis.",
    falsificationCondition: "Results flip solely based on lag choice.",
    notes: "Blocks synthesis until complete.",
    owner: "H. Nakamura",
    createdAt: "2026-06-01T10:00:00.000Z",
    updatedAt: "2026-07-11T08:05:00.000Z",
    resultSummary: "In progress — lag assumption dominates early windows.",
    metrics: {
      sharpe: 0.11,
      cagr: 0.022,
      maxDrawdown: -0.095,
      volatility: 0.074,
      tradeCount: null,
      winRate: null,
      totalTransactionCost: null,
    },
    linkedNotebookEntryIds: ["nb-mac-001", "nb-mac-002"],
    relatedEvidenceIds: ["ev-mac-sens"],
    validationReadiness: "partial",
  },
];

const SECTOR_EXPERIMENTS: ResearchExperiment[] = [
  {
    id: "exp-sec-001",
    researchId: "rs-sector-008",
    name: "Capacity stress on industry momentum",
    hypothesis:
      "Industry momentum survives excluding top liquidity quintile under capacity-aware costs.",
    status: "Invalidated",
    experimentType: "Cost Test",
    datasetOrSymbol: "Industry momentum panel",
    startDate: "2000-01-01",
    endDate: "2020-12-31",
    benchmark: "Equal-weight industries",
    parameters: [{ key: "capacity_model", value: "participation-aware v1" }],
    successCriteria: "Net edge after capacity costs.",
    falsificationCondition: "Edge disappears under realistic capacity.",
    notes: "Invalidated for production claims; negative result retained.",
    owner: "M. Okonkwo",
    createdAt: "2025-08-01T09:00:00.000Z",
    updatedAt: "2026-05-19T11:45:00.000Z",
    resultSummary: "Rejected — edge collapses under capacity. Archived research.",
    metrics: {
      sharpe: 0.08,
      cagr: 0.012,
      maxDrawdown: -0.21,
      volatility: 0.145,
      tradeCount: 980,
      winRate: 0.48,
      totalTransactionCost: 22.0,
    },
    linkedNotebookEntryIds: ["nb-sec-001"],
    relatedEvidenceIds: ["ev-sec-stress"],
    validationReadiness: "blocked",
  },
];

export const MOCK_EXPERIMENTS_BY_RESEARCH: Record<string, ResearchExperiment[]> = {
  "rs-momentum-001": MOMENTUM_EXPERIMENTS,
  "rs-rsi-002": RSI_EXPERIMENTS,
  "rs-pairs-003": PAIRS_EXPERIMENTS,
  "rs-vol-004": [],
  "rs-etf-005": [],
  "rs-factor-006": FACTOR_EXPERIMENTS,
  "rs-macro-007": MACRO_EXPERIMENTS,
  "rs-sector-008": SECTOR_EXPERIMENTS,
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
