import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import ResearchWorkspaceOrientation from "@/components/features/research/ResearchWorkspaceOrientation";

describe("ResearchWorkspaceOrientation", () => {
  it("explains the workflow and identifies one next milestone", () => {
    render(
      <ResearchWorkspaceOrientation
        nextMilestone="Run validation"
        labels={{
          eyebrow: "Research workflow",
          title: "Define, test, challenge, observe, then decide.",
          description: "Work from left to right.",
          next: "Next step",
        }}
      />
    );

    expect(
      screen.getByRole("heading", {
        name: "Define, test, challenge, observe, then decide.",
      })
    ).toBeInTheDocument();
    expect(screen.getByText("Run validation")).toBeInTheDocument();
  });
});
