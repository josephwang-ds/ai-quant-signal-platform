import { ApiRequestError } from "@/lib/apiRequest";
import { IntelligenceApiError } from "@/lib/intelligence/api";

export type IntelligenceErrorContext =
  | "latest_run"
  | "run_detail"
  | "run_artifacts"
  | "run_snapshots"
  | "snapshot_content";

export type IntelligenceUiErrorCategory =
  | "not_found"
  | "not_published"
  | "backend_unavailable"
  | "invalid_snapshot"
  | "malformed_response"
  | "unknown";

export type IntelligenceUiErrorReason =
  | "latest_missing"
  | "run_not_found"
  | "snapshot_not_found"
  | "run_not_published"
  | "snapshot_invalid"
  | "backend_unavailable"
  | "unknown";

export type IntelligenceUiError = {
  category: IntelligenceUiErrorCategory;
  reason: IntelligenceUiErrorReason;
  message: string;
  status?: number;
  transportCode?: string;
  backendCode?: string;
  runId?: string | null;
  resourceId?: string | null;
};

type ErrorDebugFields = Pick<
  IntelligenceUiError,
  "status" | "transportCode" | "backendCode" | "runId" | "resourceId"
>;

function makeUiError(
  category: IntelligenceUiErrorCategory,
  reason: IntelligenceUiErrorReason,
  message: string,
  source: ErrorDebugFields = {}
): IntelligenceUiError {
  return {
    category,
    reason,
    message,
    status: source.status,
    transportCode: source.transportCode,
    backendCode: source.backendCode,
    runId: source.runId,
    resourceId: source.resourceId,
  };
}

export function mapIntelligenceError(
  error: unknown,
  context: IntelligenceErrorContext
): IntelligenceUiError {
  if (error instanceof IntelligenceApiError) {
    if (error.transportCode === "INVALID_JSON_RESPONSE") {
      return makeUiError(
        "malformed_response",
        "unknown",
        "Published research response could not be interpreted safely.",
        error
      );
    }
    if (error.backendCode === "INVALID_RUN_ID") {
      return makeUiError(
        "malformed_response",
        "unknown",
        "This published research identity is unavailable.",
        error
      );
    }
    if (error.backendCode === "RUN_NOT_PUBLISHED") {
      return makeUiError(
        "not_published",
        "run_not_published",
        "This run is not available as published research.",
        error
      );
    }
    if (error.backendCode === "RUN_NOT_FOUND") {
      return makeUiError(
        "not_found",
        "run_not_found",
        "Published research run not found.",
        error
      );
    }
    if (error.backendCode === "SNAPSHOT_NOT_FOUND") {
      return makeUiError("not_found", "snapshot_not_found", error.userMessage, error);
    }
    if (
      error.backendCode === "SNAPSHOT_CONTENT_INVALID" ||
      error.backendCode === "SNAPSHOT_INTEGRITY_FAILED" ||
      error.backendCode === "INVALID_SNAPSHOT_TYPE"
    ) {
      return makeUiError("invalid_snapshot", "snapshot_invalid", error.userMessage, error);
    }
    if (
      error.category === "backend_unavailable" ||
      error.category === "network" ||
      error.category === "timeout" ||
      error.category === "rate_limited" ||
      error.category === "server_error"
    ) {
      return makeUiError(
        "backend_unavailable",
        "backend_unavailable",
        error.userMessage,
        error
      );
    }
    if (error.category === "not_found") {
      if (context === "latest_run") {
        return makeUiError("not_found", "latest_missing", error.userMessage, error);
      }
      if (context === "snapshot_content") {
        return makeUiError("not_found", "snapshot_not_found", error.userMessage, error);
      }
      return makeUiError(
        "not_found",
        "run_not_found",
        context === "run_detail"
          ? "Published research run not found."
          : error.userMessage,
        error
      );
    }
    return makeUiError("unknown", "unknown", error.userMessage, error);
  }

  if (error instanceof ApiRequestError) {
    if (error.code === "INVALID_JSON_RESPONSE") {
      return makeUiError("malformed_response", "unknown", error.userMessage, {
        status: error.status,
        transportCode: error.code,
      });
    }
    if (
      error.category === "backend_unavailable" ||
      error.category === "network" ||
      error.category === "timeout" ||
      error.category === "rate_limited" ||
      error.category === "server_error"
    ) {
      return makeUiError("backend_unavailable", "backend_unavailable", error.userMessage, {
        status: error.status,
        transportCode: error.code,
      });
    }
    if (error.category === "not_found") {
      return makeUiError(
        "not_found",
        context === "latest_run" ? "latest_missing" : "run_not_found",
        error.userMessage,
        {
          status: error.status,
          transportCode: error.code,
        }
      );
    }
  }

  return makeUiError("unknown", "unknown", "The published research request could not be completed.");
}

export function classifyLatestPublishedRunError(error: unknown): IntelligenceUiError {
  return mapIntelligenceError(error, "latest_run");
}

export function classifyPublishedRunDetailError(error: unknown): IntelligenceUiError {
  return mapIntelligenceError(error, "run_detail");
}
