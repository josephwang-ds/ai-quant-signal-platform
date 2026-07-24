import { API_REQUEST_TIMEOUT_MS, requestJson } from "@/lib/apiRequest";
import type {
  CompletionReviewResult,
  DraftResearchDefinitionResult,
  EvidenceReviewResult,
  HypothesisReviewResult,
  ResearchReviewerResponse,
} from "@/types/researchReviewer";

const REVIEWER_BASE = "/api/v1/research/reviewer";

function postReviewer<T>(
  path: string,
  body: Record<string, unknown>,
  signal?: AbortSignal
): Promise<ResearchReviewerResponse<T>> {
  return requestJson<ResearchReviewerResponse<T>>(
    `${REVIEWER_BASE}/${path}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
    },
    { timeoutMs: API_REQUEST_TIMEOUT_MS }
  );
}

export function draftResearchDefinition(
  body: Record<string, unknown>,
  signal?: AbortSignal
) {
  return postReviewer<DraftResearchDefinitionResult>(
    "draft-definition",
    body,
    signal
  );
}

export function reviewResearchHypothesis(
  body: Record<string, unknown>,
  signal?: AbortSignal
) {
  return postReviewer<HypothesisReviewResult>(
    "review-hypothesis",
    body,
    signal
  );
}

export function reviewResearchEvidence(
  body: Record<string, unknown>,
  signal?: AbortSignal
) {
  return postReviewer<EvidenceReviewResult>(
    "review-evidence",
    body,
    signal
  );
}

export function identifyMissingResearchSteps(
  body: Record<string, unknown>,
  signal?: AbortSignal
) {
  return postReviewer<CompletionReviewResult>(
    "identify-missing-steps",
    body,
    signal
  );
}
