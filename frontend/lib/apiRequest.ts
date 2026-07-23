import { ApiConfigurationError, buildApiUrl } from "@/lib/apiConfig";

export const API_REQUEST_TIMEOUT_MS = 60_000;
export const API_STATUS_TIMEOUT_MS = 5_000;
export const BACKEND_WARMUP_TIMEOUT_MS = 90_000;

const BACKEND_READY_TTL_MS = 60_000;
const BACKEND_WARMUP_ATTEMPT_TIMEOUT_MS = 70_000;
const BACKEND_WARMUP_RETRY_BASE_MS = 1_000;
const BACKEND_WARMUP_RETRY_MAX_MS = 5_000;

export type ApiErrorCategory =
  | "configuration"
  | "network"
  | "timeout"
  | "backend_unavailable"
  | "provider_unavailable"
  | "invalid_request"
  | "not_found"
  | "server_error"
  | "unknown";

export const API_USER_MESSAGES: Record<ApiErrorCategory, string> = {
  configuration: "Backend API is not configured for this deployment.",
  network:
    "The research backend is currently unavailable or starting up. Try again shortly.",
  timeout:
    "The research backend is currently unavailable or starting up. Try again shortly.",
  backend_unavailable:
    "The research backend is currently unavailable or starting up. Try again shortly.",
  provider_unavailable:
    "Historical market data could not be retrieved. No fallback values were used.",
  invalid_request:
    "The research request is invalid. Review the configured parameters.",
  not_found: "The requested research evidence could not be found.",
  server_error:
    "The research backend returned an unexpected error. Try again shortly.",
  unknown: "The research request could not be completed.",
};

type ApiRequestErrorOptions = {
  category: ApiErrorCategory;
  code: string;
  status?: number;
  backendDetail?: string;
  userMessage?: string;
  cause?: unknown;
};

export class ApiRequestError extends Error {
  readonly category: ApiErrorCategory;
  readonly code: string;
  readonly status?: number;
  readonly backendDetail?: string;
  readonly userMessage: string;
  readonly cause?: unknown;

  constructor(options: ApiRequestErrorOptions) {
    const userMessage =
      options.userMessage ?? API_USER_MESSAGES[options.category];
    super(options.backendDetail ?? userMessage);
    this.name = "ApiRequestError";
    this.category = options.category;
    this.code = options.code;
    this.status = options.status;
    this.backendDetail = options.backendDetail;
    this.userMessage = userMessage;
    this.cause = options.cause;
  }
}

export type BackendReadinessState =
  | "idle"
  | "waking"
  | "ready"
  | "unavailable";

type BackendHealth = {
  status: string;
  service: string;
};

let backendReadinessState: BackendReadinessState = "idle";
let backendReadyUntil = 0;
let backendWarmupPromise: Promise<BackendHealth> | null = null;
const backendReadinessListeners = new Set<
  (state: BackendReadinessState) => void
>();

function publishBackendReadiness(state: BackendReadinessState): void {
  backendReadinessState = state;
  backendReadinessListeners.forEach((listener) => listener(state));
}

export function getBackendReadinessState(): BackendReadinessState {
  if (
    backendReadinessState === "ready" &&
    backendReadyUntil > 0 &&
    Date.now() >= backendReadyUntil
  ) {
    backendReadinessState = "idle";
  }
  return backendReadinessState;
}

export function subscribeBackendReadiness(
  listener: (state: BackendReadinessState) => void
): () => void {
  backendReadinessListeners.add(listener);
  return () => backendReadinessListeners.delete(listener);
}

function wait(delayMs: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, delayMs));
}

function configurationRequestError(error: ApiConfigurationError): ApiRequestError {
  return new ApiRequestError({
    category: "configuration",
    code: error.code,
    cause: error,
  });
}

