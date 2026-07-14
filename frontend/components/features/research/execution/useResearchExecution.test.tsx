import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useResearchExecution } from "@/components/features/research/execution/useResearchExecution";
import { API_USER_MESSAGES, ApiRequestError } from "@/lib/apiRequest";
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
});
