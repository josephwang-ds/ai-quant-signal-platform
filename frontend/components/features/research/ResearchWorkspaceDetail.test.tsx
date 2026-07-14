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
  });
});

describe("ResearchWorkspaceNavigation", () => {
  it("renders all workspace sections and marks the active one", () => {
    render(
      <ResearchWorkspaceNavigation
        researchId={CANONICAL_RESEARCH_ID}
        activeSection="overview"
        labels={navLabels}
      />
    );

    expect(screen.getByRole("navigation", { name: /research workspace sections/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Notebook" })).toHaveAttribute(
      "href",
      `/research/${CANONICAL_RESEARCH_ID}?tab=notebook`
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
          confidence: "Evaluation",
          strategyConfig: "Strategy configuration",
          dataRequirements: "Data requirements",
          symbol: "Symbol",
          benchmark: "Benchmark",
          strategy: "Strategy",
          dataStatus: "Data status",
          metricsStatus: "Metrics status",
        }}
      />
    );

    expect(
      screen.getByText(/MA20\/MA60 crossover outperform SPY buy-and-hold/i)
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/Evaluation pending real validation evidence/i).length
    ).toBeGreaterThan(0);
    expect(screen.getByText("SPY")).toBeInTheDocument();
    expect(screen.queryByText(/^62$/)).not.toBeInTheDocument();
  });
});
