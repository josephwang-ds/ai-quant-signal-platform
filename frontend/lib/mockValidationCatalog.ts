/**
 * Validation Pipeline mock 目录（与 List / Detail / Experiments 同源）。
 *
 * TODO(backend): GET /api/research/{id}/validation
 * TODO(engine): 闸口由确定性 Validation 引擎计算，禁止 AI 判定 Pass/Fail。
 */

import type {
  ValidationBlocker,
  ValidationPipelineSnapshot,
  ValidationStage,
} from "@/types/validation";
import type { ResearchTimelineEvent } from "@/types/notebook";

function gate(
  id: string,
  rule: string,
  threshold: string,
  observed: string,
  passed: boolean,
  severity: "info" | "warning" | "blocking",
  evidenceRef: string
) {
  return { id, rule, threshold, observed, passed, severity, evidenceRef };
}

const MOMENTUM_STAGES: ValidationStage[] = [
  {
    id: "val-mom-hist",
    researchId: "rs-momentum-001",
    stageKey: "historical_backtest",
    name: "Historical Backtest",
    status: "Passed",
    purpose: "Assess in-sample behavior of the frozen MA 20/60 protocol after costs.",
    method: "Walk-forward-ready backtest on liquid US equity panel; cost 8 bps.",
    dataset: "US Large Cap Liquid Panel",
    dateRange: "2010-01-01 → 2021-12-31",
    benchmark: "Equal-weight buy & hold",
    successCriteria: "Net Sharpe ≥ 0.5; trade count ≥ 100; max DD better than B&H by ≥ 2pp.",
    falsificationCriteria: "Net Sharpe < 0.3 or trade count < 50 after costs.",
    lastRunAt: "2026-04-02T11:20:00.000Z",
    owner: "A. Chen",
    evidenceCount: 3,
    keyResult: "IS net Sharpe 0.78; 214 trades. Historical demo metrics only.",
    warnings: ["In-sample optimism risk remains until OOS completes."],
    nextAction: "Keep protocol frozen; rely on OOS and stress for advancement.",
    result: "Passed mandatory historical gates. Not a performance guarantee.",
    metrics: [
      { key: "sharpe", label: "Sharpe Ratio", value: "0.78", basis: "historical" },
      { key: "cagr", label: "CAGR", value: "9.2%", basis: "historical" },
      { key: "vol", label: "Volatility", value: "11.8%", basis: "historical" },
      { key: "mdd", label: "Maximum Drawdown", value: "−14.2%", basis: "historical" },
      { key: "trades", label: "Trade Count", value: "214", basis: "historical" },
      { key: "win", label: "Win Rate", value: "54%", basis: "historical" },
      { key: "cost", label: "Total Costs", value: "8.0 bps", basis: "simulated" },
    ],
    gates: [
      gate("g-hist-sharpe", "Minimum net Sharpe", "≥ 0.50", "0.78", true, "blocking", "ev-mom-bt"),
      gate("g-hist-trades", "Minimum trade count", "≥ 100", "214", true, "blocking", "ev-mom-bt"),
      gate("g-hist-mdd", "Max DD vs benchmark", "≥ 2pp improvement", "+2.1pp", true, "warning", "ev-mom-bt"),
    ],
    evidenceRefs: ["ev-mom-bt", "exp-mom-001"],
    dataConfidence: "high",
    limitations: ["Single cost assumption", "No capacity model in historical package"],
    recommendation: "Accept as historical baseline evidence only.",
    runHistory: [
      {
        id: "rh-hist-1",
        ranAt: "2026-04-02T11:20:00.000Z",
        outcome: "Passed",
        note: "ValidationPassed on frozen EXP-MOM-001.",
      },
    ],
  },
  {
    id: "val-mom-bench",
    researchId: "rs-momentum-001",
    stageKey: "benchmark_comparison",
    name: "Benchmark Comparison",
    status: "Passed",
    purpose: "Compare protocol to equal-weight and value-tilt baselines.",
    method: "Same window and costs; excess return and risk-adjusted spread.",
    dataset: "US Large Cap Liquid Panel",
    dateRange: "2010-01-01 → 2021-12-31",
    benchmark: "Equal-weight + value tilt",
    successCriteria: "Positive excess Sharpe vs equal-weight after costs.",
    falsificationCriteria: "Negative excess Sharpe vs both baselines.",
    lastRunAt: "2026-04-08T09:00:00.000Z",
    owner: "A. Chen",
    evidenceCount: 2,
    keyResult: "Beats equal-weight; mixed vs value tilt. Demo only.",
    warnings: ["Value tilt window sensitivity not fully explored."],
    nextAction: "Document mixed value result in synthesis.",
    result: "Passed equal-weight excess gate.",
    metrics: [
      {
        key: "excess",
        label: "Benchmark Excess Return",
        value: "+1.8%/yr vs EW",
        basis: "historical",
      },
      { key: "sharpe", label: "Sharpe Ratio", value: "0.78", basis: "historical" },
    ],
    gates: [
      gate(
        "g-bench-excess",
        "Positive excess vs equal-weight",
        "> 0",
        "+1.8%/yr",
        true,
        "blocking",
        "ev-mom-bench"
      ),
    ],
    evidenceRefs: ["ev-mom-bench", "ev-mom-bt"],
    dataConfidence: "high",
    limitations: ["Value comparison inconclusive"],
    recommendation: "Pass for EW; note value caveat.",
    runHistory: [
      {
        id: "rh-bench-1",
        ranAt: "2026-04-08T09:00:00.000Z",
        outcome: "Passed",
        note: "ValidationPassed vs equal-weight.",
      },
    ],
  },
  {
    id: "val-mom-oos",
    researchId: "rs-momentum-001",
    stageKey: "out_of_sample",
    name: "Out-of-Sample Validation",
    status: "Passed",
    purpose: "Confirm sign of expectancy outside the design window.",
    method: "Walk-forward folds; frozen parameters; fold 3/5 completed package.",
    dataset: "US Large Cap Liquid Panel",
    dateRange: "2022-01-01 → 2025-06-30 (partial)",
    benchmark: "Equal-weight buy & hold",
    successCriteria: "OOS net Sharpe ≥ 0.40 on completed folds.",
    falsificationCriteria: "Majority folds net Sharpe < 0.20.",
    lastRunAt: "2026-06-20T16:45:00.000Z",
    owner: "A. Chen",
    evidenceCount: 2,
    keyResult: "OOS Sharpe ~0.51 through fold 3 — passed with limitations.",
    warnings: [
      "Folds 4–5 incomplete",
      "2022 regime attenuates magnitude",
    ],
    nextAction: "Freeze universe before fold 4; do not claim full OOS completion.",
    result: "Passed threshold on completed folds; coverage incomplete.",
    metrics: [
      {
        key: "oos_sharpe",
        label: "Out-of-Sample Sharpe",
        value: "0.51",
        basis: "historical",
      },
      { key: "mdd", label: "Maximum Drawdown", value: "−16.8%", basis: "historical" },
      { key: "trades", label: "Trade Count", value: "89", basis: "historical" },
    ],
    gates: [
      gate("g-oos-sharpe", "Positive OOS Sharpe", "≥ 0.40", "0.51", true, "blocking", "ev-mom-oos"),
      gate(
        "g-oos-coverage",
        "Required fold coverage",
        "5/5 folds",
        "3/5 folds",
        false,
        "warning",
        "ev-mom-oos"
      ),
    ],
    evidenceRefs: ["ev-mom-oos", "exp-mom-005", "nb-mom-005"],
    dataConfidence: "medium",
    limitations: ["Incomplete walk-forward", "Sample thin in stress year"],
    recommendation: "Accept provisional Pass; continue folds before Evaluation.",
    runHistory: [
      {
        id: "rh-oos-1",
        ranAt: "2026-06-20T16:45:00.000Z",
        outcome: "Passed",
        note: "ValidationPassed with coverage limitation.",
      },
    ],
  },
  {
    id: "val-mom-sens",
    researchId: "rs-momentum-001",
    stageKey: "parameter_sensitivity",
    name: "Parameter Sensitivity",
    status: "Passed",
    purpose: "Check stability of lookback and rebalance choices.",
    method: "Local grid around 20/60; stability band on net Sharpe.",
    dataset: "US Large Cap Liquid Panel",
    dateRange: "2010-01-01 → 2021-12-31",
    benchmark: "MA 20/60 baseline",
    successCriteria: "Adjacent cells retain Sharpe within ±0.15 of baseline.",
    falsificationCriteria: "Edge collapses outside a one-step neighbor.",
    lastRunAt: "2026-05-02T13:40:00.000Z",
    owner: "A. Chen",
    evidenceCount: 2,
    keyResult: "Lookback 9–15m / MA neighbors stable. Demo only.",
    warnings: ["10/50 raises turnover materially."],
    nextAction: "Keep 20/60 as primary; archive 10/50 as rejected variant.",
    result: "Passed parameter stability gate.",
    metrics: [
      {
        key: "stability",
        label: "Parameter Stability",
        value: "±0.09 Sharpe band",
        basis: "simulated",
      },
      { key: "turnover", label: "Turnover", value: "~180% ann.", basis: "historical" },
    ],
    gates: [
      gate(
        "g-sens-band",
        "Parameter stability",
        "Sharpe band ≤ 0.15",
        "0.09",
        true,
        "blocking",
        "ev-mom-sens"
      ),
    ],
    evidenceRefs: ["ev-mom-sens", "exp-mom-002", "exp-mom-003"],
    dataConfidence: "high",
    limitations: ["Grid is local, not global"],
    recommendation: "Pass; freeze primary parameters.",
    runHistory: [
      {
        id: "rh-sens-1",
        ranAt: "2026-05-02T13:40:00.000Z",
        outcome: "Passed",
        note: "ValidationPassed stability band.",
      },
    ],
  },
  {
    id: "val-mom-stress",
    researchId: "rs-momentum-001",
    stageKey: "stress_testing",
    name: "Stress Testing",
    status: "Failed",
    purpose: "Probe crisis and liquidity-shock paths against drawdown guardrail.",
    method: "Historical crisis windows + liquidity shock overlay.",
    dataset: "US Large Cap Liquid Panel",
    dateRange: "Crisis subsets 2008 / 2020 / 2022",
    benchmark: "Equal-weight buy & hold",
    successCriteria: "Stress max DD within −20% guardrail.",
    falsificationCriteria: "Any mandated crisis path exceeds −20% DD.",
    lastRunAt: "2026-07-05T10:00:00.000Z",
    owner: "A. Chen",
    evidenceCount: 1,
    keyResult: "Failed — 2020 path stress DD −22.4% exceeds guardrail.",
    warnings: ["Liquidity overlay still coarse"],
    nextAction: "Redesign stress overlay or tighten universe before re-run.",
    result: "ValidationFailed on drawdown guardrail.",
    metrics: [
      { key: "stress_loss", label: "Stress Loss", value: "−22.4% DD", basis: "simulated" },
      { key: "mdd", label: "Maximum Drawdown", value: "−22.4%", basis: "simulated" },
    ],
    gates: [
      gate(
        "g-stress-dd",
        "Maximum drawdown threshold",
        "≥ −20%",
        "−22.4%",
        false,
        "blocking",
        "ev-mom-stress"
      ),
      gate(
        "g-stress-cov",
        "Required evidence coverage",
        "crisis battery complete",
        "primary paths run",
        true,
        "info",
        "ev-mom-stress"
      ),
    ],
    evidenceRefs: ["ev-mom-stress"],
    dataConfidence: "medium",
    limitations: ["Overlay not capacity-aware"],
    recommendation: "Block Evaluation until stress gate passes.",
    runHistory: [
      {
        id: "rh-stress-1",
        ranAt: "2026-07-05T10:00:00.000Z",
        outcome: "Failed",
        note: "ValidationFailed — DD guardrail breach.",
      },
    ],
  },
  {
    id: "val-mom-regime",
    researchId: "rs-momentum-001",
    stageKey: "regime_analysis",
    name: "Regime Analysis",
    status: "Inconclusive",
    purpose: "Measure behavior in low-trend / high-chop regimes.",
    method: "ADX & realized-vol regime labels; compare to B&H.",
    dataset: "US Large Cap Liquid Panel",
    dateRange: "2015-01-01 → 2019-12-31",
    benchmark: "Equal-weight buy & hold",
    successCriteria: "Document underperformance; DD within policy.",
    falsificationCriteria: "Regime definition not reproducible.",
    lastRunAt: "2026-06-30T12:00:00.000Z",
    owner: "A. Chen",
    evidenceCount: 1,
    keyResult: "Inconclusive — regime labels unstable across definitions.",
    warnings: ["Competing regime taxonomies disagree on 2018."],
    nextAction: "Pin a single published regime definition, then reassess.",
    result: "ValidationInconclusive — insufficient consensus on regime labels.",
    metrics: [
      { key: "sharpe", label: "Sharpe Ratio", value: "0.18 (chop)", basis: "historical" },
      { key: "mdd", label: "Maximum Drawdown", value: "−11.0%", basis: "historical" },
    ],
    gates: [
      gate(
        "g-regime-repro",
        "Reproducible regime definition",
        "single pinned taxonomy",
        "two competing defs",
        false,
        "warning",
        "exp-mom-006"
      ),
    ],
    evidenceRefs: ["exp-mom-006", "nb-mom-008"],
    dataConfidence: "medium",
    limitations: ["Definition disagreement"],
    recommendation: "Do not treat as Pass or Fail yet.",
    runHistory: [
      {
        id: "rh-regime-1",
        ranAt: "2026-06-30T12:00:00.000Z",
        outcome: "Inconclusive",
        note: "ValidationInconclusive on taxonomy conflict.",
      },
    ],
  },
  {
    id: "val-mom-cost",
    researchId: "rs-momentum-001",
    stageKey: "transaction_cost_review",
    name: "Transaction-Cost Review",
    status: "Passed",
    purpose: "Stress costs to 12–16 bps and locate break-even.",
    method: "Cost grid on frozen protocol.",
    dataset: "US Large Cap Liquid Panel",
    dateRange: "2010-01-01 → 2021-12-31",
    benchmark: "MA 20/60 @ 8 bps",
    successCriteria: "Net Sharpe > 0.40 at 12 bps.",
    falsificationCriteria: "Edge disappears at ≤ 12 bps.",
    lastRunAt: "2026-05-15T17:00:00.000Z",
    owner: "A. Chen",
    evidenceCount: 2,
    keyResult: "Break-even ~15 bps; 12 bps Sharpe ~0.52. Demo only.",
    warnings: ["Assumes constant bps; ignores borrow."],
    nextAction: "Keep 8 bps baseline; cite stress in Evaluation packet later.",
    result: "Passed transaction-cost resilience gate.",
    metrics: [
      { key: "cost", label: "Total Costs", value: "12.0 bps (stress)", basis: "simulated" },
      { key: "sharpe", label: "Sharpe Ratio", value: "0.52 @ 12 bps", basis: "simulated" },
      { key: "turnover", label: "Turnover", value: "~180% ann.", basis: "historical" },
    ],
    gates: [
      gate(
        "g-cost-resilience",
        "Transaction-cost resilience",
        "Sharpe > 0.40 at 12 bps",
        "0.52",
        true,
        "blocking",
        "exp-mom-004"
      ),
    ],
    evidenceRefs: ["exp-mom-004", "ev-mom-bt"],
    dataConfidence: "high",
    limitations: ["Constant bps model"],
    recommendation: "Pass with documented break-even.",
    runHistory: [
      {
        id: "rh-cost-1",
        ranAt: "2026-05-15T17:00:00.000Z",
        outcome: "Passed",
        note: "ValidationPassed cost resilience.",
      },
    ],
  },
  {
    id: "val-mom-data",
    researchId: "rs-momentum-001",
    stageKey: "data_quality_review",
    name: "Data-Quality Review",
    status: "Passed",
    purpose: "Confirm MarketDataset readiness and confidence for validation inputs.",
    method: "Provenance checklist + coverage / freshness / corporate-action joins.",
    dataset: "US Large Cap Liquid Panel",
    dateRange: "Dataset profile as of 2026-07-01",
    benchmark: "N/A",
    successCriteria: "Data confidence ≥ medium-high; no quarantine.",
    falsificationCriteria: "Quarantine or unresolved contamination.",
    lastRunAt: "2026-07-01T08:00:00.000Z",
    owner: "A. Chen",
    evidenceCount: 1,
    keyResult: "Medium-high confidence; primary panel provenance reviewed.",
    warnings: ["Crowding proxy still heuristic (not a DQ fail)."],
    nextAction: "Monitor dataset freshness before fold 4.",
    result: "Passed data confidence threshold.",
    metrics: [
      {
        key: "dq",
        label: "Data Confidence",
        value: "medium-high",
        basis: "historical",
      },
    ],
    gates: [
      gate(
        "g-dq-conf",
        "Data confidence threshold",
        "≥ medium",
        "medium-high",
        true,
        "blocking",
        "ev-mom-data"
      ),
      gate(
        "g-dq-coverage",
        "Required evidence coverage",
        "provenance complete",
        "complete",
        true,
        "info",
        "ev-mom-data"
      ),
    ],
    evidenceRefs: ["ev-mom-data"],
    dataConfidence: "high",
    limitations: ["Heuristic crowding field out of scope for DQ"],
    recommendation: "Pass for current ValidationRun inputs.",
    runHistory: [
      {
        id: "rh-data-1",
        ranAt: "2026-07-01T08:00:00.000Z",
        outcome: "Passed",
        note: "ValidationPassed data confidence.",
      },
    ],
  },
];

