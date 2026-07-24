/**
 * Frontend client for deterministic validation evidence.
 * The browser only requests backend-derived results; it never calculates them.
 */

import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";
import {
  API_REQUEST_TIMEOUT_MS,
  ApiRequestError,
  requestJson,
} from "@/lib/apiRequest";
import type { ResearchValidationResult } from "@/types/researchValidation";
import {
  isFactorRunConfiguration,
  type ResearchRunConfiguration,
  type TrendFollowingRunConfiguration,
} from "@/types/research";

export { ApiRequestError as ResearchValidationApiError };

const DEFAULT_CONFIGURATION: TrendFollowingRunConfiguration = {
  templateId: "trend_following",
  symbol: "SPY",
  benchmark: "SPY",
  startDate: "2018-01-01",
  endDate: null,
  shortWindow: 20,
  longWindow: 60,
  transactionCost: 0.001,
  riskFreeRate: 0,
};

function activeCriterionThresholds(researchId: string): Record<string, number> {
  if (typeof window === "undefined") return {};
  try {
    const raw = window.localStorage.getItem(
      "quant.research.guidance-definitions.v1"
    );
    const criteria = JSON.parse(raw ?? "{}")?.[researchId]?.successCriteria;
    if (!Array.isArray(criteria)) return {};
    const mapping: Record<string, string> = {
      excess_return: "min_excess_return",
      sharpe_difference: "min_sharpe_difference",
      drawdown_improvement: "min_drawdown_improvement",
      cost_adjusted_return: "min_cost_adjusted_return",
      robust_parameter_ratio: "min_robust_parameter_ratio",
      observation_count: "min_observations",
    };
    return Object.fromEntries(
      criteria
        .filter(
          (item: { active?: boolean; threshold?: unknown; metric?: string }) =>
            item?.active &&
            typeof item.threshold === "number" &&
            Number.isFinite(item.threshold) &&
            Boolean(item.metric && mapping[item.metric])
        )
        .map((item: { threshold: number; metric: string }) => [
          mapping[item.metric],
          item.threshold,
        ])
    );
  } catch {
    return {};
  }
}

function asTrendConfig(
  configuration?: ResearchRunConfiguration
): TrendFollowingRunConfiguration {
  if (isFactorRunConfiguration(configuration)) {
    throw new Error(
      "MA validation does not accept cross-sectional factor configuration."
    );
  }
  return configuration ?? DEFAULT_CONFIGURATION;
}

export async function fetchResearchValidation(options?: {
  signal?: AbortSignal;
  researchId?: string;
  configuration?: ResearchRunConfiguration;
}): Promise<ResearchValidationResult> {
  const configuration = asTrendConfig(options?.configuration);
  const researchId = options?.researchId ?? CANONICAL_RESEARCH_ID;
  return requestJson<ResearchValidationResult>(
    "/api/v1/research/validation",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: options?.signal,
      body: JSON.stringify({
        research_id: researchId,
        symbol: configuration.symbol,
        benchmark: configuration.benchmark,
        start_date: configuration.startDate,
        end_date: configuration.endDate,
        short_window: configuration.shortWindow,
        long_window: configuration.longWindow,
        transaction_cost: configuration.transactionCost,
        risk_free_rate: configuration.riskFreeRate,
        in_sample_ratio: 0.7,
        ...activeCriterionThresholds(researchId),
      }),
    },
    { timeoutMs: API_REQUEST_TIMEOUT_MS }
  );
}
