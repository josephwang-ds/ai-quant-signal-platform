import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useState } from "react";
import ResearchExperiments from "@/components/features/research/experiments/ResearchExperiments";
import ExperimentLifecycle from "@/components/features/research/experiments/ExperimentLifecycle";
import {
  CANONICAL_RESEARCH_ID,
  getMockResearchById,
} from "@/lib/mockResearchCatalog";
import type { ResearchExperiment } from "@/types/experiment";
import type { NotebookEntry, ResearchTimelineEvent } from "@/types/notebook";

vi.mock("@/lib/mockExperimentCatalog", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("@/lib/mockExperimentCatalog")>();
  return {
    ...actual,
    loadMockExperiments: vi.fn(async (researchId: string) =>
      actual.getMockExperiments(researchId)
    ),
  };
});

const detailLabels = {
  title: "Experiment detail",
  close: "Close detail",
  overview: "Overview",
  hypothesis: "Hypothesis",
  configuration: "Configuration",
  parameters: "Parameters",
  results: "Results",
  notes: "Notes",
  relatedEvidence: "Related evidence",
  linkedNotebook: "Linked notebook entries",
  validationReadiness: "Validation readiness",
  dataset: "Dataset",
  window: "Window",
  benchmark: "Benchmark",
  owner: "Owner",
  created: "Created",
  updated: "Updated",
  success: "Success",
  falsification: "Falsify",
  none: "None",
  lifecycle: {
    title: "Experiment lifecycle",
    description: "Lifecycle",
    completed: "Completed",
    current: "Current",
    upcoming: "Upcoming",
    terminalNote: "Terminal",
    governedNote: "Governed",
  },
  metrics: {
    title: "Metrics",
    disclaimer: "Demo only",
    sharpe: "Sharpe",
    cagr: "CAGR",
    maxDrawdown: "Max DD",
    volatility: "Vol",
    tradeCount: "Trades",
    winRate: "Win rate",
    totalTransactionCost: "Cost",
  },
};

const labels = {
  title: "Experiments",
  totalCount: "experiments",
  activeCount: "active",
  newExperiment: "New Experiment",
  loading: "Loading",
  errorTitle: "Error",
  retry: "Retry",
  emptyTitle: "No experiments yet",
  emptyDescription: "Design the first controlled test.",
  filterEmptyTitle: "No experiments match",
  filterEmptyDescription: "Clear filters.",
  notFoundTitle: "Experiment not found",
  notFoundDescription: "Missing.",
  backToList: "Back to experiments",
  filters: {
    search: "Search",
    searchPlaceholder: "Search…",
    status: "Status",
    type: "Type",
    sort: "Sort",
    all: "All",
    sortUpdated: "Updated",
    sortCreated: "Created",
    sortResult: "Result",
  },
  card: {
    hypothesis: "Hypothesis",
    dataset: "Dataset",
    window: "Window",
    benchmark: "Benchmark",
    owner: "Owner",
    updated: "Updated",
    result: "Result",
    readiness: "Readiness",
    parameters: "Parameters",
    linkedNotes: "Notes",
    openDetail: "Open detail",
    sharpe: "Sharpe",
    maxDrawdown: "Max DD",
  },
  composer: {
    title: "New experiment (Designed)",
    name: "Experiment name",
    hypothesis: "Hypothesis",
    experimentType: "Experiment type",
    dataset: "Dataset or symbol",
    startDate: "Start date",
    endDate: "End date",
    benchmark: "Benchmark",
    parameters: "Parameters",
    parametersHint: "key=value",
    successCriteria: "Success criteria",
    falsification: "Falsification condition",
    notes: "Notes",
    save: "Save as Designed",
    cancel: "Cancel",
    nameRequired: "Name required",
    hypothesisRequired: "Hypothesis required",
    typeRequired: "Type required",
    datasetRequired: "Dataset required",
    startRequired: "Start required",
    endRequired: "End required",
    dateRangeInvalid: "Range invalid",
    successRequired: "Success required",
    falsificationRequired: "Falsify required",
  },
  detail: detailLabels,
};

afterEach(() => {
  cleanup();
});

describe("ExperimentLifecycle", () => {
  it("renders current stage for Running experiments", () => {
    render(
      <ExperimentLifecycle status="Running" labels={detailLabels.lifecycle} />
    );
    expect(screen.getByText("Running")).toBeInTheDocument();
    expect(screen.getAllByText("Current")).toHaveLength(1);
  });
});

