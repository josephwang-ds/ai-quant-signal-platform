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
import type { ResearchRunConfiguration } from "@/types/research";

export { ApiRequestError as ResearchExecutionApiError };

const DEFAULT_CONFIGURATION: ResearchRunConfiguration = {
  symbol: "SPY",
  benchmark: "SPY",
  startDate: "2018-01-01",
  endDate: null,
  shortWindow: 20,
  longWindow: 60,
  transactionCost: 0.001,
  riskFreeRate: 0,
};

export async function fetchResearchExecution(options?: {
  signal?: AbortSignal;
  researchId?: string;
  configuration?: ResearchRunConfiguration;
}): Promise<ResearchExecutionResult> {
  const configuration = options?.configuration ?? DEFAULT_CONFIGURATION;
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
