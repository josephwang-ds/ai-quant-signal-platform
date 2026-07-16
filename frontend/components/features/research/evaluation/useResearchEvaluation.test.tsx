import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useResearchEvaluation } from "@/components/features/research/evaluation/useResearchEvaluation";
import { ApiRequestError } from "@/lib/apiRequest";
import { fetchResearchEvaluation } from "@/lib/researchEvaluationApi";

vi.mock("@/lib/researchEvaluationApi", () => ({
  fetchResearchEvaluation: vi.fn(),
}));

const fetchMock = vi.mocked(fetchResearchEvaluation);

describe("useResearchEvaluation", () => {
  beforeEach(() => fetchMock.mockReset());

  it("does not request evaluation outside the canonical evaluation tab", () => {
    const { result } = renderHook(() =>
      useResearchEvaluation("ma-crossover-spy", false, "val-abc")
    );

    expect(result.current.status).toBe("idle");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("requests evaluation for a local MA research id", async () => {
    fetchMock.mockResolvedValueOnce({
      research_id: "some-other-research",
    } as never);
    const { result } = renderHook(() =>
      useResearchEvaluation("some-other-research", true, "val-abc")
    );

    await waitFor(() => expect(result.current.status).toBe("ready"));
    expect(fetchMock).toHaveBeenCalledWith(
      "val-abc",
      expect.objectContaining({ researchId: "some-other-research" })
    );
  });

  it("reports awaiting_validation and never calls the API without a validation_run_id", () => {
    const { result } = renderHook(() =>
      useResearchEvaluation("ma-crossover-spy", true, null)
    );

    expect(result.current.status).toBe("awaiting_validation");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("loads canonical evaluation using the supplied validation_run_id and supports retry after an error", async () => {
    fetchMock
      .mockRejectedValueOnce(new Error("evaluation unavailable"))
      .mockResolvedValueOnce({ research_id: "ma-crossover-spy" } as never);

    const { result } = renderHook(() =>
      useResearchEvaluation("ma-crossover-spy", true, "val-abc123")
    );

    expect(result.current.status).toBe("loading");
    await waitFor(() => expect(result.current.status).toBe("error"));
    expect(result.current.evaluation).toBeNull();

    act(() => result.current.reload());
    await waitFor(() => expect(result.current.status).toBe("ready"));
    expect(result.current.evaluation?.research_id).toBe("ma-crossover-spy");
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      "val-abc123",
      expect.objectContaining({ signal: expect.anything() })
    );
  });

  it("switches from awaiting_validation to loading once a validation_run_id becomes available", async () => {
    fetchMock.mockResolvedValueOnce({
      research_id: "ma-crossover-spy",
    } as never);

    const { result, rerender } = renderHook(
      ({ validationRunId }: { validationRunId: string | null }) =>
        useResearchEvaluation("ma-crossover-spy", true, validationRunId),
      { initialProps: { validationRunId: null as string | null } }
    );

    expect(result.current.status).toBe("awaiting_validation");
    expect(fetchMock).not.toHaveBeenCalled();

    rerender({ validationRunId: "val-xyz" });

    await waitFor(() => expect(result.current.status).toBe("ready"));
    expect(fetchMock).toHaveBeenCalledWith(
      "val-xyz",
      expect.objectContaining({ signal: expect.anything() })
    );
  });

  it("shows the stable missing-validation message for an evaluation 404", async () => {
    const userMessage =
      "Run or load Validation evidence before Evaluation can be generated.";
    fetchMock.mockRejectedValueOnce(
      new ApiRequestError({
        category: "not_found",
        code: "HTTP_404",
        status: 404,
        userMessage,
      })
    );

    const { result } = renderHook(() =>
      useResearchEvaluation("ma-crossover-spy", true, "missing")
    );

    await waitFor(() => expect(result.current.status).toBe("error"));
    expect(result.current.error).toBe(userMessage);
    expect(result.current.evaluation).toBeNull();
  });
});
