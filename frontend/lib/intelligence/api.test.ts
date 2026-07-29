import { afterEach, describe, expect, it, vi } from "vitest";
import {
  getLatestPublishedRun,
  getPublishedRunDetail,
  getPublishedSnapshotContent,
  listPublishedRunArtifacts,
  listPublishedRunSnapshots,
  listPublishedRuns,
} from "@/lib/intelligence/api";
import {
  classifyLatestPublishedRunError,
  classifyPublishedRunDetailError,
  mapIntelligenceError,
} from "@/lib/intelligence/errorMap";
import { isIntelligenceApiErrorResponse } from "@/lib/intelligence/types";

describe("intelligence transport client", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("constructs the exact Phase 4.5 read-only endpoint URLs", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "https://api.example.com/");
    const fetchMock = vi.fn().mockImplementation(
      async () =>
        new Response("{}", {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
    );
    vi.stubGlobal("fetch", fetchMock);

    await listPublishedRuns({ status: "PUBLISHED", run_type: "MODEL" });
    await getLatestPublishedRun();
    await getPublishedRunDetail("run_20260728T041530Z_a1b2c3d4");
    await listPublishedRunArtifacts("run_20260728T041530Z_a1b2c3d4");
    await listPublishedRunSnapshots("run_20260728T041530Z_a1b2c3d4", {
      snapshot_type: "signal",
    });
    await getPublishedSnapshotContent(
      "run_20260728T041530Z_a1b2c3d4",
      "signals-daily",
      { verify: true }
    );

    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      "https://api.example.com/api/v1/intelligence/runs?status=PUBLISHED&run_type=MODEL",
      "https://api.example.com/api/v1/intelligence/runs/latest",
      "https://api.example.com/api/v1/intelligence/runs/run_20260728T041530Z_a1b2c3d4",
      "https://api.example.com/api/v1/intelligence/runs/run_20260728T041530Z_a1b2c3d4/artifacts",
      "https://api.example.com/api/v1/intelligence/runs/run_20260728T041530Z_a1b2c3d4/snapshots?snapshot_type=signal",
      "https://api.example.com/api/v1/intelligence/runs/run_20260728T041530Z_a1b2c3d4/snapshots/signals-daily?verify=true",
    ]);
  });

  it("uses the shared buildApiUrl + warmup fetch stack (no alternate client)", async () => {
    const { readFileSync } = await import("node:fs");
    const { join } = await import("node:path");
    const source = readFileSync(
      join(process.cwd(), "lib/intelligence/api.ts"),
      "utf8"
    );
    expect(source).toContain("buildApiUrl");
    expect(source).toContain("fetchWithBackendReady");
    expect(source).toContain("API_USER_MESSAGES");
    expect(source).not.toMatch(/from ["']axios["']/);
    expect(source).not.toContain("react-query");
    expect(source).not.toContain("useSWR");
  });  it("accepts nullable backend error fields in the runtime guard", () => {
    expect(
      isIntelligenceApiErrorResponse({
        detail: {
          error_code: "RUN_NOT_FOUND",
          message: "missing run",
          run_id: null,
          resource_id: null,
        },
      })
    ).toBe(true);
  });

  it("classifies latest-run 404 as an empty latest-missing condition", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            detail: {
              error_code: "LATEST_NOT_FOUND",
              message: "no latest published research run",
            },
          }),
          { status: 404, headers: { "Content-Type": "application/json" } }
        )
      )
    );

    await expect(getLatestPublishedRun()).rejects.toSatisfy((error) => {
      const mapped = classifyLatestPublishedRunError(error);
      expect(mapped.category).toBe("not_found");
      expect(mapped.reason).toBe("latest_missing");
      expect(mapped.backendCode).toBe("LATEST_NOT_FOUND");
      return true;
    });
  });

  it("classifies run-detail 404 as a run-not-found condition", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            detail: {
              error_code: "RUN_NOT_FOUND",
              message: "unknown run",
              run_id: "run_20260728T041530Z_a1b2c3d4",
            },
          }),
          { status: 404, headers: { "Content-Type": "application/json" } }
        )
      )
    );

    await expect(getPublishedRunDetail("run_20260728T041530Z_a1b2c3d4")).rejects.toSatisfy(
      (error) => {
        const mapped = classifyPublishedRunDetailError(error);
        expect(mapped.category).toBe("not_found");
        expect(mapped.reason).toBe("run_not_found");
        expect(mapped.backendCode).toBe("RUN_NOT_FOUND");
        return true;
      }
    );
  });

  it("classifies RUN_NOT_PUBLISHED as unavailable rather than empty", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            detail: {
              error_code: "RUN_NOT_PUBLISHED",
              message: "research run is not published for consumer access",
              run_id: "run_20260728T041530Z_a1b2c3d4",
            },
          }),
          { status: 403, headers: { "Content-Type": "application/json" } }
        )
      )
    );

    await expect(getPublishedRunDetail("run_20260728T041530Z_a1b2c3d4")).rejects.toSatisfy(
      (error) => {
        const mapped = classifyPublishedRunDetailError(error);
        expect(mapped.category).toBe("not_published");
        expect(mapped.reason).toBe("run_not_published");
        expect(mapped.backendCode).toBe("RUN_NOT_PUBLISHED");
        return true;
      }
    );
  });

  it("maps invalid snapshot responses without inventing fallback data", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            detail: {
              error_code: "SNAPSHOT_CONTENT_INVALID",
              message: "snapshot payload is invalid",
              resource_id: "signals-daily",
            },
          }),
          { status: 422, headers: { "Content-Type": "application/json" } }
        )
      )
    );

    await expect(
      getPublishedSnapshotContent(
        "run_20260728T041530Z_a1b2c3d4",
        "signals-daily"
      )
    ).rejects.toSatisfy((error) => {
      const mapped = mapIntelligenceError(error, "snapshot_content");
      expect(mapped.category).toBe("invalid_snapshot");
      expect(mapped.backendCode).toBe("SNAPSHOT_CONTENT_INVALID");
      return true;
    });
  });

  it("maps SNAPSHOT_NOT_FOUND separately from run-not-found", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(
        async () =>
          new Response(
            JSON.stringify({
              detail: {
                error_code: "SNAPSHOT_NOT_FOUND",
                message: "snapshot missing",
                resource_id: "signals-daily",
              },
            }),
            { status: 404, headers: { "Content-Type": "application/json" } }
          )
      )
    );

    await expect(
      getPublishedSnapshotContent(
        "run_20260728T041530Z_a1b2c3d4",
        "signals-daily"
      )
    ).rejects.toSatisfy((error) => {
      const mapped = mapIntelligenceError(error, "snapshot_content");
      expect(mapped.category).toBe("not_found");
      expect(mapped.reason).toBe("snapshot_not_found");
      expect(mapped.backendCode).toBe("SNAPSHOT_NOT_FOUND");
      return true;
    });
  });

  it("maps backend/network-style failures to backend_unavailable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(
        async () =>
          new Response(
            JSON.stringify({
              detail: {
                error_code: "INTELLIGENCE_STORAGE_ERROR",
                message: "storage unavailable",
              },
            }),
            { status: 503, headers: { "Content-Type": "application/json" } }
          )
      )
    );

    await expect(getLatestPublishedRun()).rejects.toSatisfy((error) => {
      const mapped = classifyLatestPublishedRunError(error);
      expect(mapped.category).toBe("backend_unavailable");
      expect(mapped.reason).toBe("backend_unavailable");
      return true;
    });
  });

  it("maps HTTP 429 to backend_unavailable with the rate-limit user message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("{}", { status: 429 }))
    );

    await expect(getLatestPublishedRun()).rejects.toSatisfy((error) => {
      const mapped = classifyLatestPublishedRunError(error);
      expect(mapped.category).toBe("backend_unavailable");
      expect(mapped.status).toBe(429);
      expect(mapped.transportCode).toBe("HTTP_429");
      expect(mapped.message.toLowerCase()).toContain("busy");
      return true;
    });
  });

  it("maps HTTP 401 through invalid_request without inventing fallback data", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("{}", { status: 401 }))
    );

    await expect(getPublishedRunDetail("run_20260728T041530Z_a1b2c3d4")).rejects.toSatisfy(
      (error) => {
        const mapped = classifyPublishedRunDetailError(error);
        expect(mapped.status).toBe(401);
        expect(mapped.transportCode).toBe("HTTP_401");
        expect(mapped.message.length).toBeGreaterThan(0);
        return true;
      }
    );
  });

  it("does not introduce automatic demo fallback when the backend is unavailable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(
        async () =>
          new Response(
            JSON.stringify({
              detail: {
                error_code: "INTELLIGENCE_STORAGE_ERROR",
                message: "storage unavailable",
              },
            }),
            { status: 503, headers: { "Content-Type": "application/json" } }
          )
      )
    );

    await expect(getLatestPublishedRun()).rejects.toBeTruthy();
    const source = (await import("node:fs")).readFileSync(
      (await import("node:path")).join(process.cwd(), "lib/intelligence/api.ts"),
      "utf8"
    );
    expect(source).not.toMatch(/DEMO_MODE|demoRuns|mockPublished/i);
  });
});
