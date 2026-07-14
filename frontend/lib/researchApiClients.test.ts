import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchResearchEvaluation } from "@/lib/researchEvaluationApi";
import { fetchResearchExecution } from "@/lib/researchExecutionApi";
import { fetchResearchValidation } from "@/lib/researchValidationApi";

describe("canonical research API clients", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("uses one normalized configured base URL for every canonical client", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", " https://api.example.com/// ");
    const fetchMock = vi.fn().mockImplementation(async () =>
        new Response("{}", {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
    );
    vi.stubGlobal("fetch", fetchMock);

    await fetchResearchExecution();
    await fetchResearchValidation();
    await fetchResearchEvaluation("validation-run");

    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      "https://api.example.com/api/v1/research/execution",
      "https://api.example.com/api/v1/research/validation",
      "https://api.example.com/api/v1/research/evaluation",
    ]);
  });

  it("gives evaluation 404 a missing-validation evidence message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({ detail: "Unknown validation_run_id 'missing'." }),
          {
            status: 404,
            headers: { "Content-Type": "application/json" },
          }
        )
      )
    );

    await expect(fetchResearchEvaluation("missing")).rejects.toMatchObject({
      category: "not_found",
      userMessage:
        "Run or load Validation evidence before Evaluation can be generated.",
      backendDetail: "Unknown validation_run_id 'missing'.",
    });
  });
});
