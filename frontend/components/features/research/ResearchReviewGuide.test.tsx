import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import ResearchReviewGuide from "@/components/features/research/ResearchReviewGuide";

describe("ResearchReviewGuide", () => {
  it("keeps the review query across the four proof points", () => {
    render(
      <ResearchReviewGuide
        researchId="ma-crossover-spy"
        activeSection="validation"
        language="en"
      />
    );

    expect(
      screen.getByRole("heading", { name: "Step 2 of 4" })
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Question" })).toHaveAttribute(
      "href",
      "/research/ma-crossover-spy?review=1"
    );
    expect(screen.getByRole("link", { name: "Evidence" })).toHaveAttribute(
      "href",
      "/research/ma-crossover-spy?tab=validation&review=1"
    );
    expect(
      screen.getByRole("link", { name: "Next: Challenge" })
    ).toHaveAttribute(
      "href",
      "/research/ma-crossover-spy?tab=robustness&review=1"
    );
  });

  it("exits to the same section without review mode", () => {
    render(
      <ResearchReviewGuide
        researchId="sample"
        activeSection="robustness"
        language="en"
      />
    );

    expect(screen.getByRole("link", { name: "Exit guide" })).toHaveAttribute(
      "href",
      "/research/sample?tab=robustness"
    );
  });
});
