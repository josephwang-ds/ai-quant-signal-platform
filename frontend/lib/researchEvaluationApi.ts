/**
 * Frontend client for the research evaluation governance layer.
 * The browser only requests backend-derived evidence summaries; it never
 * calculates or infers evaluation status itself.
 */

import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";
import type { ResearchEvaluationResult } from "@/types/researchEvaluation";

function apiBase(): string {
  return (
    process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
    "http://127.0.0.1:8000"
  );
}

export class ResearchEvaluationApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ResearchEvaluationApiError";
    this.status = status;
  }
}

export async function fetchResearchEvaluation(
  validationRunId: string,
  options?: {
    signal?: AbortSignal;
  }
): Promise<ResearchEvaluationResult> {
  const response = await fetch(`${apiBase()}/api/v1/research/evaluation`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    signal: options?.signal,
    body: JSON.stringify({
      research_id: CANONICAL_RESEARCH_ID,
      validation_run_id: validationRunId,
    }),
  });

  if (!response.ok) {
    let detail = `Research evaluation failed (${response.status}).`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // Keep the status-bearing fallback when a provider returns a non-JSON error.
    }
    throw new ResearchEvaluationApiError(detail, response.status);
  }

  return (await response.json()) as ResearchEvaluationResult;
}
