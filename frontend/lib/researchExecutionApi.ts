/**
 * Frontend client for POST /api/v1/research/execution.
 * Never calls Yahoo Finance from the browser.
 */

import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";
import type { ResearchExecutionResult } from "@/types/researchExecution";

function apiBase(): string {
  return (
    process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
    "http://127.0.0.1:8000"
  );
}

export class ResearchExecutionApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ResearchExecutionApiError";
    this.status = status;
  }
}

export async function fetchResearchExecution(options?: {
  signal?: AbortSignal;
}): Promise<ResearchExecutionResult> {
  const response = await fetch(`${apiBase()}/api/v1/research/execution`, {
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
  });

  if (!response.ok) {
    let detail = `Research execution failed (${response.status}).`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // keep default
    }
    throw new ResearchExecutionApiError(detail, response.status);
  }

  return (await response.json()) as ResearchExecutionResult;
}