async function runBackendWarmup(): Promise<BackendHealth> {
  let healthUrl: string;
  try {
    healthUrl = buildApiUrl("/health");
  } catch (error) {
    publishBackendReadiness("unavailable");
    if (error instanceof ApiConfigurationError) {
      throw configurationRequestError(error);
    }
    throw error;
  }

  publishBackendReadiness("waking");
  const deadline = Date.now() + BACKEND_WARMUP_TIMEOUT_MS;
  let attempt = 0;
  let lastError: unknown;

  while (Date.now() < deadline) {
    const remainingMs = deadline - Date.now();
    const controller = new AbortController();
    const timeoutId = setTimeout(
      () => controller.abort(),
      Math.min(BACKEND_WARMUP_ATTEMPT_TIMEOUT_MS, remainingMs)
    );

    try {
      const response = await fetch(healthUrl, {
        cache: "no-store",
        headers: { Accept: "application/json" },
        signal: controller.signal,
      });
      if (!response.ok) {
        throw new Error(`Backend warmup returned HTTP ${response.status}.`);
      }

      const health = (await response.json()) as Partial<BackendHealth>;
      if (health.status !== "ok" || typeof health.service !== "string") {
        throw new Error("Backend warmup returned an invalid health response.");
      }

      backendReadyUntil = Date.now() + BACKEND_READY_TTL_MS;
      publishBackendReadiness("ready");
      return health as BackendHealth;
    } catch (error) {
      lastError = error;
    } finally {
      clearTimeout(timeoutId);
    }

    attempt += 1;
    const remainingAfterAttempt = deadline - Date.now();
    if (remainingAfterAttempt <= 0) break;
    const retryDelayMs = Math.min(
      BACKEND_WARMUP_RETRY_BASE_MS * 2 ** Math.min(attempt - 1, 3),
      BACKEND_WARMUP_RETRY_MAX_MS,
      remainingAfterAttempt
    );
    await wait(retryDelayMs);
  }

  backendReadyUntil = 0;
  publishBackendReadiness("unavailable");
  throw new ApiRequestError({
    category: "backend_unavailable",
    code: "BACKEND_WARMUP_TIMEOUT",
    cause: lastError,
  });
}

/**
 * Wake the backend once and share that work across concurrent page requests.
 * Render free instances can take about a minute to spin up, so the UI keeps a
 * loading state while this bounded readiness gate runs instead of surfacing an
 * immediate error from every feature panel.
 */
export function warmBackend(options: { force?: boolean } = {}): Promise<BackendHealth> {
  if (
    !options.force &&
    getBackendReadinessState() === "ready" &&
    Date.now() < backendReadyUntil
  ) {
    return Promise.resolve({
      status: "ok",
      service: "ai-quant-signal-backend",
    });
  }

  if (backendWarmupPromise) {
    return backendWarmupPromise;
  }

  backendWarmupPromise = runBackendWarmup().finally(() => {
    backendWarmupPromise = null;
  });
  return backendWarmupPromise;
}

function shouldGateBackendRequest(): boolean {
  return process.env.NODE_ENV !== "test";
}

function throwIfAborted(signal?: AbortSignal | null): void {
  if (signal?.aborted) {
    throw new DOMException("Aborted", "AbortError");
  }
}

/** Fetch helper for legacy clients that still parse their own response bodies. */
export async function fetchWithBackendReady(
  input: RequestInfo | URL,
  init: RequestInit = {}
): Promise<Response> {
  throwIfAborted(init.signal);
  if (shouldGateBackendRequest()) {
    await warmBackend();
  }
  throwIfAborted(init.signal);
  return fetch(input, init);
}

export function resetBackendReadinessForTests(): void {
  backendReadinessState = "idle";
  backendReadyUntil = 0;
  backendWarmupPromise = null;
  backendReadinessListeners.clear();
}

export function getApiUserMessage(
  error: unknown,
  fallback = API_USER_MESSAGES.unknown
): string {
  return error instanceof ApiRequestError ? error.userMessage : fallback;
}

const UNSAFE_DETAIL_PATTERNS = [
  /traceback/i,
  /\bat\s+\S+\.py:\d+/i,
  /exception/i,
  /error:\s*\d+/i,
];

function isSafeBackendDetail(detail: string): boolean {
  const trimmed = detail.trim();
  if (!trimmed || trimmed.length > 280) {
    return false;
  }
  return !UNSAFE_DETAIL_PATTERNS.some((pattern) => pattern.test(trimmed));
}

function formatDetailSuffix(detail: string): string {
  const normalized = detail.trim().replace(/\s+/g, " ");
  return normalized.endsWith(".") ? normalized : `${normalized}.`;
}

export function getApiDisplayMessage(
  error: unknown,
  fallback = API_USER_MESSAGES.unknown
): string {
  if (!(error instanceof ApiRequestError)) {
    return fallback;
  }

  const detail =
    error.backendDetail && isSafeBackendDetail(error.backendDetail)
      ? formatDetailSuffix(error.backendDetail)
      : undefined;

  if (!detail) {
    return error.userMessage;
  }

  switch (error.category) {
    case "invalid_request":
      return `The research request is invalid: ${detail}`;
    case "provider_unavailable":
      return `Historical market data could not be retrieved. ${detail} No fallback values were used.`;
    case "backend_unavailable":
    case "network":
    case "timeout":
      return `${error.userMessage} ${detail}`;
    case "configuration":
      return error.userMessage;
    default:
      return `${error.userMessage} ${detail}`;
  }
}

