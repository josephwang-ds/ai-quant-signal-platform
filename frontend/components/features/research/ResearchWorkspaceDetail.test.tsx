import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import LifecycleProgress from "@/components/features/research/LifecycleProgress";
import ResearchWorkspaceNavigation from "@/components/features/research/ResearchWorkspaceNavigation";
import OverviewSection from "@/components/features/research/OverviewSection";
import { overviewSectionTestLabels } from "@/components/features/research/overviewSectionTestLabels";
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
        labels={overviewSectionTestLabels}
      />
    );

    expect(screen.getByText("Research Brief")).toBeInTheDocument();
    expect(
      screen.getByText("Run the research to calculate historical evidence.")
    ).toBeInTheDocument();
  });
});