const MOMENTUM_BLOCKERS: ValidationBlocker[] = [
  {
    id: "blk-mom-stress",
    researchId: "rs-momentum-001",
    severity: "blocking",
    reason: "Stress performance exceeds the drawdown guardrail (−22.4% vs −20%).",
    affectedStageId: "val-mom-stress",
    affectedStageName: "Stress Testing",
    requiredNextAction:
      "Revise stress overlay or universe constraints, then open a new ValidationRun.",
  },
  {
    id: "blk-mom-regime",
    researchId: "rs-momentum-001",
    severity: "warning",
    reason: "Regime analysis remains inconclusive due to competing taxonomies.",
    affectedStageId: "val-mom-regime",
    affectedStageName: "Regime Analysis",
    requiredNextAction: "Pin one published regime definition before reassessing.",
  },
  {
    id: "blk-mom-oos",
    researchId: "rs-momentum-001",
    severity: "warning",
    reason: "Out-of-sample fold coverage incomplete (3/5).",
    affectedStageId: "val-mom-oos",
    affectedStageName: "Out-of-Sample Validation",
    requiredNextAction: "Freeze universe and complete remaining walk-forward folds.",
  },
];

const RSI_STAGES: ValidationStage[] = [
  {
    id: "val-rsi-oos",
    researchId: "rs-rsi-002",
    stageKey: "out_of_sample",
    name: "Out-of-Sample Validation",
    status: "Passed",
    purpose: "OOS check for RSI mean reversion.",
    method: "Holdout with earnings filter prototype.",
    dataset: "S&P 100 constituents",
    dateRange: "2018-01-01 → 2023-12-31",
    benchmark: "Buy & hold large-cap sleeve",
    successCriteria: "OOS Sharpe ≥ 0.40",
    falsificationCriteria: "OOS Sharpe < 0.20",
    lastRunAt: "2026-07-01T15:30:00.000Z",
    owner: "M. Okonkwo",
    evidenceCount: 1,
    keyResult: "OOS Sharpe 0.41; thin 2022 sample.",
    warnings: ["Thin high-vol subsample"],
    nextAction: "Unblock earnings-calendar stress.",
    result: "Passed with limitations.",
    metrics: [
      {
        key: "oos_sharpe",
        label: "Out-of-Sample Sharpe",
        value: "0.41",
        basis: "historical",
      },
    ],
    gates: [
      gate("g-rsi-oos", "Positive out-of-sample Sharpe", "≥ 0.40", "0.41", true, "blocking", "ev-rsi-oos"),
    ],
    evidenceRefs: ["ev-rsi-oos"],
    dataConfidence: "medium",
    limitations: ["Thin 2022 coverage"],
    recommendation: "Continue validation — stress still blocked.",
    runHistory: [],
  },
  {
    id: "val-rsi-stress",
    researchId: "rs-rsi-002",
    stageKey: "stress_testing",
    name: "Stress Testing",
    status: "Not Started",
    purpose: "Earnings-aligned stress battery.",
    method: "Pending calendar alignment.",
    dataset: "S&P 100 constituents",
    dateRange: "TBD",
    benchmark: "Buy & hold",
    successCriteria: "TBD after calendar join",
    falsificationCriteria: "TBD",
    lastRunAt: null,
    owner: "M. Okonkwo",
    evidenceCount: 0,
    keyResult: "Not started — blocked on earnings calendar.",
    warnings: ["Dataset join incomplete"],
    nextAction: "Align earnings calendar, then prepare ValidationRun.",
    result: "Not Started",
    metrics: [],
    gates: [],
    evidenceRefs: [],
    dataConfidence: "degraded",
    limitations: ["Cannot start without calendar"],
    recommendation: "Do not advance.",
    runHistory: [],
  },
];

