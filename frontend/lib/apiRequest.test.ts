import { afterEach, describe, expect, it, vi } from "vitest";
import {
  API_USER_MESSAGES,
  ApiRequestError,
  requestJson,
} from "@/lib/apiRequest";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("shared API request transport", () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("fails configuration before fetch in production", async () => {
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "");
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    await expect(requestJson("/health")).rejects.toMatchObject({
      category: "configuration",
      userMessage: API_USER_MESSAGES.configuration,
    });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("classifies browser network failures", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    await expect(requestJson("/health")).rejects.toMatchObject({
      category: "network",
      code: "NETWORK_ERROR",
      userMessage: API_USER_MESSAGES.network,
    });
  });

  it.each([
    [400, "invalid_request"],
    [422, "invalid_request"],
    [404, "not_found"],
    [502, "provider_unavailable"],
    [503, "backend_unavailable"],
    [500, "server_error"],
  ] as const)("classifies HTTP %i as %s", async (status, category) => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse({ detail: "Backend detail" }, status))
    );

    await expect(requestJson("/api/test")).rejects.toMatchObject({
      category,
      status,
      backendDetail: "Backend detail",
    });
  });

  it("parses FastAPI validation arrays safely", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(
          { detail: [{ loc: ["body", "short_window"], msg: "Invalid value" }] },
          422
        )
      )
    );

    await expect(requestJson("/api/test")).rejects.toMatchObject({
      backendDetail: "short_window: Invalid value",
      userMessage: API_USER_MESSAGES.invalid_request,
    });
  });

  it("distinguishes a bounded timeout", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn((_url: string, init?: RequestInit) => {
        return new Promise((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () => {
            reject(new DOMException("Aborted", "AbortError"));
          });
        });
      })
    );

    const assertion = expect(
      requestJson("/api/test", {}, { timeoutMs: 25 })
    ).rejects.toMatchObject({
      category: "timeout",
      code: "REQUEST_TIMEOUT",
    });
    await vi.advanceTimersByTimeAsync(25);

    await assertion;
  });

  it("preserves caller abort as AbortError instead of timeout", async () => {
    const controller = new AbortController();
    vi.stubGlobal(
      "fetch",
      vi.fn((_url: string, init?: RequestInit) => {
        return new Promise((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () => {
            reject(new DOMException("Aborted", "AbortError"));
          });
        });
      })
    );

    const request = requestJson("/api/test", { signal: controller.signal });
    controller.abort();

    await expect(request).rejects.toMatchObject({ name: "AbortError" });
    await expect(request).rejects.not.toBeInstanceOf(ApiRequestError);
  });
});
