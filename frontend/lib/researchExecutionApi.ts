/**
 * Frontend client for POST /api/v1/research/execution.
 * Never calls Yahoo Finance from the browser.
 */

import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";
import {
  API_REQUEST_TIMEOUT_MS,
  ApiRequestError,
  requestJson,
} from "@/lib/apiRequest";
import type { ResearchExecutionResult } from "@/types/researchExecution";
import {
  isFactorRunConfiguration,
  type ResearchRunConfiguration,
  type TrendFollowingRunConfiguration,
} from "@/types/research";

export { ApiRequestError as ResearchExecutionApiError };

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
      "MA research execution does not accept cross-sectional factor configuration."
    );
  }
  return configuration ?? DEFAULT_CONFIGURATION;
}

export async function fetchResearchExecution(options?: {
  signal?: AbortSignal;
  researchId?: string;
  configuration?: ResearchRunConfiguration;
}): Promise<ResearchExecutionResult> {
  const configuration = asTrendConfig(options?.configuration);
  return requestJson<ResearchExecutionResult>(
    "/api/v1/research/execution",
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
      }),
    },
    { timeoutMs: API_REQUEST_TIMEOUT_MS }
  );
}
