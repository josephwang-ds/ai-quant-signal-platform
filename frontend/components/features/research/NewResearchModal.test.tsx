import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import NewResearchModal, {
  type NewResearchModalLabels,
} from "@/components/features/research/NewResearchModal";

const labels: NewResearchModalLabels = {
  title: "New Research",
  localNote: "Create local research.",
  name: "Research Title",
  question: "Research Question",
  hypothesis: "Hypothesis",
  tags: "Tags",
  tagsHint: "Optional tags",
  executionTitle: "Executable protocol",
  executionHint: "Inputs for validation.",
  symbol: "Symbol",
  benchmark: "Benchmark",
  startDate: "Start date",
  endDate: "End date",
  shortWindow: "Short MA",
  longWindow: "Long MA",
  transactionCost: "Transaction cost",
  create: "Create",
  cancel: "Cancel",
  errorName: "Name required",
  errorQuestion: "Question required",
  errorHypothesis: "Hypothesis required",
  errorSymbol: "Symbol required",
  errorShortWindow: "Invalid short window",
  errorLongWindow: "Invalid long window",
  errorDateRange: "Invalid date range",
  errorTransactionCost: "Invalid cost",
};

describe("NewResearchModal", () => {
  it("creates an executable research definition with protocol defaults", async () => {
    const user = userEvent.setup();
    const onCreate = vi.fn();
    render(
      <NewResearchModal
        open
        labels={labels}
        onClose={vi.fn()}
        onCreate={onCreate}
      />
    );

    await user.type(screen.getByLabelText("Research Title *"), "SPY trend study");
    await user.type(
      screen.getByLabelText("Research Question *"),
      "Does the rule improve drawdown?"
    );
    await user.type(
      screen.getByLabelText("Hypothesis *"),
      "The rule may reduce drawdown."
    );
    await user.click(screen.getByRole("button", { name: "Create" }));

    expect(onCreate).toHaveBeenCalledWith(
      expect.objectContaining({
        name: "SPY trend study",
        runConfiguration: expect.objectContaining({
          symbol: "SPY",
          benchmark: "SPY",
          startDate: "2018-01-01",
          shortWindow: 20,
          longWindow: 60,
          transactionCost: 0.001,
        }),
      })
    );
  });
});
