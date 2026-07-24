/**
 * Canonical Cross-Sectional Factor Studies — Momentum and Low Volatility demos.
 * Factor validation workflow only. Metrics come from the Factor Validation engine.
 */

import type { CanonicalResearchPackage } from "@/types/canonicalResearch";
import type { FactorId, FactorRunConfiguration } from "@/types/research";

/** Momentum demo (kept stable for existing bookmarks / tests). */
export const CANONICAL_FACTOR_RESEARCH_ID = "cross-sectional-factor-sector-etfs";
export const CANONICAL_MOMENTUM_FACTOR_RESEARCH_ID = CANONICAL_FACTOR_RESEARCH_ID;
export const CANONICAL_LOW_VOL_FACTOR_RESEARCH_ID =
  "cross-sectional-low-vol-sector-etfs";

export const CANONICAL_FACTOR_DEMO_IDS = [
  CANONICAL_MOMENTUM_FACTOR_RESEARCH_ID,
  CANONICAL_LOW_VOL_FACTOR_RESEARCH_ID,
] as const;

const DEFINITION_DOCUMENTED_AT = "2026-07-24T08:00:00.000Z";
const LOW_VOL_DOCUMENTED_AT = "2026-07-24T09:00:00.000Z";

const SHARED_UNIVERSE = "us_sector_etfs";
const SHARED_START = "2018-01-01";

function buildFactorRunConfiguration(
  factorId: Exclude<FactorId, "value">
): FactorRunConfiguration {
  return {
    templateId: "cross_sectional_factor",
    universeId: SHARED_UNIVERSE,
    factorId,
    rebalanceFrequency: "monthly",
    holdingPeriodMonths: 1,
    startDate: SHARED_START,
    endDate: null,
    transactionCost: 0.001,
  };
}

export const CANONICAL_FACTOR_RUN_CONFIGURATION =
  buildFactorRunConfiguration("momentum");
export const CANONICAL_MOMENTUM_RUN_CONFIGURATION =
  CANONICAL_FACTOR_RUN_CONFIGURATION;
export const CANONICAL_LOW_VOL_RUN_CONFIGURATION =
  buildFactorRunConfiguration("low_volatility");