const RSI_BLOCKERS: ValidationBlocker[] = [
  {
    id: "blk-rsi-cal",
    researchId: "rs-rsi-002",
    severity: "blocking",
    reason: "Dataset confidence degraded — earnings calendar join incomplete.",
    affectedStageId: "val-rsi-stress",
    affectedStageName: "Stress Testing",
    requiredNextAction: "Complete calendar alignment before stress ValidationRun.",
  },
];

export const MOCK_VALIDATION_BY_RESEARCH: Record<string, ValidationPipelineSnapshot> = {
  "rs-momentum-001": {
    researchId: "rs-momentum-001",
    stages: MOMENTUM_STAGES,
    blockers: MOMENTUM_BLOCKERS,
    lastValidationAt: "2026-07-05T10:00:00.000Z",
  },
  "rs-rsi-002": {
    researchId: "rs-rsi-002",
    stages: RSI_STAGES,
    blockers: RSI_BLOCKERS,
    lastValidationAt: "2026-07-01T15:30:00.000Z",
  },
  "rs-pairs-003": {
    researchId: "rs-pairs-003",
    stages: [
      {
        id: "val-pairs-hist",
        researchId: "rs-pairs-003",
        stageKey: "historical_backtest",
        name: "Historical Backtest",
        status: "Passed",
        purpose: "Pairs holdout package.",
        method: "Holdout + cost stress.",
        dataset: "Sector ETF pairs set v3",
        dateRange: "2016-01-01 → 2024-12-31",
        benchmark: "Cash + sector-neutral",
        successCriteria: "Net Sharpe ≥ 0.70",
        falsificationCriteria: "Cointegration break without recovery",
        lastRunAt: "2026-06-15T11:00:00.000Z",
        owner: "S. Patel",
        evidenceCount: 2,
        keyResult: "Net Sharpe 0.92 — demo only.",
        warnings: [],
        nextAction: "Submit Evaluation package.",
        result: "Passed",
        metrics: [
          { key: "sharpe", label: "Sharpe Ratio", value: "0.92", basis: "historical" },
        ],
        gates: [
          gate("g-pairs-sharpe", "Minimum net Sharpe", "≥ 0.70", "0.92", true, "blocking", "ev-pairs-bt"),
        ],
        evidenceRefs: ["ev-pairs-bt", "exp-pairs-001"],
        dataConfidence: "high",
        limitations: [],
        recommendation: "Ready for Evaluation consideration.",
        runHistory: [],
      },
    ],
    blockers: [],
    lastValidationAt: "2026-06-15T11:00:00.000Z",
  },
};

