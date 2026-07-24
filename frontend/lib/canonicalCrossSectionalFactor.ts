/**
 * Canonical Cross-Sectional Equity Factor Study — factor validation workflow.
 * Not a trading strategy. Metrics come only from Factor Validation engine.
 */

import type { CanonicalResearchPackage } from "@/types/canonicalResearch";
import type { FactorRunConfiguration } from "@/types/research";

export const CANONICAL_FACTOR_RESEARCH_ID = "cross-sectional-factor-sector-etfs";

const DEFINITION_DOCUMENTED_AT = "2026-07-24T08:00:00.000Z";

export const CANONICAL_FACTOR_RUN_CONFIGURATION: FactorRunConfiguration = {
  templateId: "cross_sectional_factor",
  universeId: "us_sector_etfs",
  factorId: "momentum",
  rebalanceFrequency: "monthly",
  holdingPeriodMonths: 1,
  startDate: "2018-01-01",
  endDate: null,
  transactionCost: 0.001,
};

export const CANONICAL_CROSS_SECTIONAL_FACTOR: CanonicalResearchPackage = {
  definition: {
    id: CANONICAL_FACTOR_RESEARCH_ID,
    name: "Cross-Sectional Equity Factor Study",
    researchQuestion:
      "Do simple cross-sectional Momentum and Low Volatility factors show persistent RankIC and quantile long–short separation on a liquid sector-ETF universe after stated turnover costs?",
    hypothesis:
      "Price-based Momentum (12-1) and Low Volatility may exhibit positive mean RankIC and Q5−Q1 separation, but edges can weaken after turnover costs and may be unstable across months.",
    researchObjective:
      "Validate factor predictive content with deterministic RankIC / ICIR and equal-weight Q1–Q5 portfolios — not to optimize or trade a portfolio.",
    strategyName: "Cross-Sectional Factor Validation",
    symbol: "US Sector ETFs",
    benchmark: "Equal-weight quantile long–short (Q5−Q1)",
    parameters: [
      { key: "universe", label: "Universe", value: "us_sector_etfs (10 sector ETFs)" },
      { key: "factor", label: "Factor", value: "momentum (low_volatility supported; value Coming Soon)" },
      { key: "rebalance", label: "Rebalance Frequency", value: "monthly" },
      { key: "holding", label: "Holding Period", value: "1 month" },
      {
        key: "transaction_cost",
        label: "Transaction Cost",
        value: "0.001 × long–short turnover",
      },
      {
        key: "quantiles",
        label: "Quantiles",
        value: "Q1–Q5 equal-count, equal-weight within bucket",
      },
    ],
    tags: ["cross-sectional-factor", "momentum", "factor-validation"],
    ownerLabel: "Research Workspace",
    publicityLabel: "Research Definition — Factor validation pending",
    explanatoryText:
      "This workspace defines a factor validation protocol (Universe, Factor, Rebalance, Holding Period). RankIC and quantile evidence are produced only by the Factor Validation engine — never invented in the UI.",
    dataRequirements: [
      "Daily OHLCV for the us_sector_etfs preset via MarketDataRouter",
      "Month-end factor panels and aligned forward returns",
      "Transparent provenance per symbol",
    ],
  },
  plannedExperiments: [
    {
      id: "exp-factor-rankic",
      name: "RankIC / ICIR Panel — Planned",
      experimentType: "Factor Test",
      hypothesis:
        "Monthly RankIC for the selected factor is not zero on average over the planned window.",
      successCriteria:
        "Publish mean/median RankIC, positive IC %, and ICIR from calculated series only.",
      falsificationCondition:
        "Mean RankIC near zero with unstable sign and no documented regime explanation.",
      notes: "Pure calculation — no LLM metrics.",
      parameters: [
        { key: "factor", label: "Factor", value: "momentum | low_volatility" },
        { key: "rebalance", label: "Rebalance", value: "monthly" },
      ],
    },
    {
      id: "exp-factor-quantile",
      name: "Quantile Portfolio Validation — Planned",
      experimentType: "Factor Test",
      hypothesis:
        "Equal-weight Q5−Q1 cumulative return and turnover-aware costs document whether separation survives stated costs.",
      successCriteria:
        "Report Q1–Q5 period/cumulative returns, LS, mean turnover, and total transaction cost from the engine.",
      falsificationCondition:
        "Q5−Q1 collapses or reverses after costs without acknowledgment.",
      notes: "No optimization, risk model, or broker.",
      parameters: [
        { key: "quantiles", label: "Buckets", value: "Q1–Q5" },
        { key: "cost_rate", label: "Cost rate", value: "0.001" },
      ],
    },
  ],
  plannedValidationStages: [
    {
      id: "val-factor-rankic",
      name: "RankIC Validation",
      status: "awaiting_data",
      description: "Awaiting Factor Validation engine RankIC / ICIR series.",
    },
    {
      id: "val-factor-quantile",
      name: "Quantile Portfolio Validation",
      status: "not_started",
      description: "Not started — Q1–Q5, long–short, turnover, and costs.",
    },
    {
      id: "val-factor-stability",
      name: "IC Stability Review",
      status: "not_started",
      description: "Not started — rolling IC and warning review from calculated evidence.",
    },
  ],
  designNotes: [
    {
      id: "nb-factor-001",
      entryType: "Observation",
      title: "Factor validation scope",
      body: "Cross-sectional study on sector ETFs. Goal is factor validation (RankIC + quantiles), not portfolio construction or live trading.",
      tags: ["design", "scope"],
    },
    {
      id: "nb-factor-002",
      entryType: "Decision",
      title: "Freeze v1 factors",
      body: "Executable: Momentum (12-1), Low Volatility (−60d vol). Value remains Coming Soon (no fundamentals panel).",
      tags: ["design", "protocol"],
    },
  ],
  timelineEvents: [
    {
      id: "tl-factor-defined",
      title: "Research Definition Created",
      summary:
        "Canonical Cross-Sectional Equity Factor Study defined for the Research Hub.",
      kind: "stage_change",
      occurredAt: DEFINITION_DOCUMENTED_AT,
    },
    {
      id: "tl-factor-method",
      title: "Factor Validation Methodology Documented",
      summary:
        "Universe, monthly rebalance, RankIC + Q1–Q5 long–short protocol documented as design notes.",
      kind: "notebook_entry",
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
    evaluationPendingMessage: "Evaluation pending factor validation evidence",
  },
};

export function getCanonicalFactorResearchPackage(): CanonicalResearchPackage {
  return CANONICAL_CROSS_SECTIONAL_FACTOR;
}
