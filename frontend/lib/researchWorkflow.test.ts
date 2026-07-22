import { describe, expect, it } from "vitest";
import {
  derivePrimaryTabProgress,
  derivePrimaryWorkflowStep,
  deriveWorkflowPrimaryAction,
  deriveWorkflowStepStates,
  sectionToWorkflowStep,
  workflowStepToSection,
  WORKFLOW_STEP_ORDER,
} from "@/lib/researchWorkflow";

const execution = {
  research_id: "ma-crossover-spy",
  metrics: { total_return: 0.1 },
} as never;

const validation = {
  validation_run_id: "val-1",
  evidence_complete: true,
} as never;

describe("researchWorkflow", () => {
  it("exposes the seven-stage product spine", () => {
    expect([...WORKFLOW_STEP_ORDER]).toEqual([
      "research",
      "experiment",
      "validation",
      "robustness",
      "paper",
      "decision",
      "archive",
    ]);
  });

  it("maps primary tabs to workflow steps bidirectionally", () => {
    for (const step of WORKFLOW_STEP_ORDER) {
      expect(sectionToWorkflowStep(workflowStepToSection(step))).toBe(step);
    }
  });

  it("requires execution before validation", () => {
    const step = derivePrimaryWorkflowStep({
      executionStatus: "idle",
      execution: null,
      validationStatus: "idle",
      validation: null,
      evaluationStatus: "idle",
      evaluation: null,
    });
    expect(step).toBe("research");
  });

  it("moves to validation after execution", () => {
    const step = derivePrimaryWorkflowStep({
      executionStatus: "ready",
      execution,
      validationStatus: "idle",
      validation: null,
      evaluationStatus: "idle",
      evaluation: null,
    });
    expect(step).toBe("validation");
  });

  it("marks experiment completed once execution exists", () => {
    const states = deriveWorkflowStepStates({
      executionStatus: "ready",
      execution,
      validationStatus: "idle",
      validation: null,
      evaluationStatus: "idle",
      evaluation: null,
    });
    expect(states.research).toBe("completed");
    expect(states.experiment).toBe("completed");
    expect(states.validation).toBe("current");
    expect(states.robustness).toBe("unavailable");
    expect(derivePrimaryTabProgress(states.research)).toBe("completed");
    expect(derivePrimaryTabProgress(states.validation)).toBe("current");
    expect(derivePrimaryTabProgress(states.robustness)).toBe("locked");
  });

  it("moves to robustness after validation summary is ready", () => {
    const step = derivePrimaryWorkflowStep({
      executionStatus: "ready",
      execution,
      validationStatus: "ready",
      validation,
      evaluationStatus: "ready",
      evaluation: { evaluation_status: "completed" } as never,
    });
    expect(step).toBe("robustness");
  });

  it("marks only one primary action at a time", () => {
    const action = deriveWorkflowPrimaryAction({
      executionStatus: "ready",
      execution,
      validationStatus: "idle",
      validation: null,
      evaluationStatus: "idle",
      evaluation: null,
    });
    expect(action.step).toBe("validation");
    expect(action.disabled).toBe(false);
  });

  it("keeps later stages unavailable until dependencies exist", () => {
    const states = deriveWorkflowStepStates({
      executionStatus: "idle",
      execution: null,
      validationStatus: "idle",
      validation: null,
      evaluationStatus: "idle",
      evaluation: null,
    });
    expect(states.validation).toBe("unavailable");
    expect(states.robustness).toBe("unavailable");
    expect(states.paper).toBe("unavailable");
    expect(states.decision).toBe("unavailable");
    expect(states.archive).toBe("unavailable");
  });
});
