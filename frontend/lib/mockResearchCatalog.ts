/**
 * Research Workspace 共享 mock 目录（列表 + 详情同源）。
 *
 * TODO(backend): 替换为 GET /api/research 与 GET /api/research/{id}。
 * TODO(database): 当前无持久化；仅内存演示。
 */

import {
  toResearchListItem,
  type ResearchDetail,
  type ResearchListItem,
} from "@/types/research";

export const MOCK_RESEARCH_DETAILS: ResearchDetail[] = [
  {
    id: "rs-momentum-001",
    name: "Momentum Strategy",
    researchQuestion:
      "Does 12–1 month cross-sectional momentum remain significant after costs on liquid US equities?",
    status: "Running",
    currentStage: "Running",
    confidenceScore: 62,
    owner: "A. Chen",
    tags: ["momentum", "equities", "cross-sectional"],
    createdAt: "2026-03-12T09:20:00.000Z",
    updatedAt: "2026-07-10T14:05:00.000Z",
    experimentCount: 14,
    lastValidation: "Walk-forward fold 3/5 in progress",
    currentRecommendation: "Continue; freeze universe before next OOS fold",
    hypothesis:
      "After realistic transaction costs and a liquid-universe filter, 12–1 momentum retains positive risk-adjusted expectancy versus equal-weight and value benchmarks.",
    researchObjective:
      "Produce a reproducible, cost-aware walk-forward evaluation that either supports limited paper allocation or falsifies the edge under capacity constraints.",
    researchSummary:
      "Fourteen experiments cover in-sample ranking, cost stress, and three completed walk-forward folds. Fold 4 is running. Universe freeze is the gating next decision before synthesis.",
    evidenceSummary:
      "Backtest and sensitivity packages are complete. Out-of-sample validation is partially complete (3/5 folds). Stress testing remains pending. Data confidence is rated medium-high on the primary CRSP-equivalent panel.",
    validationSummary:
      "Holdout through 2021 is acceptable; 2022 regime reduces Sharpe. Cost stress at 8–12 bps still leaves a thin but positive edge on the top liquidity quintile.",
    keyStrengths: [
      "Clear falsification criteria and frozen protocol versions",
      "Cost and turnover stress already documented",
      "Universe definition is explicit and versioned",
    ],
    knownWeaknesses: [
      "Walk-forward incomplete (fold 3/5)",
      "Crowding proxy still heuristic",
      "Benchmark set does not yet include industry-neutral variants",
    ],
    openQuestions: [
      "Does the edge survive excluding the top liquidity quintile?",
      "How sensitive is fold 4 to 2020 microstructure shifts?",
      "What capacity ceiling keeps net Sharpe above 0.4?",
    ],
    nextActions: [
      "Freeze equity universe definition before fold 4",
      "Complete remaining walk-forward folds",
      "Schedule stress-test battery after OOS completes",
    ],
    evidenceItems: [
      {
        id: "ev-mom-bt",
        label: "Backtest completed",
        status: "completed",
        result: "IS Sharpe 0.78 net of 8 bps; max DD −14.2%",
      },
      {
        id: "ev-mom-oos",
        label: "Out-of-sample validation",
        status: "in_progress",
        result: "Walk-forward fold 3/5; current OOS Sharpe 0.51",
      },
      {
        id: "ev-mom-sens",
        label: "Sensitivity analysis completed",
        status: "completed",
        result: "Lookback 9–15m stable; rebalance monthly preferred",
      },
      {
        id: "ev-mom-stress",
        label: "Stress test pending",
        status: "pending",
        result: "Crisis and liquidity-shock battery not started",
      },
      {
        id: "ev-mom-data",
        label: "Data confidence rating",
        status: "completed",
        result: "Medium-high · primary panel provenance reviewed",
      },
      {
        id: "ev-mom-bench",
        label: "Benchmark comparison",
        status: "completed",
        result: "Beats equal-weight; mixed vs value tilt",
      },
    ],
  },
  {
    id: "rs-rsi-002",
    name: "RSI Mean Reversion",
    researchQuestion:
      "Can RSI(14) oversold entries on large-cap names deliver positive expectancy with a 5-day exit?",
    status: "Review",
    currentStage: "Reviewed",
    confidenceScore: 48,
    owner: "M. Okonkwo",
    tags: ["mean-reversion", "RSI", "short-horizon"],
    createdAt: "2026-02-04T11:00:00.000Z",
    updatedAt: "2026-07-08T16:40:00.000Z",
    experimentCount: 9,
    lastValidation: "OOS Sharpe 0.41; sample thin in 2022 regime",
    currentRecommendation: "Request risk review before paper allocation",
    hypothesis:
      "RSI(14) < 30 on S&P 100 constituents produces positive 5-day expectancy after costs when entries avoid earnings windows.",
    researchObjective:
      "Decide whether short-horizon mean reversion merits a constrained paper sleeve or should return to redesign.",
    researchSummary:
      "Nine experiments closed. Synthesis and accountable review are complete. Reviewers flagged thin 2022 coverage and earnings-window leakage risk before any paper allocation.",
    evidenceSummary:
      "Backtest, OOS, and sensitivity are complete. Stress test is blocked pending earnings calendar alignment. Data confidence is medium.",
    validationSummary:
      "OOS Sharpe 0.41 with wide confidence bands. 2022 subsample is thin; reviewers require a dedicated regime stress before Evaluation.",
    keyStrengths: [
      "Simple, auditable entry/exit rules",
      "Earnings filter prototype exists",
      "Review packet already assembled",
    ],
    knownWeaknesses: [
      "Thin sample in high-vol regimes",
      "Slippage model may understate short-horizon costs",
      "No capacity study yet",
    ],
    openQuestions: [
      "Does expectancy survive a stricter earnings blackout?",
      "Is 5-day exit optimal versus 3–7 day grid under costs?",
    ],
    nextActions: [
      "Request Evaluation with risk-gate checklist",
      "Align stress test to earnings calendar",
      "Document reviewer conditions in Decision draft",
    ],
    evidenceItems: [
      {
        id: "ev-rsi-bt",
        label: "Backtest completed",
        status: "completed",
        result: "IS hit rate 54%; net expectancy +4.1 bps/trade",
      },
      {
        id: "ev-rsi-oos",
        label: "Out-of-sample validation completed",
        status: "completed",
        result: "OOS Sharpe 0.41; 2022 subsample thin",
      },
      {
        id: "ev-rsi-sens",
        label: "Sensitivity analysis completed",
        status: "completed",
        result: "RSI thresholds 25–35 retain sign; 5d exit preferred",
      },
      {
        id: "ev-rsi-stress",
        label: "Stress test pending",
        status: "blocked",
        result: "Blocked on earnings-calendar alignment",
      },
      {
        id: "ev-rsi-data",
        label: "Data confidence rating",
        status: "completed",
        result: "Medium · corporate-action join reviewed",
      },
      {
        id: "ev-rsi-bench",
        label: "Benchmark comparison",
        status: "completed",
        result: "Modest edge vs buy-and-hold large-cap sleeve",
      },
    ],
  },
  {
    id: "rs-pairs-003",
    name: "Pairs Trading",
    researchQuestion:
      "Do cointegrated sector ETF pairs sustain half-life and z-score edges after 2020 microstructure shifts?",
    status: "Validated",
    currentStage: "Reviewed",
    confidenceScore: 71,
    owner: "S. Patel",
    tags: ["pairs", "cointegration", "ETF"],
    createdAt: "2025-11-18T08:15:00.000Z",
    updatedAt: "2026-06-28T10:12:00.000Z",
    experimentCount: 22,
    lastValidation: "Passed holdout + cost stress at 8 bps",
    currentRecommendation: "Approve for limited paper trading book",
    hypothesis:
      "Selected sector ETF pairs remain mean-reverting with tradable half-lives after 2020, net of 8 bps round-trip costs.",
    researchObjective:
      "Validate a small pairs book with explicit entry z-scores, stop rules, and monitoring hooks for cointegration breaks.",
    researchSummary:
      "Twenty-two experiments including Engle–Granger and Johansen screens. Holdout and cost stress passed. Research is reviewed and ready for Evaluation → paper decision.",
    evidenceSummary:
      "Backtest, OOS, sensitivity, and stress tests completed. Data confidence high on ETF panels. Benchmark comparison versus cash and sector-neutral baselines complete.",
    validationSummary:
      "Holdout post-2020 preserves half-life band 5–12 days. Cost stress at 8 bps keeps net Sharpe above gate. Cointegration break monitor prototype ready.",
    keyStrengths: [
      "Strong evidence lineage across pair selection and execution assumptions",
      "Explicit break-monitor design",
      "Passed cost and holdout gates",
    ],
    knownWeaknesses: [
      "Pair universe still discretionary",
      "Funding and borrow not modeled for single-name extensions",
    ],
    openQuestions: [
      "What is the maximum concurrent pairs under risk budget?",
      "Should Evaluation require live cointegration alerts before paper start?",
    ],
    nextActions: [
      "Submit Evaluation package",
      "Propose limited paper book size and kill criteria",
      "Register monitoring program draft",
    ],
    evidenceItems: [
      {
        id: "ev-pairs-bt",
        label: "Backtest completed",
        status: "completed",
        result: "Net Sharpe 0.92 on selected pair set",
      },
      {
        id: "ev-pairs-oos",
        label: "Out-of-sample validation completed",
        status: "completed",
        result: "Holdout post-2020 passed half-life gates",
      },
      {
        id: "ev-pairs-sens",
        label: "Sensitivity analysis completed",
        status: "completed",
        result: "Z-entry 1.5–2.5 stable; stop at 3.5 preferred",
      },
      {
        id: "ev-pairs-stress",
        label: "Stress test completed",
        status: "completed",
        result: "2020 gap and 2022 inflation shock within DD gate",
      },
      {
        id: "ev-pairs-data",
        label: "Data confidence rating",
        status: "completed",
        result: "High · ETF adjust method documented",
      },
      {
        id: "ev-pairs-bench",
        label: "Benchmark comparison",
        status: "completed",
        result: "Outperforms cash; competitive vs sector-neutral",
      },
    ],
  },
  {
    id: "rs-vol-004",
    name: "Volatility Breakout",
    researchQuestion:
      "Does a 20-day realized-vol breakout on SPX futures improve risk-adjusted returns versus buy-and-hold?",
    status: "Paper Trading",
    currentStage: "Closed",
    confidenceScore: 58,
    owner: "J. Morales",
    tags: ["volatility", "breakout", "futures"],
    createdAt: "2025-09-02T13:45:00.000Z",
    updatedAt: "2026-07-09T09:30:00.000Z",
    experimentCount: 17,
    lastValidation: "Paper day 47; max DD within gate",
    currentRecommendation: "Keep paper; review after 90 trading days",
    hypothesis:
      "A 20-day realized-vol breakout overlay improves SPX futures risk-adjusted returns versus continuous long exposure after costs and roll.",
    researchObjective:
      "Close research with published findings and operate a governed paper simulation for 90 trading days before any expansion.",
    researchSummary:
      "Research is Closed after review. Paper simulation is day 47 with drawdown inside the approved gate. Next governance checkpoint is day 90.",
    evidenceSummary:
      "All core evidence packages completed before closure. Paper monitoring now owns ongoing observation; research artifacts remain immutable.",
    validationSummary:
      "Validation passed with modest net Sharpe improvement versus buy-and-hold under roll-aware costs. Review approved limited paper.",
    keyStrengths: [
      "Clear baseline (buy-and-hold futures)",
      "Roll and cost model documented",
      "Monitoring hooks already active in paper",
    ],
    knownWeaknesses: [
      "Single-contract focus",
      "Regime classifier still coarse",
    ],
    openQuestions: [
      "Should day-90 review expand to equity index basket?",
      "Is overnight gap filter still necessary?",
    ],
    nextActions: [
      "Continue paper through day 90",
      "Prepare monitoring digest for governance review",
      "Do not reopen research unless paper alerts fire",
    ],
    evidenceItems: [
      {
        id: "ev-vol-bt",
        label: "Backtest completed",
        status: "completed",
        result: "Net Sharpe +0.18 vs B&H; DD improved 2.1pp",
      },
      {
        id: "ev-vol-oos",
        label: "Out-of-sample validation completed",
        status: "completed",
        result: "OOS confirms sign; magnitude attenuated",
      },
      {
        id: "ev-vol-sens",
        label: "Sensitivity analysis completed",
        status: "completed",
        result: "Window 15–25d stable; 20d selected",
      },
      {
        id: "ev-vol-stress",
        label: "Stress test completed",
        status: "completed",
        result: "2020 crash path within approved DD gate",
      },
      {
        id: "ev-vol-data",
        label: "Data confidence rating",
        status: "completed",
        result: "High · futures roll series audited",
      },
      {
        id: "ev-vol-bench",
        label: "Benchmark comparison",
        status: "completed",
        result: "Beats continuous long after costs",
      },
    ],
  },
  {
    id: "rs-etf-005",
    name: "ETF Rotation",
    researchQuestion:
      "Can dual-momentum rotation across sector ETFs beat a 60/40 benchmark on a monthly rebalance?",
    status: "Monitoring",
    currentStage: "Closed",
    confidenceScore: 66,
    owner: "L. Bergström",
    tags: ["rotation", "ETF", "allocation"],
    createdAt: "2025-06-21T10:00:00.000Z",
    updatedAt: "2026-07-07T18:22:00.000Z",
    experimentCount: 31,
    lastValidation: "Live monitor healthy; regime flag amber",
    currentRecommendation: "Maintain; escalate if correlation cluster rises",
    hypothesis:
      "Absolute and relative dual-momentum across liquid sector ETFs outperform a static 60/40 on a monthly cadence after costs.",
    researchObjective:
      "Deliver a closed research record and an operating monitoring program with explicit escalation rules.",
    researchSummary:
      "Research Closed. Monitoring is active with an amber regime flag driven by rising sector correlation. No reopen requested yet.",
    evidenceSummary:
      "Full evidence suite completed pre-closure. Current attention is monitoring posture, not new research experiments.",
    validationSummary:
      "Validated against 60/40 with turnover and tax-aware notes. Monitoring inherits the frozen parameter set.",
    keyStrengths: [
      "Long experiment history with clear version pins",
      "Monitoring alerts defined",
      "Benchmark contract explicit",
    ],
    knownWeaknesses: [
      "Correlation cluster can mute diversification",
      "Monthly cadence may lag fast shocks",
    ],
    openQuestions: [
      "Should amber escalate to Needs Review on Strategy?",
      "Is a defensive cash sleeve warranted under high correlation?",
    ],
    nextActions: [
      "Track correlation-cluster alert for 10 sessions",
      "Escalate only if monitoring policy thresholds breach",
      "Keep research Closed unless reopening criteria met",
    ],
    evidenceItems: [
      {
        id: "ev-etf-bt",
        label: "Backtest completed",
        status: "completed",
        result: "Net excess vs 60/40 +1.9%/yr",
      },
      {
        id: "ev-etf-oos",
        label: "Out-of-sample validation completed",
        status: "completed",
        result: "OOS excess retained with higher turnover",
      },
      {
        id: "ev-etf-sens",
        label: "Sensitivity analysis completed",
        status: "completed",
        result: "Lookbacks 6–12m stable region",
      },
      {
        id: "ev-etf-stress",
        label: "Stress test completed",
        status: "completed",
        result: "2008/2020 paths within policy DD",
      },
      {
        id: "ev-etf-data",
        label: "Data confidence rating",
        status: "completed",
        result: "High · ETF total-return series",
      },
      {
        id: "ev-etf-bench",
        label: "Benchmark comparison",
        status: "completed",
        result: "Beats 60/40 on risk-adjusted basis",
      },
    ],
  },
  {
    id: "rs-factor-006",
    name: "Factor Timing",
    researchQuestion:
      "Can value–momentum relative strength time factor tilts without excessive turnover?",
    status: "Draft",
    currentStage: "Draft",
    confidenceScore: 28,
    owner: "A. Chen",
    tags: ["factors", "timing", "value"],
    createdAt: "2026-07-01T07:50:00.000Z",
    updatedAt: "2026-07-06T12:10:00.000Z",
    experimentCount: 2,
    lastValidation: "No formal validation yet",
    currentRecommendation: "Define falsification criteria before scoping experiments",
    hypothesis:
      "Relative strength between value and momentum factor portfolios can time tilts with turnover below a 40% annualized ceiling.",
    researchObjective:
      "Scope a falsifiable plan: datasets, experiment grid, and kill criteria before any Running experiments.",
    researchSummary:
      "Draft only. Two exploratory notebooks exist. No Approved Experiment yet. Planning cannot start until falsification criteria are written.",
    evidenceSummary:
      "No formal evidence packages. Data confidence not rated. Benchmark contract still TBD.",
    validationSummary: "No formal validation yet — research remains in Draft.",
    keyStrengths: [
      "Clear economic intuition",
      "Owner assigned",
    ],
    knownWeaknesses: [
      "No experiment protocol",
      "Turnover ceiling not operationalized",
      "Factor definitions not version-pinned",
    ],
    openQuestions: [
      "Which factor constructions are in scope?",
      "What observation would falsify the timing claim?",
    ],
    nextActions: [
      "Write falsification criteria",
      "Pin factor portfolio definitions",
      "Draft Planning packet for owner review",
    ],
    evidenceItems: [
      {
        id: "ev-fac-bt",
        label: "Backtest completed",
        status: "pending",
        result: "Not started — Draft stage",
      },
      {
        id: "ev-fac-oos",
        label: "Out-of-sample validation completed",
        status: "pending",
        result: "Blocked until experiments exist",
      },
      {
        id: "ev-fac-sens",
        label: "Sensitivity analysis completed",
        status: "pending",
        result: "Not started",
      },
      {
        id: "ev-fac-stress",
        label: "Stress test pending",
        status: "pending",
        result: "Not started",
      },
      {
        id: "ev-fac-data",
        label: "Data confidence rating",
        status: "pending",
        result: "Dataset candidates not yet Ready",
      },
      {
        id: "ev-fac-bench",
        label: "Benchmark comparison",
        status: "pending",
        result: "Benchmark contract TBD",
      },
    ],
  },
  {
    id: "rs-macro-007",
    name: "Macro Allocation",
    researchQuestion:
      "Do simple growth/inflation regime maps improve multi-asset risk parity overlays?",
    status: "Running",
    currentStage: "Running",
    confidenceScore: 44,
    owner: "H. Nakamura",
    tags: ["macro", "multi-asset", "regimes"],
    createdAt: "2026-01-15T15:20:00.000Z",
    updatedAt: "2026-07-11T08:05:00.000Z",
    experimentCount: 11,
    lastValidation: "Sensitivity to CPI revision lag unfinished",
    currentRecommendation: "Complete lag robustness before synthesis",
    hypothesis:
      "A four-quadrant growth/inflation map improves risk-parity overlays on multi-asset futures after accounting for CPI revision lag.",
    researchObjective:
      "Finish lag-robustness experiments, then synthesize whether regime overlays beat static risk parity under costs.",
    researchSummary:
      "Eleven experiments running or completed. CPI revision-lag sensitivity is unfinished and blocks synthesis. No review packet yet.",
    evidenceSummary:
      "Primary backtest complete. OOS partially complete. Sensitivity in progress. Stress and final benchmark package pending lag study.",
    validationSummary:
      "Preliminary OOS mixed; lag assumption materially changes 2010–2015 results. Validation incomplete until lag grid finishes.",
    keyStrengths: [
      "Transparent regime taxonomy",
      "Multi-asset scope documented",
    ],
    knownWeaknesses: [
      "CPI revision lag unresolved",
      "Transaction cost model coarse for FX sleeves",
    ],
    openQuestions: [
      "Which lag specification survives robustness?",
      "Does overlay help only in inflation shocks?",
    ],
    nextActions: [
      "Finish CPI lag sensitivity grid",
      "Lock OOS windows",
      "Only then start synthesis",
    ],
    evidenceItems: [
      {
        id: "ev-mac-bt",
        label: "Backtest completed",
        status: "completed",
        result: "IS overlay +0.11 Sharpe vs static RP",
      },
      {
        id: "ev-mac-oos",
        label: "Out-of-sample validation",
        status: "in_progress",
        result: "Partial OOS; lag assumption dominates",
      },
      {
        id: "ev-mac-sens",
        label: "Sensitivity analysis",
        status: "in_progress",
        result: "CPI revision lag grid unfinished",
      },
      {
        id: "ev-mac-stress",
        label: "Stress test pending",
        status: "pending",
        result: "Queued after lag study",
      },
      {
        id: "ev-mac-data",
        label: "Data confidence rating",
        status: "completed",
        result: "Medium · vintage CPI series required",
      },
      {
        id: "ev-mac-bench",
        label: "Benchmark comparison",
        status: "pending",
        result: "Final package after sensitivity",
      },
    ],
  },
  {
    id: "rs-sector-008",
    name: "Sector Momentum",
    researchQuestion:
      "Is industry-level momentum robust after excluding the top liquidity quintile?",
    status: "Archived",
    currentStage: "Closed",
    confidenceScore: 35,
    owner: "M. Okonkwo",
    tags: ["sector", "momentum", "liquidity"],
    createdAt: "2025-04-09T09:00:00.000Z",
    updatedAt: "2026-05-19T11:45:00.000Z",
    experimentCount: 18,
    lastValidation: "Rejected: edge disappears under realistic capacity",
    currentRecommendation: "Archive; reopen only with new capacity model",
    hypothesis:
      "Industry momentum remains profitable after removing the most liquid names and applying capacity-aware costs.",
    researchObjective:
      "Falsify or support industry momentum under capacity constraints; publish a closed negative result if edge fails.",
    researchSummary:
      "Closed and archived after review. Edge disappears under realistic capacity. Reopen only with a new capacity model and refreshed MarketDataset.",
    evidenceSummary:
      "All packages completed. Capacity stress was decisive and negative. Evidence retained for future comparison.",
    validationSummary:
      "Validation rejected the claim for production consideration. Negative result is intentional and preserved.",
    keyStrengths: [
      "Honest negative result with lineage",
      "Capacity framing explicit",
    ],
    knownWeaknesses: [
      "Original capacity model coarse",
      "Industry taxonomy dated",
    ],
    openQuestions: [
      "Would a newer capacity model change the conclusion?",
    ],
    nextActions: [
      "Keep Closed/Archived",
      "Reopen only with new capacity model + owner",
    ],
    evidenceItems: [
      {
        id: "ev-sec-bt",
        label: "Backtest completed",
        status: "completed",
        result: "Gross edge present; net collapses with capacity",
      },
      {
        id: "ev-sec-oos",
        label: "Out-of-sample validation completed",
        status: "completed",
        result: "OOS confirms capacity failure",
      },
      {
        id: "ev-sec-sens",
        label: "Sensitivity analysis completed",
        status: "completed",
        result: "Liquidity exclusion destroys edge",
      },
      {
        id: "ev-sec-stress",
        label: "Stress test completed",
        status: "completed",
        result: "Capacity stress decisive — rejected",
      },
      {
        id: "ev-sec-data",
        label: "Data confidence rating",
        status: "completed",
        result: "Medium · industry map version pinned",
      },
      {
        id: "ev-sec-bench",
        label: "Benchmark comparison",
        status: "completed",
        result: "Fails vs equal-weight industry after costs",
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
  return {
    ...found,
    tags: [...found.tags],
    keyStrengths: [...found.keyStrengths],
    knownWeaknesses: [...found.knownWeaknesses],
    openQuestions: [...found.openQuestions],
    nextActions: [...found.nextActions],
    evidenceItems: found.evidenceItems.map((evidence) => ({ ...evidence })),
  };
}

export class MockResearchError extends Error {
  constructor(message = "Unable to load the research workspace.") {
    super(message);
    this.name = "MockResearchError";
  }
}

/** @deprecated Prefer MockResearchError — kept for list page compatibility. */
export class MockResearchListError extends MockResearchError {
  constructor(message = "Unable to load the research workspace.") {
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

/**
 * 模拟异步列表加载。
 * TODO(backend): 替换为 listResearch() API 客户端。
 */
export async function loadMockResearchProjects(options?: {
  delayMs?: number;
}): Promise<ResearchListItem[]> {
  await delay(options?.delayMs ?? 480);
  if (shouldForceMockError()) {
    throw new MockResearchListError(
      "Mock load failed. Remove mockError=1 from the URL or retry."
    );
  }
  return getMockResearchProjects();
}

/**
 * 模拟异步详情加载。
 * TODO(backend): 替换为 getResearch(id) API 客户端。
 */
export async function loadMockResearchById(
  researchId: string,
  options?: { delayMs?: number }
): Promise<ResearchDetail | null> {
  await delay(options?.delayMs ?? 420);
  if (shouldForceMockError()) {
    throw new MockResearchError(
      "Mock load failed. Remove mockError=1 from the URL or retry."
    );
  }
  return getMockResearchById(researchId);
}

/** 兼容旧导入路径：列表常量仍导出。 */
export const MOCK_RESEARCH_PROJECTS: ResearchListItem[] =
  MOCK_RESEARCH_DETAILS.map(toResearchListItem);
