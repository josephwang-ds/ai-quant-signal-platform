/**
 * Canonical MA Crossover research — single source of truth for Research List,
 * Detail, Notebook, Experiments, Validation, Evaluation, and Timeline.
 *
 * Do not invent market-derived metrics here. See docs/data/AUTHENTICITY_POLICY.md.
 */

import type { CanonicalResearchPackage } from "@/types/canonicalResearch";

export const CANONICAL_RESEARCH_ID = "ma-crossover-spy";

/** Product-definition event dates (methodology documentation), not backtest runs. */
const DEFINITION_DOCUMENTED_AT = "2026-07-14T04:00:00.000Z";

export const CANONICAL_MA_CROSSOVER: CanonicalResearchPackage = {
  definition: {
    id: CANONICAL_RESEARCH_ID,
    name: "MA Crossover Research",
    researchQuestion:
      "Does a simple MA20/MA60 crossover outperform SPY buy-and-hold after transaction costs over a long historical period?",
    hypothesis:
      "A medium-term moving-average crossover may reduce large drawdowns, but its performance advantage may weaken after transaction costs and during sideways markets.",
    researchObjective:
      "Define a reproducible MA20/MA60 protocol on SPY versus buy-and-hold, then obtain calculated evidence from the Research Execution Engine — never invent results in the UI.",
    strategyName: "Moving Average Crossover",
    symbol: "SPY",
    benchmark: "SPY Buy & Hold",
    parameters: [
      { key: "short_ma", label: "Short Window", value: "20" },
      { key: "long_ma", label: "Long Window", value: "60" },
      {
        key: "transaction_cost",
        label: "Transaction Cost",
        value: "0.001 per position change",
      },
      {
        key: "position_lag_days",
        label: "Position Lag",
        value: "1 trading day (no look-ahead)",
      },
      {
        key: "planned_window",
        label: "Planned History Window",
        value: "2018-01-01 → latest complete trading day",
      },
    ],
    tags: ["ma-crossover", "SPY", "research-definition"],
    ownerLabel: "Research Workspace",
    publicityLabel: "Research Definition — Calculated results pending",
    explanatoryText:
      "This workspace currently defines the research methodology and configuration. Market-derived evidence will be populated by the Research Execution Engine.",
    dataRequirements: [
      "Daily OHLCV (adjusted close preferred) for SPY from a historical provider",
      "Chronological series with validated non-empty bars and unique dates",
      "Same history available for both strategy and SPY buy-and-hold benchmark",
      "Transparent provenance: provider, symbol, actual range, retrieved_at",
    ],
  },
  plannedExperiments: [
    {
      id: "exp-ma-baseline",
      name: "MA20/60 Baseline Backtest — Planned",
      experimentType: "Backtest",
      hypothesis:
        "MA20/MA60 on SPY with one-day lagged positions and 0.001 cost per position change may differ from SPY buy-and-hold after costs.",
      successCriteria:
        "After costs, document whether risk-adjusted returns improve versus buy-and-hold on the planned window.",
      falsificationCondition:
        "After costs, no meaningful improvement versus buy-and-hold — or documented edge collapses under OOS / sensitivity.",
      notes: "Baseline protocol. Metrics not calculated until Research Execution Engine.",
      parameters: [
        { key: "short_ma", label: "Short Window", value: "20" },
        { key: "long_ma", label: "Long Window", value: "60" },
        { key: "transaction_cost", label: "Transaction Cost", value: "0.001" },
      ],
    },
    {
      id: "exp-ma-oos",
      name: "Chronological OOS Validation — Planned",
      experimentType: "Backtest",
      hypothesis:
        "A chronological in-sample / out-of-sample split (default 70/30) does not reverse the baseline conclusion by construction noise alone.",
      successCriteria:
        "OOS windows and split dates are published; outcomes derived from calculated series only.",
      falsificationCondition:
        "OOS evidence contradicts the baseline claim without a documented regime explanation.",
      notes: "Never shuffle time-series data. Split dates must be explicit.",
      parameters: [
        { key: "in_sample_ratio", label: "In-sample ratio", value: "0.70" },
        { key: "split", label: "Split method", value: "chronological" },
      ],
    },
    {
      id: "exp-ma-sensitivity",
      name: "Parameter Sensitivity Grid — Planned",
      experimentType: "Parameter Test",
      hypothesis:
        "A bounded short/long MA grid (short < long) shows whether the baseline is fragile to nearby parameters.",
      successCriteria:
        "Report grid outcomes from calculated runs — do not claim robustness from a single profitable backtest.",
      falsificationCondition:
        "Nearby valid (short < long) cells reverse the baseline claim without documentation.",
      notes: "Keep grid bounded for request latency.",
      parameters: [
        { key: "short_grid", label: "Short windows", value: "10, 20, 30" },
        { key: "long_grid", label: "Long windows", value: "50, 60, 100" },
      ],
    },
    {
      id: "exp-ma-costs",
      name: "Transaction-Cost Review — Planned",
      experimentType: "Cost Test",
      hypothesis:
        "Cost levels 0, 0.001, 0.002, and 0.005 change net expectancy in a documented way.",
      successCriteria:
        "Publish net metrics at each cost level from calculated runs.",
      falsificationCondition:
        "Edge disappears at or below the protocol cost without acknowledgment.",
      notes: "Cost applied only when position changes.",
      parameters: [
        { key: "cost_grid", label: "Cost grid", value: "0, 0.001, 0.002, 0.005" },
      ],
    },
    {
      id: "exp-ma-regime",
      name: "Regime Analysis — Planned",
      experimentType: "Regime Test",
      hypothesis:
        "Sideways or choppy regimes may weaken any crossover advantage versus buy-and-hold.",
      successCriteria:
        "Document regime definitions and calculated under/over-performance without inventing Sharpe labels.",
      falsificationCondition:
        "Regime rules cannot be reproduced from the published protocol.",
      notes: "Deferred calculation — definition only in this PR.",
      parameters: [
        { key: "focus", label: "Focus", value: "sideways / low-trend regimes" },
      ],
    },
  ],
  plannedValidationStages: [
    {
      id: "val-historical",
      name: "Historical Backtest",
      status: "awaiting_data",
      description:
        "Awaiting real historical prices from the Research Execution Engine.",
    },
    {
      id: "val-benchmark",
      name: "Benchmark Comparison",
      status: "not_started",
      description: "Not started — requires calculated strategy and benchmark series.",
    },
    {
      id: "val-oos",
      name: "Out-of-Sample Validation",
      status: "not_started",
      description: "Not started — chronological split only; no shuffled time series.",
    },
    {
      id: "val-sensitivity",
      name: "Parameter Sensitivity",
      status: "not_started",
      description: "Not started — bounded grid after baseline data is available.",
    },
    {
      id: "val-costs",
      name: "Transaction-Cost Review",
      status: "not_started",
      description: "Not started — evaluate documented cost grid on calculated returns.",
    },
    {
      id: "val-quality",
      name: "Data-Quality Review",
      status: "awaiting_data",
      description: "Awaiting market-data provenance and series validation.",
    },
  ],
  designNotes: [
    {
      id: "nb-ma-001",
      entryType: "Observation",
      title: "Research question framed",
      body: `## Research Design Notes\n\nDefine whether **MA20/MA60** on **SPY** can outperform **SPY buy-and-hold** after a **0.001** cost on each position change over a long historical window.\n\nThis entry documents scope only. No performance has been calculated.`,
      tags: ["design", "scope"],
    },
    {
      id: "nb-ma-002",
      entryType: "Hypothesis",
      title: "Primary hypothesis (design)",
      body: "A medium-term moving-average crossover may reduce large drawdowns, but its performance advantage may weaken after transaction costs and during sideways markets.\n\n*Research Design Notes — not a result.*",
      tags: ["design", "hypothesis"],
    },
    {
      id: "nb-ma-003",
      entryType: "Decision",
      title: "Freeze protocol parameters",
      body: `## Protocol (design)\n\n- Short window: **20**\n- Long window: **60**\n- Position = signal lagged **1** trading day\n- Transaction cost: **0.001** per position change\n- Benchmark: SPY Buy & Hold\n\nNo experiment results are recorded here.`,
      tags: ["design", "protocol"],
    },
    {
      id: "nb-ma-004",
      entryType: "Action",
      title: "Await Research Execution Engine",
      body: "Next: populate market-derived evidence from real historical data. Until then, validation and evaluation remain unavailable — do not invent metrics.",
      tags: ["design", "next-action"],
    },
  ],
  timelineEvents: [
    {
      id: "tl-ma-defined",
      title: "Research Definition Created",
      summary:
        "Canonical MA Crossover Research defined for the public Research Workspace.",
      kind: "stage_change",
      occurredAt: DEFINITION_DOCUMENTED_AT,
    },
    {
      id: "tl-ma-method",
      title: "Research Methodology Documented",
      summary:
        "MA20/MA60, lag-1 position, 0.001 cost, SPY vs buy-and-hold protocol documented as design notes.",
      kind: "notebook_entry",
      occurredAt: DEFINITION_DOCUMENTED_AT,
    },
    {
      id: "tl-ma-data",
      title: "Real Data Integration Planned",
      summary:
        "Market-derived evidence deferred to the Research Execution Engine (PR-008B+).",
      kind: "stage_change",
      occurredAt: DEFINITION_DOCUMENTED_AT,
    },
  ],
  runtimeMarketData: null,
  calculatedEvidence: null,
  evaluationResult: null,
  integrity: {
    operationalStatus: "Data Integration",
    progressStage: "Planning",
    dataStatus: "Awaiting Real Historical Data",
    metricsStatus: "Not Calculated",
    validationStatus: "Not Started",
    evaluationStatus: "Not Available",
    evaluationPendingMessage: "Evaluation pending real validation evidence",
  },
};

export function getCanonicalResearchPackage(): CanonicalResearchPackage {
  return CANONICAL_MA_CROSSOVER;
}
