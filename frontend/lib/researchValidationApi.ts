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

export { ApiRequestError as ResearchValidationApiError };

export async function fetchResearchValidation(options?: {
  signal?: AbortSignal;
}): Promise<ResearchValidationResult> {
  return requestJson<ResearchValidationResult>(
    "/api/v1/research/validation",
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
        in_sample_ratio: 0.7,
      }),
    },
    { timeoutMs: API_REQUEST_TIMEOUT_MS }
  );
}
