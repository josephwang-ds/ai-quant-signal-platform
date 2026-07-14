/**
 * Frontend client for the research evaluation governance layer.
 * The browser only requests backend-derived evidence summaries; it never
 * calculates or infers evaluation status itself.
 */

import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";
import {
  API_REQUEST_TIMEOUT_MS,
  ApiRequestError,
  requestJson,
} from "@/lib/apiRequest";
import type { ResearchEvaluationResult } from "@/types/researchEvaluation";

export { ApiRequestError as ResearchEvaluationApiError };

export async function fetchResearchEvaluation(
  validationRunId: string,
  options?: {
    signal?: AbortSignal;
  }
): Promise<ResearchEvaluationResult> {
  return requestJson<ResearchEvaluationResult>(
    "/api/v1/research/evaluation",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: options?.signal,
      body: JSON.stringify({
        research_id: CANONICAL_RESEARCH_ID,
        validation_run_id: validationRunId,
      }),
    },
    {
      timeoutMs: API_REQUEST_TIMEOUT_MS,
      notFoundMessage:
        "Run or load Validation evidence before Evaluation can be generated.",
    }
  );
}