function buildFactorPackage(input: {
  id: string;
  name: string;
  factorId: Exclude<FactorId, "value">;
  researchQuestion: string;
  hypothesis: string;
  successCriteria: string;
  documentedAt: string;
  tags: string[];
}): CanonicalResearchPackage {
  const factorLabel =
    input.factorId === "momentum" ? "Momentum (12-1)" : "Low Volatility (−60d vol)";
  return {
    definition: {
      id: input.id,
      name: input.name,
      researchQuestion: input.researchQuestion,
      hypothesis: input.hypothesis,
      researchObjective:
        "Validate factor predictive content with deterministic RankIC / ICIR and equal-weight Q1–Q5 portfolios — not to optimize or trade a portfolio.",
      strategyName: "Cross-Sectional Factor Validation",
      symbol: "US Sector ETFs",
      benchmark: "Equal-weight quantile long–short (Q5−Q1)",
      parameters: [
        {
          key: "universe",
          label: "Universe / Data",
          value: "us_sector_etfs (10 liquid sector ETFs)",
        },
        { key: "factor", label: "Factor", value: factorLabel },
        { key: "rebalance", label: "Rebalance Frequency", value: "monthly" },
        { key: "holding", label: "Holding Period", value: "1 month" },
        {
          key: "transaction_cost",
          label: "Transaction Cost",
          value: "0.001 × long–short turnover",
        },
        {
          key: "evaluation_protocol",
          label: "Evaluation Protocol",
          value: "Monthly RankIC + Q1–Q5 equal-weight; LS = Q5−Q1; costs on turnover",
        },
        {
          key: "success_criteria",
          label: "Success Criteria",
          value: input.successCriteria,
        },
        {
          key: "demo_label",
          label: "Demo Label",
          value: "Reproducible historical demonstration — not live trading",
        },
      ],
      tags: [...input.tags],
      ownerLabel: "Research Workspace",
      publicityLabel:
        "Research Definition — Reproducible historical demonstration; calculated results pending",
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
        id: `exp-${input.factorId}-rankic`,
        name: "RankIC / ICIR Panel — Planned",
        experimentType: "Factor Test",
        hypothesis: input.hypothesis,
        successCriteria: input.successCriteria,
        falsificationCondition:
          "Mean RankIC near zero with unstable sign and no documented regime explanation.",
        notes: "Pure calculation — no LLM metrics. Value factor is not runnable.",
        parameters: [
          { key: "factor", label: "Factor", value: input.factorId },
          { key: "rebalance", label: "Rebalance", value: "monthly" },
        ],
      },
      {
        id: `exp-${input.factorId}-quantile`,
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
        id: `val-${input.factorId}-rankic`,
        name: "RankIC Validation",
        status: "awaiting_data",
        description: "Awaiting Factor Validation engine RankIC / ICIR series.",
      },
      {
        id: `val-${input.factorId}-quantile`,
        name: "Quantile Portfolio Validation",
        status: "not_started",
        description: "Not started — Q1–Q5, long–short, turnover, and costs.",
      },
    ],
    designNotes: [
      {
        id: `nb-${input.factorId}-001`,
        entryType: "Observation",
        title: "Factor validation scope",
        body: "Cross-sectional study on sector ETFs. Goal is factor validation (RankIC + quantiles), not portfolio construction or live trading.",
        tags: ["design", "scope"],
      },
      {
        id: `nb-${input.factorId}-002`,
        entryType: "Decision",
        title: "Known limitations",
        body: "Static sector-ETF universe is not historical index membership. Survivorship and provider adjustments remain. Value is Coming Soon.",
        tags: ["design", "limitations"],
      },
    ],
    timelineEvents: [
      {
        id: `tl-${input.factorId}-defined`,
        title: "Research Definition Created",
        summary: `${input.name} defined as a reproducible historical demonstration.`,
        kind: "stage_change",
        occurredAt: input.documentedAt,
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
}

export const CANONICAL_CROSS_SECTIONAL_FACTOR = buildFactorPackage({
  id: CANONICAL_MOMENTUM_FACTOR_RESEARCH_ID,
  name: "Cross-Sectional Momentum Factor Study",
  factorId: "momentum",
  researchQuestion:
    "Do securities with stronger historical momentum earn higher subsequent cross-sectional returns after turnover and transaction costs?",
  hypothesis:
    "Relative performance persistence may produce positive RankIC and an economically meaningful Q5 minus Q1 spread.",
  successCriteria:
    "After costs, publish mean/median RankIC, positive IC %, ICIR, and Q5−Q1 net of turnover costs from calculated series only — do not claim success before validation runs.",
  documentedAt: DEFINITION_DOCUMENTED_AT,
  tags: ["cross-sectional-factor", "momentum", "factor-validation", "demo"],
});

export const CANONICAL_LOW_VOL_FACTOR = buildFactorPackage({
  id: CANONICAL_LOW_VOL_FACTOR_RESEARCH_ID,
  name: "Cross-Sectional Low Volatility Factor Study",
  factorId: "low_volatility",
  researchQuestion:
    "Do lower-volatility securities produce more stable subsequent risk-adjusted returns than higher-volatility securities?",
  hypothesis:
    "Lower-volatility securities may provide more stable outcomes, but the factor may not consistently generate positive raw long-short return.",
  successCriteria:
    "Publish RankIC summary and Q5−Q1 (gross and net of cost) from the engine; do not claim success before validation runs.",
  documentedAt: LOW_VOL_DOCUMENTED_AT,
  tags: ["cross-sectional-factor", "low-volatility", "factor-validation", "demo"],
});

/** @deprecated Prefer CANONICAL_CROSS_SECTIONAL_FACTOR (Momentum). */
export function getCanonicalFactorResearchPackage(): CanonicalResearchPackage {
  return CANONICAL_CROSS_SECTIONAL_FACTOR;
}

export function getCanonicalMomentumFactorPackage(): CanonicalResearchPackage {
  return CANONICAL_CROSS_SECTIONAL_FACTOR;
}

export function getCanonicalLowVolFactorPackage(): CanonicalResearchPackage {
  return CANONICAL_LOW_VOL_FACTOR;
}

export function isCanonicalFactorResearchId(researchId: string): boolean {
  return (CANONICAL_FACTOR_DEMO_IDS as readonly string[]).includes(researchId);
}
