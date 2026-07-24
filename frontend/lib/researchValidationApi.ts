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
  return requestJson<ResearchValidationResult>(
    "/api/v1/research/validation",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: options?.signal,
      body: JSON.stringify({
        research_id: options?.researchId ?? CANONICAL_RESEARCH_ID,
        symbol: configuration.symbol,
        benchmark: configuration.benchmark,
        start_date: configuration.startDate,
        end_date: configuration.endDate,
        short_window: configuration.shortWindow,
        long_window: configuration.longWindow,
        transaction_cost: configuration.transactionCost,
        risk_free_rate: configuration.riskFreeRate,
        in_sample_ratio: 0.7,
      }),
    },
    { timeoutMs: API_REQUEST_TIMEOUT_MS }
  );
}
