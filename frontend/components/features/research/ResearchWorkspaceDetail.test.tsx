import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import LifecycleProgress from "@/components/features/research/LifecycleProgress";
import ResearchWorkspaceNavigation from "@/components/features/research/ResearchWorkspaceNavigation";
import OverviewSection from "@/components/features/research/OverviewSection";
import {
  CANONICAL_RESEARCH_ID,
  getMockResearchById,
} from "@/lib/mockResearchCatalog";

const navLabels = {
  overview: "Overview",
  notebook: "Notes",
  experiments: "Experiments",
  validation: "Evidence",
  evaluation: "Review",
  copilot: "Copilot",
  timeline: "Timeline",
  files: "Files",
  settings: "Settings",
};

describe("LifecycleProgress", () => {
  it("renders current-state labels for the active stage", () => {
    render(<LifecycleProgress currentStage="Synthesizing" />);

    expect(screen.getByText("Synthesizing")).toBeInTheDocument();
    expect(screen.getAllByText("Current")).toHaveLength(1);
  });
});

describe("ResearchWorkspaceNavigation", () => {
  it("renders primary research sections and marks the active one", () => {
    render(
      <ResearchWorkspaceNavigation
        researchId={CANONICAL_RESEARCH_ID}
        activeSection="overview"
        labels={navLabels}
      />
    );

    expect(screen.getByRole("navigation", { name: /research workspace sections/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Notes" })).toHaveAttribute(
      "href",
      `/research/${CANONICAL_RESEARCH_ID}?tab=notebook`
    );
    expect(screen.getByRole("link", { name: "Evidence" })).toHaveAttribute(
      "href",
      `/research/${CANONICAL_RESEARCH_ID}?tab=validation`
    );
  });
});

describe("OverviewSection", () => {
  it("renders definition content without a numeric confidence score", () => {
    const research = getMockResearchById(CANONICAL_RESEARCH_ID);
    expect(research).not.toBeNull();

    render(
      <OverviewSection
        language="en"
        research={research!}
        executionStatus="idle"
        execution={null}
        validationStatus="idle"
        validation={null}
        evaluationStatus="idle"
        evaluation={null}
        onRunResearch={() => void 0}
        onRunValidation={() => void 0}
        onRequestEvaluation={() => void 0}
        onAskCopilot={() => void 0}
        labels={{
          briefTitle: "Research Brief",
          keyResultsTitle: "Key Results",
          guidedWorkflowTitle: "Guided workflow",
          conclusionTitle: "Research Conclusion",

          datasetPeriodLabel: "Dataset & period",
          strategyRuleLabel: "Strategy rule",
          evidenceStatusLabel: "Evidence",
          decisionStatusLabel: "Evaluation status",

          evidenceComplete: "Evidence complete",
          evidenceIncomplete: "Incomplete",
          evidencePending: "Not started",

          decisionPending: "Decision pending evidence and review.",
          evaluationCompleted: "Completed",
          evaluationIncomplete: "Incomplete",
          evaluationBlocked: "Blocked",

          coverageLabel: "Coverage",
          keyStrengthsLabel: "Key strengths",
          limitationLabel: "Known weaknesses",
          nextActionLabel: "Next actions",

          strategyTotalReturnLabel: "Strategy total return",
          benchmarkTotalReturnLabel: "Benchmark total return",
          maxDrawdownLabel: "Maximum drawdown",
          oosSharpeLabel: "Out-of-sample Sharpe ratio",

          keyResultsUnavailable: "Run the research to calculate historical evidence.",
          oosSharpeUnavailable: "Run validation to calculate out-of-sample Sharpe ratio.",

          stepRunResearch: "Run Research",
          stepValidateEvidence: "Validate evidence",
          stepReviewEvaluation: "Review evaluation",
          stepAskCopilot: "Ask Copilot",

          ctaRunResearch: "Run Research",
          ctaResearchLoading: "Research is running…",
          ctaRetryResearch: "Retry research",
          ctaRunValidation: "Run Validation",
          ctaRequestEvaluation: "Request Evaluation",
          ctaAskCopilot: "Ask Copilot",
        }}
      />
    );

    expect(screen.getByText("Research Brief")).toBeInTheDocument();
    expect(
      screen.getByText("Run the research to calculate historical evidence.")
    ).toBeInTheDocument();
  });
});
