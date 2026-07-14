import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useResearchValidation } from "@/components/features/research/validation/useResearchValidation";
import { API_USER_MESSAGES, ApiRequestError } from "@/lib/apiRequest";
import { fetchResearchValidation } from "@/lib/researchValidationApi";

vi.mock("@/lib/researchValidationApi", () => ({
  fetchResearchValidation: vi.fn(),
}));

const fetchMock = vi.mocked(fetchResearchValidation);

describe("useResearchValidation", () => {
  beforeEach(() => fetchMock.mockReset());

  it("does not request validation outside the canonical validation tab", () => {
    const { result } = renderHook(() =>
      useResearchValidation("ma-crossover-spy", false)
    );

    expect(result.current.status).toBe("idle");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("loads canonical validation and supports retry after an error", async () => {
    fetchMock
      .mockRejectedValueOnce(new Error("provider unavailable"))
      .mockResolvedValueOnce({ research_id: "ma-crossover-spy" } as never);

    const { result } = renderHook(() =>
      useResearchValidation("ma-crossover-spy", true)
    );

    expect(result.current.status).toBe("loading");
    await waitFor(() => expect(result.current.status).toBe("error"));
    expect(result.current.validation).toBeNull();

    act(() => result.current.reload());
    await waitFor(() => expect(result.current.status).toBe("ready"));
    expect(result.current.validation?.research_id).toBe("ma-crossover-spy");
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("shows the provider-unavailable message without validation evidence", async () => {
    fetchMock.mockRejectedValueOnce(
      new ApiRequestError({
        category: "provider_unavailable",
        code: "HTTP_502",
      })
    );

    const { result } = renderHook(() =>
      useResearchValidation("ma-crossover-spy", true)
    );

    await waitFor(() => expect(result.current.status).toBe("error"));
    expect(result.current.error).toBe(API_USER_MESSAGES.provider_unavailable);
    expect(result.current.validation).toBeNull();
  });
});
