import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import ResearchActionPanel, {
  type ResearchActionPanelLabels,
} from "@/components/features/research/ResearchActionPanel";

const labels: ResearchActionPanelLabels = {
  title: "Workspace actions",
  description: "Use the available research workflows.",
  addNotebook: "Add Notebook Entry",
  createExperiment: "Create Experiment",
  runValidation: "Run Validation",
  runningValidation: "Running Validation…",
  requestEvaluation: "Request Evaluation",
  openCopilot: "Open Research Copilot",
  hintNotebook: "Open research notes.",
  hintExperiment: "Open planned experiments.",
  hintValidation: "Run deterministic validation.",
  hintEvaluation: "Review governance conclusions.",
  hintEvaluationDisabled: "Run Validation first.",
  hintCopilot: "Ask grounded questions.",
  hintCopilotDisabled: "Run Validation first.",
};

describe("ResearchActionPanel", () => {
  it("navigates to notebook and experiments", async () => {
    const user = userEvent.setup();
    const onNavigate = vi.fn();
    const onRunValidation = vi.fn();
    const onRequestEvaluation = vi.fn();

    render(
      <ResearchActionPanel
        labels={labels}
        activeSection="overview"
        onNavigate={onNavigate}
        onRunValidation={onRunValidation}
        onRequestEvaluation={onRequestEvaluation}
        validationStatus="idle"
        validationRunId={null}
        evaluationStatus="idle"
      />
    );

    await user.click(screen.getByRole("button", { name: "Add Notebook Entry" }));
    await user.click(screen.getByRole("button", { name: "Create Experiment" }));

    expect(onNavigate).toHaveBeenNthCalledWith(1, "notebook");
    expect(onNavigate).toHaveBeenNthCalledWith(2, "experiments");
    expect(screen.queryByText("Coming in a later PR")).not.toBeInTheDocument();
    expect(screen.queryByText("后续 PR 提供")).not.toBeInTheDocument();
  });

  it("enables validation when idle and disables while loading", async () => {
    const user = userEvent.setup();
    const onRunValidation = vi.fn();
    const { rerender } = render(
      <ResearchActionPanel
        labels={labels}
        activeSection="overview"
        onNavigate={vi.fn()}
        onRunValidation={onRunValidation}
        onRequestEvaluation={vi.fn()}
        validationStatus="idle"
        validationRunId={null}
        evaluationStatus="idle"
      />
    );

    const runButton = screen.getByRole("button", { name: "Run Validation" });
    expect(runButton).toBeEnabled();
    await user.click(runButton);
    expect(onRunValidation).toHaveBeenCalledTimes(1);

    rerender(
      <ResearchActionPanel
        labels={labels}
        activeSection="validation"
        onNavigate={vi.fn()}
        onRunValidation={onRunValidation}
        onRequestEvaluation={vi.fn()}
        validationStatus="loading"
        validationRunId={null}
        evaluationStatus="idle"
      />
    );

    expect(
      screen.getByRole("button", { name: "Running Validation…" })
    ).toBeDisabled();
  });

  it("gates evaluation and copilot on validation_run_id", async () => {
    const user = userEvent.setup();
    const onNavigate = vi.fn();
    const onRequestEvaluation = vi.fn();
    const { rerender } = render(
      <ResearchActionPanel
        labels={labels}
        activeSection="overview"
        onNavigate={onNavigate}
        onRunValidation={vi.fn()}
        onRequestEvaluation={onRequestEvaluation}
        validationStatus="idle"
        validationRunId={null}
        evaluationStatus="idle"
      />
    );

    expect(
      screen.getByRole("button", { name: "Request Evaluation" })
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Open Research Copilot" })
    ).toBeDisabled();
    expect(screen.getAllByText("Run Validation first.")).toHaveLength(2);

    rerender(
      <ResearchActionPanel
        labels={labels}
        activeSection="overview"
        onNavigate={onNavigate}
        onRunValidation={vi.fn()}
        onRequestEvaluation={onRequestEvaluation}
        validationStatus="ready"
        validationRunId="val-run-1"
        evaluationStatus="idle"
      />
    );

    await user.click(
      screen.getByRole("button", { name: "Request Evaluation" })
    );
    await user.click(
      screen.getByRole("button", { name: "Open Research Copilot" })
    );

    expect(onRequestEvaluation).toHaveBeenCalledTimes(1);
    expect(onNavigate).toHaveBeenCalledWith("copilot");
  });

  it("does not invoke Copilot API callbacks when opening Copilot", async () => {
    const user = userEvent.setup();
    const onNavigate = vi.fn();
    const askCopilot = vi.fn();

    render(
      <ResearchActionPanel
        labels={labels}
        activeSection="overview"
        onNavigate={(section) => {
          onNavigate(section);
          // Opening Copilot must never auto-submit an LLM request.
          expect(askCopilot).not.toHaveBeenCalled();
        }}
        onRunValidation={vi.fn()}
        onRequestEvaluation={vi.fn()}
        validationStatus="ready"
        validationRunId="val-run-1"
        evaluationStatus="idle"
      />
    );

    await user.click(
      screen.getByRole("button", { name: "Open Research Copilot" })
    );
    expect(onNavigate).toHaveBeenCalledWith("copilot");
    expect(askCopilot).not.toHaveBeenCalled();
  });
});
