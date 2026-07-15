import { afterEach, describe, expect, it, vi } from "vitest";
import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";
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

  it("emits the canonical execution payload contract", async () => {
    const fetchMock = vi.fn().mockImplementation(async () =>
      new Response("{}", {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    await fetchResearchExecution();

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(JSON.parse(String(init.body))).toEqual({
      research_id: CANONICAL_RESEARCH_ID,
      symbol: "SPY",
      benchmark: "SPY",
      start_date: "2018-01-01",
      end_date: null,
      short_window: 20,
      long_window: 60,
      transaction_cost: 0.001,
      risk_free_rate: 0,
    });
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