type FastApiValidationError = {
  loc?: (string | number)[];
  msg?: string;
};

function parseStructuredDetail(value: unknown): string | undefined {
  if (typeof value === "string") {
    return value;
  }

  if (Array.isArray(value)) {
    const messages = value
      .map((item) => {
        if (!item || typeof item !== "object") {
          return undefined;
        }
        const error = item as FastApiValidationError;
        if (typeof error.msg !== "string") {
          return undefined;
        }
        const location = Array.isArray(error.loc)
          ? error.loc.filter((part) => part !== "body").join(".")
          : "";
        return location ? `${location}: ${error.msg}` : error.msg;
      })
      .filter((message): message is string => Boolean(message));
    return messages.length ? messages.join("; ") : undefined;
  }

  if (value && typeof value === "object") {
    const detail = value as Record<string, unknown>;
    if (typeof detail.message === "string") {
      return detail.message;
    }
  }

  return undefined;
}

async function readBackendDetail(response: Response): Promise<string | undefined> {
  try {
    const body = (await response.json()) as Record<string, unknown>;
    return parseStructuredDetail(body.detail) ?? parseStructuredDetail(body.message);
  } catch {
    return undefined;
  }
}

function categoryForStatus(status: number): ApiErrorCategory {
  if (status === 400 || status === 422) return "invalid_request";
  if (status === 404) return "not_found";
  if (status === 502) return "provider_unavailable";
  if (status === 503) return "backend_unavailable";
  if (status >= 500) return "server_error";
  return "unknown";
}

function isAbortError(error: unknown): boolean {
  return (
    error instanceof DOMException
      ? error.name === "AbortError"
      : Boolean(
          error &&
            typeof error === "object" &&
            "name" in error &&
            error.name === "AbortError"
        )
  );
}

export type ApiRequestOptions = {
  timeoutMs?: number;
  notFoundMessage?: string;
};

export async function requestJson<T>(
  path: string,
  init: RequestInit = {},
  options: ApiRequestOptions = {}
): Promise<T> {
  let url: string;
  try {
    url = buildApiUrl(path);
  } catch (error) {
    if (error instanceof ApiConfigurationError) {
      throw new ApiRequestError({
        category: "configuration",
        code: error.code,
        cause: error,
      });
    }
    throw error;
  }

  const timeoutMs = options.timeoutMs ?? API_REQUEST_TIMEOUT_MS;
  throwIfAborted(init.signal);
  if (shouldGateBackendRequest() && path !== "/health") {
    await warmBackend();
  }
  throwIfAborted(init.signal);
  const requestController = new AbortController();
  const callerSignal = init.signal;
  let timedOut = false;

  const abortFromCaller = () => requestController.abort(callerSignal?.reason);
  if (callerSignal?.aborted) {
    abortFromCaller();
  } else {
    callerSignal?.addEventListener("abort", abortFromCaller, { once: true });
  }

  const timeoutId = setTimeout(() => {
    timedOut = true;
    requestController.abort();
  }, timeoutMs);

  try {
    const response = await fetch(url, {
      ...init,
      signal: requestController.signal,
    });

    if (!response.ok) {
      const category = categoryForStatus(response.status);
      throw new ApiRequestError({
        category,
        code: `HTTP_${response.status}`,
        status: response.status,
        backendDetail: await readBackendDetail(response),
        userMessage:
          category === "not_found" ? options.notFoundMessage : undefined,
      });
    }

    try {
      return (await response.json()) as T;
    } catch (error) {
      throw new ApiRequestError({
        category: "unknown",
        code: "INVALID_JSON_RESPONSE",
        cause: error,
      });
    }
  } catch (error) {
    if (error instanceof ApiRequestError) {
      throw error;
    }
    if (isAbortError(error)) {
      if (!timedOut) {
        throw error;
      }
      throw new ApiRequestError({
        category: "timeout",
        code: "REQUEST_TIMEOUT",
        cause: error,
      });
    }
    if (error instanceof TypeError) {
      throw new ApiRequestError({
        category: "network",
        code: "NETWORK_ERROR",
        cause: error,
      });
    }
    throw new ApiRequestError({
      category: "unknown",
      code: "UNKNOWN_ERROR",
      cause: error,
    });
  } finally {
    clearTimeout(timeoutId);
    callerSignal?.removeEventListener("abort", abortFromCaller);
  }
}