describe("ResearchExperiments", () => {
  const research = getMockResearchById(CANONICAL_RESEARCH_ID);
  expect(research).not.toBeNull();

  it("renders the canonical MA crossover experiment", async () => {
    render(
      <ResearchExperiments
        research={research!}
        language="en"
        labels={labels}
        sessionExperiments={[]}
        selectedExperimentId={null}
        onSelectExperiment={() => undefined}
        onExperimentDesigned={() => undefined}
      />
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "MA 20/60 baseline — SPY" })
      ).toBeInTheDocument();
    });
    expect(screen.getByText(/Pending \(execution engine\)/i)).toBeInTheDocument();
  });

  it("filters by status", async () => {
    const user = userEvent.setup();
    render(
      <ResearchExperiments
        research={research!}
        language="en"
        labels={labels}
        sessionExperiments={[]}
        selectedExperimentId={null}
        onSelectExperiment={() => undefined}
        onExperimentDesigned={() => undefined}
      />
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "MA 20/60 baseline — SPY" })
      ).toBeInTheDocument();
    });

    await user.selectOptions(screen.getByLabelText("Status"), "Running");
    expect(
      screen.queryByRole("heading", { name: "MA 20/60 baseline — SPY" })
    ).not.toBeInTheDocument();
    expect(screen.getByText("No experiments match")).toBeInTheDocument();
  });

  it("opens experiment detail on select", async () => {
    const user = userEvent.setup();

    function Harness() {
      const [selected, setSelected] = useState<string | null>(null);
      return (
        <ResearchExperiments
          research={research!}
          language="en"
          labels={labels}
          sessionExperiments={[]}
          selectedExperimentId={selected}
          onSelectExperiment={setSelected}
          onExperimentDesigned={() => undefined}
        />
      );
    }

    render(<Harness />);

    await waitFor(() => {
      expect(screen.getAllByRole("button", { name: "Open detail" })[0]).toBeEnabled();
    });

    await user.click(screen.getAllByRole("button", { name: "Open detail" })[0]);
    expect(
      screen.getByRole("region", { name: "Experiment detail" })
    ).toBeInTheDocument();
    expect(screen.getByText("Experiment lifecycle")).toBeInTheDocument();
  });

  it("validates new experiment composer", async () => {
    const user = userEvent.setup();
    render(
      <ResearchExperiments
        research={research!}
        language="en"
        labels={labels}
        sessionExperiments={[]}
        selectedExperimentId={null}
        onSelectExperiment={() => undefined}
        onExperimentDesigned={() => undefined}
      />
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "New Experiment" })).toBeEnabled();
    });

    await user.click(screen.getByRole("button", { name: "New Experiment" }));
    const composer = screen.getByRole("region", {
      name: "New experiment (Designed)",
    });
    await user.click(within(composer).getByRole("button", { name: "Save as Designed" }));
    expect(within(composer).getByText("Name required")).toBeInTheDocument();
    expect(within(composer).getByText("Hypothesis required")).toBeInTheDocument();
  });

  it("adds a Designed experiment after save", async () => {
    const user = userEvent.setup();

    function Harness() {
      const [session, setSession] = useState<ResearchExperiment[]>([]);
      const [selected, setSelected] = useState<string | null>(null);
      return (
        <ResearchExperiments
          research={research!}
          language="en"
          labels={labels}
          sessionExperiments={session}
          selectedExperimentId={selected}
          onSelectExperiment={setSelected}
          onExperimentDesigned={({ experiment }) => {
            setSession((prev) => [experiment, ...prev]);
            setSelected(experiment.id);
          }}
        />
      );
    }

    render(<Harness />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "New Experiment" })).toBeEnabled();
    });

    await user.click(screen.getByRole("button", { name: "New Experiment" }));
    const composer = screen.getByRole("region", {
      name: "New experiment (Designed)",
    });
    await user.type(within(composer).getByLabelText("Experiment name"), "Local MA test");
    await user.type(within(composer).getByLabelText("Hypothesis"), "Local hypothesis");
    await user.selectOptions(
      within(composer).getByLabelText("Experiment type"),
      "Backtest"
    );
    await user.type(within(composer).getByLabelText("Dataset or symbol"), "SPY");
    await user.type(within(composer).getByLabelText("Start date"), "2020-01-01");
    await user.type(within(composer).getByLabelText("End date"), "2021-01-01");
    await user.type(
      within(composer).getByLabelText("Success criteria"),
      "Sharpe > 0.5"
    );
    await user.type(
      within(composer).getByLabelText("Falsification condition"),
      "Sharpe < 0.2"
    );
    await user.click(within(composer).getByRole("button", { name: "Save as Designed" }));

    expect(
      screen.getByRole("heading", { name: "Local MA test" })
    ).toBeInTheDocument();
    const detail = screen.getByRole("region", { name: "Experiment detail" });
    expect(within(detail).getAllByText("Designed").length).toBeGreaterThan(0);
  });

  it("shows experiment not found for unknown selection", async () => {
    render(
      <ResearchExperiments
        research={research!}
        language="en"
        labels={labels}
        sessionExperiments={[]}
        selectedExperimentId="does-not-exist"
        onSelectExperiment={() => undefined}
        onExperimentDesigned={() => undefined}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Experiment not found")).toBeInTheDocument();
    });
  });
});

describe("empty experiments catalog", () => {
  it("shows empty state when experiment load returns none", async () => {
    const research = getMockResearchById(CANONICAL_RESEARCH_ID);
    expect(research).not.toBeNull();

    const { loadMockExperiments } = await import("@/lib/mockExperimentCatalog");
    vi.mocked(loadMockExperiments).mockResolvedValueOnce([]);

    render(
      <ResearchExperiments
        research={research!}
        language="en"
        labels={labels}
        sessionExperiments={[]}
        selectedExperimentId={null}
        onSelectExperiment={() => undefined}
        onExperimentDesigned={(_payload: {
          experiment: ResearchExperiment;
          notebookEntry: NotebookEntry;
          timelineEvent: ResearchTimelineEvent;
        }) => undefined}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("No experiments yet")).toBeInTheDocument();
    });
  });
});
