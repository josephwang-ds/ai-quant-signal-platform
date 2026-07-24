import {
  isFactorRunConfiguration,
  type ResearchDetail,
} from "@/types/research";

export type ResearchGuidanceDefinition = {
  researchQuestion: string;
  hypothesis: string;
  nullHypothesis: string;
  mechanism: string;
  primaryBenchmark: string;
  successCriteria: ResearchSuccessCriterion[];
  failureCriteria: string[];
  requiredValidation: string[];
  knownLimitations: string[];
};

export type ResearchCriterionOperator =
  | "gte"
  | "lte"
  | "gt"
  | "lt"
  | "positive"
  | "non_negative";

export type ResearchSuccessCriterion = {
  criterionId: string;
  metric: string;
  operator: ResearchCriterionOperator;
  threshold: number | null;
  severity: "core" | "supporting" | "guardrail";
  description: string;
  source: "template" | "user" | "ai_proposed";
  active: boolean;
};

function criterion(
  criterionId: string,
  metric: string,
  operator: ResearchCriterionOperator,
  threshold: number | null,
  severity: ResearchSuccessCriterion["severity"],
  description: string
): ResearchSuccessCriterion {
  return {
    criterionId,
    metric,
    operator,
    threshold,
    severity,
    description,
    source: "template",
    active: true,
  };
}

export const RESEARCH_GUIDANCE_STORAGE_KEY =
  "quant.research.guidance-definitions.v1";

function factorTemplate(research: ResearchDetail): ResearchGuidanceDefinition {
  const config = isFactorRunConfiguration(research.runConfiguration)
    ? research.runConfiguration
    : null;
  const lowVol = config?.factorId === "low_volatility";
  return {
    researchQuestion: research.researchQuestion,
    hypothesis: research.hypothesis,
    nullHypothesis: lowVol
      ? "Low-volatility ranking does not improve subsequent risk-adjusted outcomes or stability relative to the equal-weight universe."
      : "Factor ranks have no meaningful relationship with subsequent return ranking, and the cost-adjusted Q5-minus-Q1 spread is not positive.",
    mechanism: lowVol
      ? "Lower-volatility securities may experience smaller drawdowns and more stable outcomes; the engine negates raw volatility so Q5 consistently means the strongest expected exposure."
      : "Relative performance persistence may carry into the next holding period, producing positive cross-sectional rank correlation.",
    primaryBenchmark: "Equal-weight universe return",
    successCriteria: [
      criterion(
        "factor-mean-rank-ic",
        "mean_rank_ic",
        "gte",
        0,
        "core",
        "Mean RankIC compared with the zero reference baseline."
      ),
      criterion(
        "factor-positive-ic-ratio",
        "positive_ic_ratio",
        "gte",
        0.5,
        "core",
        "Share of periods with positive cross-sectional RankIC."
      ),
      criterion(
        "factor-net-long-short",
        "q5_minus_q1_after_cost",
        "positive",
        0,
        "core",
        "Q5-minus-Q1 cumulative return after configured transaction costs."
      ),
      criterion(
        "factor-quantile-ordering",
        "quantile_monotonicity",
        "gte",
        0.75,
        "supporting",
        "Directional ordering across Q1 through Q5."
      ),
      criterion(
        "factor-turnover",
        "mean_turnover",
        "lte",
        2,
        "guardrail",
        "Turnover remains within the researcher-defined limit."
      ),
      criterion(
        "factor-subperiod-stability",
        "subperiod_mean_rank_ic",
        "non_negative",
        0,
        "core",
        "RankIC direction remains stable across chronological subperiods."
      ),
    ],
    failureCriteria: [
      "Cost-adjusted Q5-minus-Q1 return is non-positive.",
      "Factor direction contradicts the hypothesis.",
      "High turnover eliminates the raw spread.",
      "Evidence is concentrated in one chronological subperiod.",
      "The number of factor observations is below the configured minimum.",
    ],
    requiredValidation: [
      "RankIC and positive-IC-ratio calculation",
      "Q1–Q5 equal-weight portfolio comparison",
      "Cost-adjusted Q5-minus-Q1 review",
      "Turnover and chronological stability review",
      "Universe and data-provenance review",
    ],
    knownLimitations: [...research.knownWeaknesses],
  };
}

