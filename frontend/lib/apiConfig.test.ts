import { afterEach, describe, expect, it, vi } from "vitest";
import {
  ApiConfigurationError,
  buildApiUrl,
  getApiBaseUrl,
} from "@/lib/apiConfig";

describe("API deployment configuration", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("uses the exact local development fallback when unset", () => {
    vi.stubEnv("NODE_ENV", "development");
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "");

    expect(getApiBaseUrl()).toBe("http://127.0.0.1:8000");
  });

  it("requires explicit configuration in production", () => {
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "  ");

    expect(() => getApiBaseUrl()).toThrow(ApiConfigurationError);
    expect(() => getApiBaseUrl()).not.toThrow(/localhost|127\.0\.0\.1|render/i);
  });

  it("trims whitespace and all trailing slashes", () => {
    vi.stubEnv(
      "NEXT_PUBLIC_API_BASE_URL",
      "  https://api.example.com/base///  "
    );

    expect(getApiBaseUrl()).toBe("https://api.example.com/base");
    expect(buildApiUrl("health")).toBe("https://api.example.com/base/health");
  });

  it.each(["not a url", "ftp://api.example.com", "file:///tmp/api"])(
    "rejects malformed or unsupported base URL %s",
    (value) => {
      vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", value);
      expect(() => getApiBaseUrl()).toThrow(ApiConfigurationError);
    }
  );

  it("normalizes leading slashes without allowing origin replacement", () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "https://api.example.com");

    expect(buildApiUrl("/api/v1/research")).toBe(
      "https://api.example.com/api/v1/research"
    );
    expect(() => buildApiUrl("https://evil.example/path")).toThrow(
      ApiConfigurationError
    );
    expect(() => buildApiUrl("//evil.example/path")).toThrow(
      ApiConfigurationError
    );
  });
});
