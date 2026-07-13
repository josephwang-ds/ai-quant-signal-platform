import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import ResearchValidation from "@/components/features/research/validation/ResearchValidation";
import { getMockResearchById } from "@/lib/mockResearchCatalog";

vi.mock("@/lib/mockValidationCatalog", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("@/lib/mockValidationCatalog")>();
  return {
    ...actual,
    loadMockValidationPipeline: vi.fn(async (researchId: string) =>
      actual.getMockValidationPipeline(researchId)
    ),
  };
});

const labels = {
  title: "Validation",
  stageCount: "pipeline stages",
  loading: "Loading validation pipeline…",
  errorTitle: "Validation unavailable",
  retry: "Retry",
  emptyTitle: "No validation stages yet",
  emptyDescription: "Validation stages appear when prepared.",
  filterEmptyTitle: "No validation stages match these filters",
  filterEmptyDescription: "Clear filters.",
  notFoundTitle: "Validation stage not found",
  notFoundDescription: "Missing stage.",
  backToPipeline: "Back to pipeline",
  runValidation: "Run Validation",
  runValidationHint: "Deferred governed workflow",
  demoLoading: "Demo loading state",
  overview: {
    title: "Pipeline overview",
    overallStatus: "Overall status",
    completed: "Completed checks",
    passed: "Passed",
    failed: "Failed",
    inconclusive: "Inconclusive",
    blocking: "Blocking issues",
    lastValidation: "Last validation",
    readiness: "Validation readiness",
    readinessNote: "Not investment advice.",
  },
  blockers: {
    title: "Blocking issues",
    description: "Issues that block advancement.",
    severity: "Severity",
    reason: "Reason",
    stage: "Affected stage",
    nextAction: "Required next action",
    empty: "No blockers.",
    inspect: "Inspect stage",
  },
  filters: {
    search: "Search",
    searchPlaceholder: "Search…",
    status: "Status",
    all: "All",
  },
  pipeline: {
    title: "Validation stages",
    card: {
      purpose: "Purpose",
      lastRun: "Last run",
      owner: "Owner",
      evidence: "Evidence count",
      keyResult: "Key result",
      warnings: "Warnings",
      nextAction: "Next action",
      openDetail: "Open detail",
    },
  },
  detail: {
    title: "Validation detail",
    close: "Close detail",
    purpose: "Purpose",
    method: "Method",
    dataset: "Dataset",
    dateRange: "Date range",
    benchmark: "Benchmark",
    successCriteria: "Success criteria",
    falsificationCriteria: "Falsification criteria",
    result: "Result",
    dataConfidence: "Data confidence",
    limitations: "Limitations",
    warnings: "Warnings",
    recommendation: "Recommendation",
    runHistory: "Run history",
    owner: "Owner",
    lastRun: "Last run",
    nextAction: "Next action",
    none: "None",
    evidenceTitle: "Evidence references",
    evidenceEmpty: "No evidence.",
    gates: {
      title: "Deterministic gates",
      rule: "Rule",
      threshold: "Threshold",
      observed: "Observed",
      result: "Result",
      severity: "Severity",
      evidence: "Evidence",
      pass: "Pass",
      fail: "Fail",
      empty: "No gates.",
      deterministicNote: "Deterministic mock rules.",
    },
    metrics: {
      title: "Metrics",
      disclaimer: "Demo metrics only.",
      historical: "historical",
      simulated: "simulated",
    },
  },
};

afterEach(() => {
  cleanup();
});

