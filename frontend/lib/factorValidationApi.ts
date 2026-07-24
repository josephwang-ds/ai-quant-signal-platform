/**
 * Client for POST /api/v1/research/factor-validation.
 * Browser never calculates RankIC or quantile metrics.
 */

import { CANONICAL_FACTOR_RESEARCH_ID } from "@/lib/canonicalCrossSectionalFactor";
import {
  API_REQUEST_TIMEOUT_MS,
  ApiRequestError,
  requestJson,
} from "@/lib/apiRequest";
import type { FactorValidationResult } from "@/types/factorValidation";
import type { FactorRunConfiguration } from "@/types/research";

export { ApiRequestError as FactorValidationApiError };

const DEFAULT_CONFIGURATION: FactorRunConfiguration = {
  templateId: "cross_sectional_factor",
  universeId: "us_sector_etfs",
  factorId: "momentum",
  rebalanceFrequency: "monthly",
  holdingPeriodMonths: 1,
  startDate: "2018-01-01",
  endDate: null,
  transactionCost: 0.001,
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
      mean_rank_ic: "min_mean_rank_ic",
      positive_ic_ratio: "min_positive_ic_ratio",
      q5_minus_q1_after_cost: "min_net_long_short_return",
      q5_excess_return: "min_q5_excess_return",
      mean_turnover: "max_mean_turnover",
      icir: "min_icir",
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

export async function fetchFactorValidation(options?: {
  signal?: AbortSignal;
  researchId?: string;
  configuration?: FactorRunConfiguration;
}): Promise<FactorValidationResult> {
  const configuration = options?.configuration ?? DEFAULT_CONFIGURATION;
  const researchId = options?.researchId ?? CANONICAL_FACTOR_RESEARCH_ID;
  return requestJson<FactorValidationResult>(
    "/api/v1/research/factor-validation",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: options?.signal,
      body: JSON.stringify({
        research_id: researchId,
        universe_id: configuration.universeId,
        factor_id: configuration.factorId,
        rebalance_frequency: configuration.rebalanceFrequency,
        holding_period_months: configuration.holdingPeriodMonths,
        start_date: configuration.startDate,
        end_date: configuration.endDate,
        transaction_cost: configuration.transactionCost,
        ...activeCriterionThresholds(researchId),
      }),
    },
    { timeoutMs: Math.max(API_REQUEST_TIMEOUT_MS, 120_000) }
  );
}
