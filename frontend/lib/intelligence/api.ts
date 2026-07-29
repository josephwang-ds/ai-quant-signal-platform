import { ApiConfigurationError, buildApiUrl } from "@/lib/apiConfig";
import {
  API_REQUEST_TIMEOUT_MS,
  API_USER_MESSAGES,
  fetchWithBackendReady,
} from "@/lib/apiRequest";
import {
  isIntelligenceApiErrorResponse,
  type ArtifactListDto,
  type IntelligenceApiErrorDetail,
  type ResearchRunDetailDto,
  type ResearchRunStatus,
  type ResearchRunType,
  type ResearchSnapshotType,
  type RunListDto,
  type SnapshotContentDto,
  type SnapshotListDto,
} from "@/lib/intelligence/types";

/**
 * Thin read-only intelligence transport (Phase 4.6A).
 *
 * Uses the shared stack: `buildApiUrl`, `fetchWithBackendReady` (warmup), and
 * `API_USER_MESSAGES`. Intentionally does not call `requestJson` because that
 * helper collapses FastAPI `detail` objects to a message string and drops the
 * Phase 4.5 `error_code` required for RUN_NOT_PUBLISHED / LATEST_NOT_FOUND
 * classification.
 */
type IntelligenceTransportCategory =
  | "configuration"
  | "network"
  | "timeout"
  | "backend_unavailable"
  | "rate_limited"
  | "invalid_request"
  | "not_found"
  | "server_error"
  | "unknown";

type RequestOptions = {
  timeoutMs?: number;
};

export class IntelligenceApiError extends Error {
  readonly category: IntelligenceTransportCategory;
  readonly transportCode: string;
  readonly status?: number;
  readonly backendCode?: string;
  readonly runId?: string | null;
  readonly resourceId?: string | null;
  readonly userMessage: string;
  readonly cause?: unknown;

  constructor(options: {
    category: IntelligenceTransportCategory;
    transportCode: string;
    status?: number;
    backend?: IntelligenceApiErrorDetail;
    userMessage?: string;
    cause?: unknown;
  }) {
    const userMessage = options.userMessage ?? resolveUserMessage(options.category);
    super(options.backend?.message ?? userMessage);
    this.name = "IntelligenceApiError";
    this.category = options.category;
    this.transportCode = options.transportCode;
    this.status = options.status;
    this.backendCode = options.backend?.error_code;
    this.runId = options.backend?.run_id;
    this.resourceId = options.backend?.resource_id;
    this.userMessage = userMessage;
    this.cause = options.cause;
  }
}

function resolveUserMessage(category: IntelligenceTransportCategory): string {
  switch (category) {
    case "configuration":
      return API_USER_MESSAGES.configuration;
    case "network":
      return API_USER_MESSAGES.network;
    case "timeout":
      return API_USER_MESSAGES.timeout;
    case "backend_unavailable":
      return API_USER_MESSAGES.backend_unavailable;
    case "rate_limited":
      return API_USER_MESSAGES.rate_limited;
    case "invalid_request":
      return API_USER_MESSAGES.invalid_request;
    case "not_found":
      return API_USER_MESSAGES.not_found;
    case "server_error":
      return API_USER_MESSAGES.server_error;
    default:
      return API_USER_MESSAGES.unknown;
  }
}

function categoryForStatus(status: number): IntelligenceTransportCategory {
  if (status === 400 || status === 409 || status === 422) return "invalid_request";
  if (status === 401 || status === 403) return "invalid_request";
  if (status === 404) return "not_found";
  if (status === 429) return "rate_limited";
  if (status === 503) return "backend_unavailable";
  if (status >= 500) return "server_error";
  return "unknown";
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException
    ? error.name === "AbortError"
    : Boolean(
        error &&
          typeof error === "object" &&
          "name" in error &&
          error.name === "AbortError"
      );
}

async function readErrorDetail(response: Response): Promise<IntelligenceApiErrorDetail | undefined> {
  try {
    const body = (await response.json()) as unknown;
    if (isIntelligenceApiErrorResponse(body)) {
      return body.detail;
    }
  } catch {
    return undefined;
  }
  return undefined;
}

