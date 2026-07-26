import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import GuidedReviewEntry from "@/components/features/research/GuidedReviewEntry";

describe("GuidedReviewEntry", () => {
  it("presents one bounded reviewer path without claiming results", () => {
    render(<GuidedReviewEntry language="en" />);

    expect(
      screen.getByRole("heading", {
        name: "From question to decision, in four checks.",
      })
    ).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(4);
    expect(
      screen.getByText("Backend-calculated results and deterministic checks")
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "Start guided review" })
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/guaranteed return/i)).not.toBeInTheDocument();
  });

  it("renders a complete Chinese experience", () => {
    render(<GuidedReviewEntry language="zh" />);

    expect(
      screen.getByRole("heading", { name: "从问题到决策，四步完成审阅。" })
    ).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(4);
    expect(
      screen.getByText("人的决策权与分析严格分离")
    ).toBeInTheDocument();
  });
});
