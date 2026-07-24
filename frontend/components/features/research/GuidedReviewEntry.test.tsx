import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import GuidedReviewEntry from "@/components/features/research/GuidedReviewEntry";

describe("GuidedReviewEntry", () => {
  it("presents one bounded reviewer path without claiming results", () => {
    render(
      <GuidedReviewEntry
        language="en"
        href="/research/ma-crossover-spy?review=1"
      />
    );

    expect(
      screen.getByRole("heading", {
        name: "One research question. Four proof points.",
      })
    ).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(8);
    expect(
      screen.getByRole("link", { name: "Start guided review" })
    ).toHaveAttribute("href", "/research/ma-crossover-spy?review=1");
    expect(screen.getByText("Why this is different")).toBeInTheDocument();
    expect(
      screen.getByText("Deterministic checks before AI")
    ).toBeInTheDocument();
    expect(screen.getByText("Unknowns stay visible")).toBeInTheDocument();
    expect(screen.queryByText(/guaranteed return/i)).not.toBeInTheDocument();
  });

  it("renders a complete Chinese experience", () => {
    render(
      <GuidedReviewEntry
        language="zh"
        href="/research/ma-crossover-spy?review=1"
      />
    );

    expect(
      screen.getByRole("heading", { name: "一个研究问题，四个证明点。" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "开始引导式审阅" })
    ).toBeInTheDocument();
    expect(screen.getByText("它为什么不同")).toBeInTheDocument();
    expect(screen.getByText("人工保留决策权")).toBeInTheDocument();
  });
});
