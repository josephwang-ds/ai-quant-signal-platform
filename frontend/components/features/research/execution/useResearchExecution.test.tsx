import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useResearchExecution } from "@/components/features/research/execution/useResearchExecution";
import { API_USER_MESSAGES, ApiRequestError, getApiDisplayMessage } from "@/lib/apiRequest";
import { fetchResearchExecution } from "@/lib/researchExecutionApi";

vi.mock("@/lib/researchExecutionApi", () => ({
  fetchResearchExecution: vi.fn(),
}));

const fetchMock = vi.mocked(fetchResearchExecution);

describe("useResearchExecution failure states", () => {
  beforeEach(() => fetchMock.mockReset());

  it.each([
    ["configuration", "API_CONFIGURATION_ERROR"],
    ["backend_unavailable", "HTTP_503"],
    ["provider_unavailable", "HTTP_502"],
  ] as const)("renders the stable %s message without metrics", async (category, code) => {
    fetchMock.mockRejectedValueOnce(
      new ApiRequestError({ category, code })
    );

    const { result } = renderHook(() =>
      useResearchExecution("ma-crossover-spy")
    );

    await waitFor(() => expect(result.current.status).toBe("error"));
    expect(result.current.error).toBe(API_USER_MESSAGES[category]);
    expect(result.current.execution).toBeNull();
  });

  it("renders safe backend detail for invalid requests", async () => {
    fetchMock.mockRejectedValueOnce(
      new ApiRequestError({
        category: "invalid_request",
        code: "HTTP_422",
        backendDetail: "short_window must be < long_window",
      })
    );

    const { result } = renderHook(() =>
      useResearchExecution("ma-crossover-spy")
    );

    await waitFor(() => expect(result.current.status).toBe("error"));
    expect(result.current.error).toBe(
      getApiDisplayMessage(
        new ApiRequestError({
          category: "invalid_request",
          code: "HTTP_422",
          backendDetail: "short_window must be < long_window",
        })
      )
    );
  });

  it("renders provider failures instead of invalid-request wording", async () => {
    fetchMock.mockRejectedValueOnce(
      new ApiRequestError({
        category: "provider_unavailable",
        code: "HTTP_502",
        backendDetail: "Column 'open' must be positive and valid.",
      })
    );

    const { result } = renderHook(() =>
      useResearchExecution("ma-crossover-spy")
    );

    await waitFor(() => expect(result.current.status).toBe("error"));
    expect(result.current.error).toContain(
      "Historical market data could not be retrieved."
    );
    expect(result.current.error).not.toContain("invalid");
  });
});
