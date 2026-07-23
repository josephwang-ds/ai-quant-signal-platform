import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import ResearchWorkspaceHeader, {
  type ResearchWorkspaceHeaderLabels,
} from "@/components/features/research/ResearchWorkspaceHeader";
import {
  CANONICAL_RESEARCH_ID,
  getMockResearchById,
} from "@/lib/mockResearchCatalog";

const labels: ResearchWorkspaceHeaderLabels = {
  back: "Back",
  moreActions: "More actions",
  moreActionsHint: "Manage this research.",
  deleteResearch: "Delete",
  owner: "Owner",
  created: "Created",
  updated: "Updated",
  recommendation: "Recommendation",
  confidence: "Confidence",
  tags: "Tags",
  benchmark: "Benchmark",
  experiment: "Experiment",
  experimentNotConfigured: "Not configured",
};

describe("ResearchWorkspaceHeader", () => {
  it("exposes permanent deletion from the detail-page action menu", async () => {
    const user = userEvent.setup();
    const onDeleteResearch = vi.fn();
    const research = getMockResearchById(CANONICAL_RESEARCH_ID);
    expect(research).not.toBeNull();

    render(
      <ResearchWorkspaceHeader
        research={research!}
        language="en"
        labels={labels}
        onDeleteResearch={onDeleteResearch}
      />
    );

    await user.click(screen.getByRole("button", { name: "More actions" }));
    await user.click(screen.getByRole("menuitem", { name: "Delete" }));

    expect(onDeleteResearch).toHaveBeenCalledTimes(1);
  });
});
