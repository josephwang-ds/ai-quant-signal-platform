import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import LifecycleProgress from "@/components/features/research/LifecycleProgress";
import ResearchWorkspaceNavigation from "@/components/features/research/ResearchWorkspaceNavigation";
import OverviewSection from "@/components/features/research/OverviewSection";
import { getMockResearchById } from "@/lib/mockResearchCatalog";

const navLabels = {
  overview: "Overview",
  notebook: "Notebook",
  experiments: "Experiments",
  validation: "Validation",
  evaluation: "Evaluation",
  timeline: "Timeline",
  files: "Files",
  settings: "Settings",
};

describe("LifecycleProgress", () => {
  it("renders current-state labels for the active stage", () => {
    render(<LifecycleProgress currentStage="Synthesizing" />);

    expect(screen.getByText("Synthesizing")).toBeInTheDocument();
    expect(screen.getAllByText("Current")).toHaveLength(1);
    expect(screen.getAllByText("Completed").length).toBeGreaterThanOrEqual(3);
    expect(screen.getAllByText("Upcoming").length).toBeGreaterThanOrEqual(2);
  });
});

describe("ResearchWorkspaceNavigation", () => {
  it("renders all workspace sections and marks the active one", () => {
    render(
      <ResearchWorkspaceNavigation
        researchId="rs-momentum-001"
        activeSection="overview"
        labels={navLabels}
      />
    );

    expect(screen.getByRole("navigation", { name: /research workspace sections/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Overview" })).toHaveAttribute(
      "aria-current",
      "page"
    );
    expect(screen.getByRole("link", { name: "Notebook" })).toHaveAttribute(
      "href",
      "/research/rs-momentum-001?tab=notebook"
    );
  });
});

describe("OverviewSection", () => {
  it("renders research detail content for the selected project", () => {
    const research = getMockResearchById("rs-momentum-001");
    expect(research).not.toBeNull();

    render(
      <OverviewSection
        research={research!}
        labels={{
          researchQuestion: "Research question",
          hypothesis: "Hypothesis",
          researchObjective: "Research objective",
          currentStage: "Current stage",
          researchConfidence: "Research confidence",
          currentRecommendation: "Recommendation",
          researchSummary: "Research summary",
          evidenceNarrative: "Evidence summary",
          validationSummary: "Validation summary",
          keyStrengths: "Key strengths",
          knownWeaknesses: "Known weaknesses",
          openQuestions: "Open questions",
          nextActions: "Next actions",
          lifecycleTitle: "Research lifecycle",
          lifecycleDescription: "Lifecycle description",
          evidenceTitle: "Evidence checklist",
          evidenceDescription: "Evidence description",
          confidence: "Confidence",
        }}
      />
    );

    expect(
      screen.getByText(/12–1 month cross-sectional momentum/i)
    ).toBeInTheDocument();
    expect(screen.getByText("Continue; freeze universe before next OOS fold")).toBeInTheDocument();
    expect(screen.getByText("Backtest completed")).toBeInTheDocument();
    expect(screen.getByText("Next actions")).toBeInTheDocument();
  });
});
