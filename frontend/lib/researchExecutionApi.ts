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

export { ApiRequestError as ResearchExecutionApiError };

export async function fetchResearchExecution(options?: {
  signal?: AbortSignal;
}): Promise<ResearchExecutionResult> {
  return requestJson<ResearchExecutionResult>(
    "/api/v1/research/execution",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: options?.signal,
      body: JSON.stringify({
        research_id: CANONICAL_RESEARCH_ID,
        symbol: "SPY",
        benchmark: "SPY",
        start_date: "2018-01-01",
        end_date: null,
        short_window: 20,
        long_window: 60,
        transaction_cost: 0.001,
        risk_free_rate: 0,
      }),
    },
    { timeoutMs: API_REQUEST_TIMEOUT_MS }
  );
}