function cloneStage(stage: ValidationStage): ValidationStage {
  return {
    ...stage,
    warnings: [...stage.warnings],
    metrics: stage.metrics.map((metric) => ({ ...metric })),
    gates: stage.gates.map((item) => ({ ...item })),
    evidenceRefs: [...stage.evidenceRefs],
    limitations: [...stage.limitations],
    runHistory: stage.runHistory.map((item) => ({ ...item })),
  };
}

export function getMockValidationPipeline(
  researchId: string
): ValidationPipelineSnapshot {
  const found = MOCK_VALIDATION_BY_RESEARCH[researchId];
  if (!found) {
    return {
      researchId,
      stages: [],
      blockers: [],
      lastValidationAt: null,
    };
  }
  return {
    researchId: found.researchId,
    stages: found.stages.map(cloneStage),
    blockers: found.blockers.map((item) => ({ ...item })),
    lastValidationAt: found.lastValidationAt,
  };
}

/** Timeline events derived from validation outcomes (session-local boundary). */
export function getMockValidationTimelineEvents(
  researchId: string
): ResearchTimelineEvent[] {
  const snapshot = getMockValidationPipeline(researchId);
  return snapshot.stages
    .filter((stage) => stage.lastRunAt)
    .map((stage) => {
      const kindLabel =
        stage.status === "Passed"
          ? "ValidationPassed"
          : stage.status === "Failed"
            ? "ValidationFailed"
            : stage.status === "Inconclusive"
              ? "ValidationInconclusive"
              : stage.status === "Invalidated"
                ? "ValidationInvalidated"
                : stage.status === "Running"
                  ? "ValidationStarted"
                  : "ValidationStarted";
      return {
        id: `tl-val-${stage.id}`,
        researchId,
        occurredAt: stage.lastRunAt as string,
        title: `${kindLabel}: ${stage.name}`,
        summary: stage.keyResult,
        kind: "validation" as const,
        sourceEntryId: stage.id,
      };
    });
}

export class MockValidationError extends Error {
  constructor(message = "Unable to load validation pipeline.") {
    super(message);
    this.name = "MockValidationError";
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

export async function loadMockValidationPipeline(
  researchId: string,
  options?: { delayMs?: number }
): Promise<ValidationPipelineSnapshot> {
  await delay(options?.delayMs ?? 360);
  if (shouldForceMockError()) {
    throw new MockValidationError(
      "Mock validation load failed. Remove mockError=1 from the URL or retry."
    );
  }
  return getMockValidationPipeline(researchId);
}