describe("ResearchValidation", () => {
  const research = getMockResearchById("rs-momentum-001");
  expect(research).not.toBeNull();

  it("renders the validation pipeline", async () => {
    render(
      <ResearchValidation
        research={research!}
        language="en"
        labels={labels}
        selectedStageId={null}
        onSelectStage={() => undefined}
      />
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Historical Backtest" })
      ).toBeInTheDocument();
    });
    expect(screen.getByText("Continue Validation")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Stress Testing" })).toBeInTheDocument();
    expect(
      screen.getByText(/Stress performance exceeds the drawdown guardrail/i)
    ).toBeInTheDocument();
  });

  it("filters by status", async () => {
    const user = userEvent.setup();
    render(
      <ResearchValidation
        research={research!}
        language="en"
        labels={labels}
        selectedStageId={null}
        onSelectStage={() => undefined}
      />
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Historical Backtest" })
      ).toBeInTheDocument();
    });

    await user.selectOptions(screen.getByLabelText("Status"), "Failed");
    expect(screen.getByRole("heading", { name: "Stress Testing" })).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Historical Backtest" })
    ).not.toBeInTheDocument();
  });

  it("opens validation detail with deterministic gates", async () => {
    const user = userEvent.setup();
    let selected: string | null = null;
    const onSelectStage = (id: string | null) => {
      selected = id;
    };

    const { rerender } = render(
      <ResearchValidation
        research={research!}
        language="en"
        labels={labels}
        selectedStageId={selected}
        onSelectStage={onSelectStage}
      />
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Stress Testing" })
      ).toBeInTheDocument();
    });

    const stressCard = screen
      .getByRole("heading", { name: "Stress Testing" })
      .closest("article");
    expect(stressCard).not.toBeNull();
    await user.click(within(stressCard!).getByRole("button", { name: "Open detail" }));
    expect(selected).toBe("val-mom-stress");

    rerender(
      <ResearchValidation
        research={research!}
        language="en"
        labels={labels}
        selectedStageId="val-mom-stress"
        onSelectStage={onSelectStage}
      />
    );

    await waitFor(() => {
      expect(screen.getByLabelText("Validation detail")).toBeInTheDocument();
    });
    expect(screen.getByText("Maximum drawdown threshold")).toBeInTheDocument();
    expect(screen.getAllByText("−22.4%").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Fail").length).toBeGreaterThan(0);
  });

  it("shows filter-empty state", async () => {
    const user = userEvent.setup();
    render(
      <ResearchValidation
        research={research!}
        language="en"
        labels={labels}
        selectedStageId={null}
        onSelectStage={() => undefined}
      />
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Historical Backtest" })
      ).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText("Search"), "zzzz-no-match");
    expect(
      screen.getByText("No validation stages match these filters")
    ).toBeInTheDocument();
  });

  it("shows loading skeleton before catalog resolves", async () => {
    const catalog = await import("@/lib/mockValidationCatalog");
    vi.mocked(catalog.loadMockValidationPipeline).mockImplementationOnce(
      () =>
        new Promise(() => {
          /* never resolve in this assertion window */
        })
    );

    render(
      <ResearchValidation
        research={research!}
        language="en"
        labels={labels}
        selectedStageId={null}
        onSelectStage={() => undefined}
      />
    );

    expect(screen.getByText("Loading validation pipeline…")).toBeInTheDocument();
  });

  it("shows empty state when catalog has no stages", async () => {
    const emptyResearch = getMockResearchById("rs-vol-004");
    expect(emptyResearch).not.toBeNull();

    render(
      <ResearchValidation
        research={emptyResearch!}
        language="en"
        labels={labels}
        selectedStageId={null}
        onSelectStage={() => undefined}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("No validation stages yet")).toBeInTheDocument();
    });
  });

  it("shows stage-not-found when selection is missing", async () => {
    render(
      <ResearchValidation
        research={research!}
        language="en"
        labels={labels}
        selectedStageId="val-missing"
        onSelectStage={() => undefined}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Validation stage not found")).toBeInTheDocument();
    });
  });

  it("keeps Run Validation disabled", async () => {
    render(
      <ResearchValidation
        research={research!}
        language="en"
        labels={labels}
        selectedStageId={null}
        onSelectStage={() => undefined}
      />
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Historical Backtest" })
      ).toBeInTheDocument();
    });

    expect(screen.getByRole("button", { name: "Run Validation" })).toBeDisabled();
  });
});
