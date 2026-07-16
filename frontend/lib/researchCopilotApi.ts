/**
 * Frontend client for POST /api/v1/research/copilot/query.
 * The browser never calls an LLM provider directly.
 */

import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";
import {
  API_REQUEST_TIMEOUT_MS,
  ApiRequestError,
  requestJson,
} from "@/lib/apiRequest";
import type { ResearchCopilotResult } from "@/types/researchCopilot";

export { ApiRequestError as ResearchCopilotApiError };

export async function fetchResearchCopilot(
  validationRunId: string,
  question: string,
  options?: {
    signal?: AbortSignal;
    researchId?: string;
  }
): Promise<ResearchCopilotResult> {
  return requestJson<ResearchCopilotResult>(
    "/api/v1/research/copilot/query",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: options?.signal,
      body: JSON.stringify({
        research_id: options?.researchId ?? CANONICAL_RESEARCH_ID,
        validation_run_id: validationRunId,
        question,
        conversation: [],
      }),
    },
    {
      timeoutMs: API_REQUEST_TIMEOUT_MS,
      notFoundMessage:
        "Run or load Validation evidence before asking evidence-specific questions.",
    }
  );
}
