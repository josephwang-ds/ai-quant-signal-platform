import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import LifecycleProgress from "@/components/features/research/LifecycleProgress";
import ResearchPrimaryTabs from "@/components/features/research/ResearchPrimaryTabs";
import ResearchWorkspaceNavigation from "@/components/features/research/ResearchWorkspaceNavigation";
import OverviewSection from "@/components/features/research/OverviewSection";
import { overviewSectionTestLabels } from "@/components/features/research/overviewSectionTestLabels";
import {
  CANONICAL_RESEARCH_ID,
  getMockResearchById,
} from "@/lib/mockResearchCatalog";
import { deriveWorkflowStepStates } from "@/lib/researchWorkflow";

const navLabels = {
  overview: "Research",
  notebook: "Notes",
  experiments: "Experiment",
  validation: "Validation",
  evaluation: "Validation",
  robustness: "Robustness",
  paper: "Paper Observation",
  decision: "Decision",
  copilot: "Copilot",
  timeline: "Timeline",
};

const primaryTabLabels = {
  overview: "Research",
  experiments: "Experiment",
  validation: "Validation",
  robustness: "Robustness",
  paper: "Paper Observation",
  decision: "Decision",
  progressCompleted: "Completed",
  progressCurrent: "Current",
  progressLocked: "Locked",
};

describe("LifecycleProgress", () => {
  it("renders current-state labels for the active stage", () => {
    render(<LifecycleProgress currentStage="Synthesizing" />);

    expect(screen.getByText("Synthesizing")).toBeInTheDocument();
    expect(screen.getAllByText("Current")).toHaveLength(1);
  });
});

describe("ResearchPrimaryTabs", () => {
  it("shows completed, current, and locked progress on primary tabs", () => {
    const stepStates = deriveWorkflowStepStates({
      executionStatus: "ready",
      execution: { research_id: CANONICAL_RESEARCH_ID } as never,
      validationStatus: "idle",
      validation: null,
      evaluationStatus: "idle",
      evaluation: null,
    });

    render(
      <ResearchPrimaryTabs
        researchId={CANONICAL_RESEARCH_ID}
        activeSection="overview"
        stepStates={stepStates}
        labels={primaryTabLabels}
      />
    );

    expect(
      screen.getByRole("link", { name: "Research, Completed" })
    ).toHaveAttribute("data-progress", "completed");
    expect(
      screen.getByRole("link", { name: "Validation, Current" })
    ).toHaveAttribute("data-progress", "current");
    expect(
      screen.getByRole("link", { name: "Robustness, Locked" })
    ).toHaveAttribute("data-progress", "locked");
  });

  it("preserves guided review mode while moving through lifecycle tabs", () => {
    const stepStates = deriveWorkflowStepStates({
      executionStatus: "idle",
      execution: null,
      validationStatus: "idle",
      validation: null,
      evaluationStatus: "idle",
      evaluation: null,
    });

    render(
      <ResearchPrimaryTabs
        researchId={CANONICAL_RESEARCH_ID}
        activeSection="overview"
        stepStates={stepStates}
        labels={primaryTabLabels}
        reviewMode
      />
    );

    expect(
      screen.getByRole("link", { name: "Validation, Locked" })
    ).toHaveAttribute(
      "href",
      `/research/${CANONICAL_RESEARCH_ID}?tab=validation&review=1`
    );
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
    expect(screen.getByRole("link", { name: "Validation" })).toHaveAttribute(
      "href",
      `/research/${CANONICAL_RESEARCH_ID}?tab=validation`
    );
    expect(screen.getByRole("link", { name: "Paper Observation" })).toHaveAttribute(
      "href",
      `/research/${CANONICAL_RESEARCH_ID}?tab=paper`
    );
    // Evaluation tab is folded into Validation — no separate "Review" link.
    expect(screen.queryByRole("link", { name: "Review" })).not.toBeInTheDocument();
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
        onOpenSection={() => void 0}
        labels={overviewSectionTestLabels}
      />
    );

    expect(screen.getByText("Continue")).toBeInTheDocument();
    expect(
      screen.getByText("Run the research to calculate historical evidence.")
    ).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent(
      "Run the research to calculate historical evidence."
    );
    // Progress lives on the primary tab bar — not duplicated in Overview.
    expect(screen.queryByText("Progress")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Guided workflow")).not.toBeInTheDocument();
  });
});
