import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useResearchCopilot } from "@/components/features/research/copilot/useResearchCopilot";
import { ApiRequestError } from "@/lib/apiRequest";
import { fetchResearchCopilot } from "@/lib/researchCopilotApi";

vi.mock("@/lib/researchCopilotApi", () => ({
  fetchResearchCopilot: vi.fn(),
}));

const fetchMock = vi.mocked(fetchResearchCopilot);

describe("useResearchCopilot", () => {
  beforeEach(() => fetchMock.mockReset());

  it("does not request outside the canonical copilot tab", async () => {
    const { result } = renderHook(() =>
      useResearchCopilot("ma-crossover-spy", false, "val-abc")
    );

    await act(async () => {
      await result.current.ask("Why incomplete?");
    });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("reports awaiting_validation without a validation_run_id", () => {
    const { result } = renderHook(() =>
      useResearchCopilot("ma-crossover-spy", true, null)
    );

    expect(result.current.status).toBe("awaiting_validation");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("loads a grounded answer for a canonical question", async () => {
    fetchMock.mockResolvedValueOnce({
      research_id: "ma-crossover-spy",
      answer: "Evaluation is incomplete because stress testing is unavailable.",
      citations: [
        {
          source_type: "evaluation",
          source_id: "val-abc",
          label: "Outstanding evidence",
          excerpt: "Stress testing unavailable.",
        },
      ],
      warnings: [],
      grounding_status: "grounded",
      model: "fake-copilot-v1",
      generated_at: "2026-07-15T00:00:00Z",
    });

    const { result } = renderHook(() =>
      useResearchCopilot("ma-crossover-spy", true, "val-abc")
    );

    await act(async () => {
      await result.current.ask("Why is evaluation incomplete?");
    });

    await waitFor(() => expect(result.current.status).toBe("ready"));
    expect(result.current.result?.citations).toHaveLength(1);
    expect(fetchMock).toHaveBeenCalledWith("val-abc", "Why is evaluation incomplete?");
  });

  it("surfaces provider unavailable without fabricating an answer", async () => {
    const userMessage =
      "Research Copilot is not configured for this deployment.";
    fetchMock.mockRejectedValueOnce(
      new ApiRequestError({
        category: "backend_unavailable",
        code: "HTTP_503",
        status: 503,
        userMessage,
      })
    );

    const { result } = renderHook(() =>
      useResearchCopilot("ma-crossover-spy", true, "val-abc")
    );

    await act(async () => {
      await result.current.ask("What does OOS show?");
    });

    await waitFor(() => expect(result.current.status).toBe("error"));
    expect(result.current.result).toBeNull();
    expect(result.current.error).toBe(userMessage);
  });
});
