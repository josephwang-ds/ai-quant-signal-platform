/**
 * Frontend client for deterministic validation evidence.
 * The browser only requests backend-derived results; it never calculates them.
 */

import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";
import type { ResearchValidationResult } from "@/types/researchValidation";

function apiBase(): string {
  return (
    process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
    "http://127.0.0.1:8000"
  );
}

export class ResearchValidationApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ResearchValidationApiError";
    this.status = status;
  }
}

export async function fetchResearchValidation(options?: {
  signal?: AbortSignal;
}): Promise<ResearchValidationResult> {
  const response = await fetch(`${apiBase()}/api/v1/research/validation`, {
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
  });

  if (!response.ok) {
    let detail = `Research validation failed (${response.status}).`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // Keep the status-bearing fallback when a provider returns a non-JSON error.
    }
    throw new ResearchValidationApiError(detail, response.status);
  }

  return (await response.json()) as ResearchValidationResult;
}
