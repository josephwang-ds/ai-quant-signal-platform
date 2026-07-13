import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import ResearchEvaluation from "@/components/features/research/evaluation/ResearchEvaluation";
import { getMockResearchById } from "@/lib/mockResearchCatalog";

vi.mock("@/lib/mockEvaluationCatalog", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("@/lib/mockEvaluationCatalog")>();
  return {
    ...actual,
    loadMockEvaluation: vi.fn(async (researchId: string) =>
      actual.getMockEvaluation(researchId) ??
      actual.getEmptyEvaluation(researchId)
    ),
  };
});

const labels = {
  title: "Evaluation",
  loading: "Loading evaluation…",
  errorTitle: "Evaluation unavailable",
  retry: "Retry",
  emptyTitle: "No evaluation dimensions yet",
  emptyDescription: "Prepare an Evaluation package.",
  filterEmptyTitle: "No dimensions match these filters",
  filterEmptyDescription: "Clear filters.",
  missingValidationTitle: "Missing validation data",
  missingValidationDescription: "Complete Validation first.",
  requestReview: "Request Review",
  requestReviewHint: "Deferred",
  demoLoading: "Demo loading state",
  demoError: "Demo error state",
  dimensionsTitle: "Evaluation dimensions",
  overview: {
    title: "Evaluation overview",
    confidence: {
      title: "Research Confidence",
      score: "Research Confidence score",
      level: "Confidence level",
      disclaimer:
        "Research Confidence measures the quality and completeness of the research process. It is not a forecast of future returns.",
      demoLabel: "Simulated Evaluation",
    },
    researchHealth: "Research Health",
    decisionReadiness: "Decision Readiness",
    recommendation: "Current recommendation",
    evaluationStatus: "Evaluation status",
    lastEvaluated: "Last evaluated",
    lifecycleStage: "Strategy lifecycle stage",
    dataConfidence: "Data confidence",
    blockers: "Number of blockers",
    evidenceCoverage: "Evidence coverage",
  },
  breakdown: {
    title: "Confidence breakdown",
    formula: "Demo formula",
    dimension: "Dimension",
    score: "Score",
    weight: "Weight",
    contribution: "Weighted contribution",
    status: "Status",
    total: "Research Confidence",
    weightsTotal: "Weights total",
  },
  readiness: {
    title: "Paper-trading readiness rules",
    description: "Deterministic rules",
    rule: "Rule",
    observed: "Observed",
    result: "Result",
    pass: "Pass",
    fail: "Fail",
  },
  blockers: {
    blockersTitle: "Critical blockers",
    warningsTitle: "Warnings",
    missingTitle: "Missing evidence",
    severity: "Severity",
    source: "Source",
    reason: "Reason",
    evidence: "Evidence",
    nextAction: "Next action",
    owner: "Owner",
    due: "Due",
    emptyBlockers: "No blockers",
    emptyWarnings: "No warnings",
    emptyMissing: "No missing",
  },
  strengthsWeaknesses: {
    title: "Strengths and weaknesses",
    strengths: "Strengths",
    weaknesses: "Weaknesses",
    empty: "None",
  },
  recommendation: {
    title: "Recommendation",
    current: "Current",
    why: "Why",
    blocking: "Blocking",
    nextActions: "Next actions",
    transition: "Transition",
    owner: "Owner",
    reassessment: "Reassessment",
    none: "None",
  },
  history: {
    title: "Evaluation history",
    date: "Date",
    score: "Score",
    recommendation: "Recommendation",
    change: "Change",
    trigger: "Trigger",
    superseded: "Superseded",
    active: "Current",
    empty: "No history",
  },
  filters: {
    search: "Search",
    searchPlaceholder: "Search…",
    status: "Status",
    all: "All",
  },
  dimensionCard: {
    score: "Score",
    weight: "Weight",
    contribution: "Contribution",
    evidence: "Evidence",
    evidenceEmpty: "No evidence",
    limitations: "Limitations",
    blocking: "Blocking",
    blockingYes: "Blocking",
    blockingNo: "No",
    lastUpdated: "Last updated",
    expand: "Expand",
    collapse: "Collapse",
    none: "None",
  },
};

afterEach(() => {
  cleanup();
});

describe("ResearchEvaluation", () => {
  const research = getMockResearchById("rs-momentum-001");
  expect(research).not.toBeNull();

  it("renders evaluation with derived score and demo label", async () => {
    render(
      <ResearchEvaluation
        research={research!}
        language="en"
        labels={labels}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Simulated Evaluation")).toBeInTheDocument();
    });
    expect(
      document.querySelector(".research-confidence-card__score")?.textContent
    ).toBe("81");
    expect(screen.getAllByText("Continue Validation").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Stress-test drawdown exceeds guardrail/i).length
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(/not a forecast of future returns/i)
    ).toBeInTheDocument();
  });

  it("renders evidence references and history", async () => {
    const user = userEvent.setup();
    render(
      <ResearchEvaluation
        research={research!}
        language="en"
        labels={labels}
      />
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Stress-Test Resilience" })
      ).toBeInTheDocument();
    });

    expect(screen.getByText("Evaluation history")).toBeInTheDocument();
    expect(screen.getByText(/82 → 81/)).toBeInTheDocument();

    const stressHeading = screen.getByRole("heading", {
      name: "Stress-Test Resilience",
    });
    const card = stressHeading.closest("article");
    expect(card).not.toBeNull();
    await user.click(
      card!.querySelector("button") as HTMLButtonElement
    );
    expect(screen.getAllByText("ev-mom-stress").length).toBeGreaterThan(0);
    expect(screen.getByText(/Observed stress DD/i)).toBeInTheDocument();
  });

  it("filters dimensions by status", async () => {
    const user = userEvent.setup();
    render(
      <ResearchEvaluation
        research={research!}
        language="en"
        labels={labels}
      />
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Historical Backtest Quality" })
      ).toBeInTheDocument();
    });

    await user.selectOptions(screen.getByLabelText("Status"), "Failed");
    expect(
      screen.getByRole("heading", { name: "Stress-Test Resilience" })
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Historical Backtest Quality" })
    ).not.toBeInTheDocument();
  });

  it("shows empty/missing validation state", async () => {
    const emptyResearch = getMockResearchById("rs-vol-004");
    expect(emptyResearch).not.toBeNull();

    render(
      <ResearchEvaluation
        research={emptyResearch!}
        language="en"
        labels={labels}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Missing validation data")).toBeInTheDocument();
    });
  });

  it("shows loading state", async () => {
    const catalog = await import("@/lib/mockEvaluationCatalog");
    vi.mocked(catalog.loadMockEvaluation).mockImplementationOnce(
      () =>
        new Promise(() => {
          /* pending */
        })
    );

    render(
      <ResearchEvaluation
        research={research!}
        language="en"
        labels={labels}
      />
    );

    expect(screen.getByText("Loading evaluation…")).toBeInTheDocument();
  });

  it("shows demo error state", async () => {
    const user = userEvent.setup();
    render(
      <ResearchEvaluation
        research={research!}
        language="en"
        labels={labels}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Simulated Evaluation")).toBeInTheDocument();
    });

    await user.click(screen.getByLabelText("Demo error state"));
    await waitFor(() => {
      expect(screen.getByText("Evaluation unavailable")).toBeInTheDocument();
    });
  });

  it("keeps Request Review disabled", async () => {
    render(
      <ResearchEvaluation
        research={research!}
        language="en"
        labels={labels}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Simulated Evaluation")).toBeInTheDocument();
    });

    expect(screen.getByRole("button", { name: "Request Review" })).toBeDisabled();
  });
});