async function requestIntelligenceJson<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  let url: string;
  try {
    url = buildApiUrl(path);
  } catch (error) {
    if (error instanceof ApiConfigurationError) {
      throw new IntelligenceApiError({
        category: "configuration",
        transportCode: error.code,
        cause: error,
      });
    }
    throw error;
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), options.timeoutMs ?? API_REQUEST_TIMEOUT_MS);

  try {
    const response = await fetchWithBackendReady(url, {
      cache: "no-store",
      headers: { Accept: "application/json" },
      signal: controller.signal,
    });

    if (!response.ok) {
      const backend = await readErrorDetail(response);
      throw new IntelligenceApiError({
        category: categoryForStatus(response.status),
        transportCode: `HTTP_${response.status}`,
        status: response.status,
        backend,
      });
    }

    try {
      return (await response.json()) as T;
    } catch (error) {
      throw new IntelligenceApiError({
        category: "unknown",
        transportCode: "INVALID_JSON_RESPONSE",
        cause: error,
      });
    }
  } catch (error) {
    if (error instanceof IntelligenceApiError) {
      throw error;
    }
    if (isAbortError(error)) {
      throw new IntelligenceApiError({
        category: "timeout",
        transportCode: "REQUEST_TIMEOUT",
        cause: error,
      });
    }
    if (error instanceof TypeError) {
      throw new IntelligenceApiError({
        category: "network",
        transportCode: "NETWORK_ERROR",
        cause: error,
      });
    }
    throw new IntelligenceApiError({
      category: "unknown",
      transportCode: "UNKNOWN_ERROR",
      cause: error,
    });
  } finally {
    clearTimeout(timeoutId);
  }
}

function withQuery(
  path: string,
  params: Record<string, string | undefined | null | boolean>
): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value == null || value === "") continue;
    query.set(key, String(value));
  }
  const suffix = query.toString();
  return suffix ? `${path}?${suffix}` : path;
}

export function listPublishedRuns(options: {
  status?: ResearchRunStatus;
  run_type?: ResearchRunType;
} = {}): Promise<RunListDto> {
  return requestIntelligenceJson<RunListDto>(
    withQuery("/api/v1/intelligence/runs", {
      status: options.status,
      run_type: options.run_type,
    })
  );
}

export function getLatestPublishedRun(): Promise<ResearchRunDetailDto> {
  return requestIntelligenceJson<ResearchRunDetailDto>("/api/v1/intelligence/runs/latest");
}

export function getPublishedRunDetail(runId: string): Promise<ResearchRunDetailDto> {
  return requestIntelligenceJson<ResearchRunDetailDto>(
    `/api/v1/intelligence/runs/${encodeURIComponent(runId)}`
  );
}

export function listPublishedRunArtifacts(runId: string): Promise<ArtifactListDto> {
  return requestIntelligenceJson<ArtifactListDto>(
    `/api/v1/intelligence/runs/${encodeURIComponent(runId)}/artifacts`
  );
}

export function listPublishedRunSnapshots(
  runId: string,
  options: { snapshot_type?: ResearchSnapshotType } = {}
): Promise<SnapshotListDto> {
  return requestIntelligenceJson<SnapshotListDto>(
    withQuery(`/api/v1/intelligence/runs/${encodeURIComponent(runId)}/snapshots`, {
      snapshot_type: options.snapshot_type,
    })
  );
}

export function getPublishedSnapshotContent(
  runId: string,
  snapshotNameOrId: string,
  options: { verify?: boolean } = {}
): Promise<SnapshotContentDto> {
  return requestIntelligenceJson<SnapshotContentDto>(
    withQuery(
      `/api/v1/intelligence/runs/${encodeURIComponent(
        runId
      )}/snapshots/${encodeURIComponent(snapshotNameOrId)}`,
      { verify: options.verify ? true : undefined }
    )
  );
}