function trendTemplate(research: ResearchDetail): ResearchGuidanceDefinition {
  return {
    researchQuestion: research.researchQuestion,
    hypothesis: research.hypothesis,
    nullHypothesis:
      "After costs, the moving-average rule does not produce materially better risk-adjusted performance or drawdown control than same-asset Buy and Hold.",
    mechanism:
      "Persistent medium-term trends may reduce downside participation, while lagged signals may underperform during rapid reversals or strongly rising markets.",
    primaryBenchmark: `${research.configuration.symbol} Buy and Hold`,
    successCriteria: [
      criterion(
        "trend-excess-return",
        "excess_return",
        "gte",
        0,
        "core",
        "Strategy return after costs versus same-asset Buy and Hold."
      ),
      criterion(
        "trend-sharpe-difference",
        "sharpe_difference",
        "gte",
        0,
        "core",
        "Risk-adjusted performance versus Buy and Hold."
      ),
      criterion(
        "trend-drawdown-improvement",
        "drawdown_improvement",
        "gte",
        0.05,
        "supporting",
        "Material maximum-drawdown improvement versus Buy and Hold."
      ),
      criterion(
        "trend-cost-resilience",
        "cost_adjusted_return",
        "non_negative",
        0,
        "core",
        "Performance remains acceptable after configured transaction costs."
      ),
      criterion(
        "trend-parameter-robustness",
        "robust_parameter_ratio",
        "gte",
        0.5,
        "core",
        "The conclusion is not concentrated in one narrow parameter cell."
      ),
    ],
    failureCriteria: [
      "Benchmark underperformance occurs without meaningful risk reduction.",
      "Transaction costs eliminate the result.",
      "Out-of-sample evidence materially deteriorates.",
      "Parameter sensitivity is unstable.",
      "The observation count is below the configured minimum.",
    ],
    requiredValidation: [
      "Aligned same-asset Buy-and-Hold comparison",
      "Chronological out-of-sample validation",
      "Bounded parameter sensitivity",
      "Transaction-cost sensitivity",
      "Data-quality and provenance checks",
    ],
    knownLimitations: [...research.knownWeaknesses],
  };
}

export function buildResearchGuidanceTemplate(
  research: ResearchDetail
): ResearchGuidanceDefinition {
  return isFactorRunConfiguration(research.runConfiguration)
    ? factorTemplate(research)
    : trendTemplate(research);
}

type StoredDefinitions = Record<string, ResearchGuidanceDefinition>;

function readAll(): StoredDefinitions {
  if (typeof window === "undefined") return {};
  try {
    const value = window.localStorage.getItem(RESEARCH_GUIDANCE_STORAGE_KEY);
    if (!value) return {};
    const parsed = JSON.parse(value);
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function normalizeDefinition(
  value: ResearchGuidanceDefinition | undefined,
  fallback: ResearchGuidanceDefinition
): ResearchGuidanceDefinition {
  if (!value) return fallback;
  const rawCriteria = Array.isArray(value.successCriteria)
    ? value.successCriteria
    : [];
  const successCriteria = rawCriteria
    .map((item, index): ResearchSuccessCriterion | null => {
      if (typeof item === "string") {
        return {
          criterionId: `legacy-${index}`,
          metric: `legacy_criterion_${index + 1}`,
          operator: "gte",
          threshold: null,
          severity: "supporting",
          description: item,
          source: "user",
          active: false,
        };
      }
      if (!item || typeof item !== "object") return null;
      return item as ResearchSuccessCriterion;
    })
    .filter((item): item is ResearchSuccessCriterion => Boolean(item));
  return { ...fallback, ...value, successCriteria };
}

export function loadResearchGuidance(
  research: ResearchDetail
): ResearchGuidanceDefinition {
  const fallback = buildResearchGuidanceTemplate(research);
  return normalizeDefinition(readAll()[research.id], fallback);
}

export function saveResearchGuidance(
  researchId: string,
  definition: ResearchGuidanceDefinition
): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(
    RESEARCH_GUIDANCE_STORAGE_KEY,
    JSON.stringify({ ...readAll(), [researchId]: definition })
  );
}

export function buildAgentResearchDefinition(
  research: ResearchDetail
): Record<string, unknown> {
  const definition = loadResearchGuidance(research);
  const runConfiguration = research.runConfiguration;
  const factor = isFactorRunConfiguration(runConfiguration);
  const trendConfiguration =
    runConfiguration && !factor ? runConfiguration : undefined;
  const activeCriteria = definition.successCriteria
    .filter((item) => item.active)
    .map((item) => ({ ...item, status: "active" as const }));

  return {
    research_question: definition.researchQuestion,
    hypothesis: definition.hypothesis,
    null_hypothesis: definition.nullHypothesis,
    mechanism: definition.mechanism,
    benchmark: definition.primaryBenchmark,
    benchmark_symbol: factor
      ? undefined
      : trendConfiguration?.benchmark || research.configuration.benchmark,
    symbol: factor
      ? undefined
      : trendConfiguration?.symbol || research.configuration.symbol,
    universe: factor ? runConfiguration.universeId : undefined,
    evaluation_period: runConfiguration
      ? `${runConfiguration.startDate} → ${runConfiguration.endDate || "latest completed bar"}`
      : research.configuration.parameterLines?.join("; ") || "",
    success_criteria: activeCriteria,
    outcome_metrics: activeCriteria.map((item) => item.metric),
    failure_criteria: definition.failureCriteria,
    required_validation: definition.requiredValidation,
    known_limitations: definition.knownLimitations,
    known_weaknesses: definition.knownLimitations,
    run_configuration: runConfiguration || {},
  };
}
