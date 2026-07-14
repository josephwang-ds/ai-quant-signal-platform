const DEVELOPMENT_API_BASE_URL = "http://127.0.0.1:8000";

export class ApiConfigurationError extends Error {
  readonly code = "API_CONFIGURATION_ERROR";

  constructor(message: string) {
    super(message);
    this.name = "ApiConfigurationError";
  }
}

export function isProductionRuntime(): boolean {
  return process.env.NODE_ENV === "production";
}

export function getApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();

  if (!configured) {
    if (isProductionRuntime()) {
      throw new ApiConfigurationError(
        "NEXT_PUBLIC_API_BASE_URL is required in production."
      );
    }
    return DEVELOPMENT_API_BASE_URL;
  }

  const normalized = configured.replace(/\/+$/, "");
  let parsed: URL;
  try {
    parsed = new URL(normalized);
  } catch {
    throw new ApiConfigurationError(
      "NEXT_PUBLIC_API_BASE_URL must be a valid absolute URL."
    );
  }

  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new ApiConfigurationError(
      "NEXT_PUBLIC_API_BASE_URL must use http or https."
    );
  }

  return normalized;
}

export function buildApiUrl(path: string): string {
  const trimmedPath = path.trim();
  if (
    /^[a-z][a-z\d+\-.]*:/i.test(trimmedPath) ||
    trimmedPath.startsWith("//")
  ) {
    throw new ApiConfigurationError(
      "API request paths must not replace the configured backend origin."
    );
  }

  const normalizedPath = trimmedPath.replace(/^\/+/, "");
  const baseUrl = getApiBaseUrl();
  return normalizedPath ? `${baseUrl}/${normalizedPath}` : baseUrl;
}
