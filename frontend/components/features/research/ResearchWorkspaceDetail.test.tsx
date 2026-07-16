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
        research={research!}
        labels={{
          researchQuestion: "Research question",
          owner: "Owner",
          benchmark: "Benchmark",
          strategy: "Strategy",
          created: "Created",
          progressTitle: "Research Progress",
          progressResearch: "Research",
          progressExperiments: "Experiments",
          progressEvidence: "Evidence",
          progressDecision: "Decision",
          quickActionsTitle: "Quick Actions",
          runExperiment: "Run Experiment",
          openValidation: "Open Validation",
          generateReview: "Generate Review",
          recentExperimentsTitle: "Recent Experiments",
          latestEvidenceTitle: "Latest Evidence",
          currentDecisionTitle: "Current Decision",
          confidence: "Evaluation",
          noExperiments: "No experiments",
          noEvidence: "No evidence",
          decisionPending: "Decision pending",
        }}
      />
    );

    expect(
      screen.getByText(/MA20\/MA60 outperform Buy & Hold/i)
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/Evaluation pending real validation evidence/i).length
    ).toBeGreaterThan(0);
    expect(screen.getByText("SPY")).toBeInTheDocument();
    expect(screen.queryByText(/^62$/)).not.toBeInTheDocument();
  });
});
