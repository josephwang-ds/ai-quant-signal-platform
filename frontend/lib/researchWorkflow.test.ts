import { describe, expect, it } from "vitest";
import {
  derivePrimaryWorkflowStep,
  deriveWorkflowPrimaryAction,
  deriveWorkflowStepStates,
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

  it("requires validation before evaluation", () => {
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

  it("moves to copilot only after evaluation is ready", () => {
    const step = derivePrimaryWorkflowStep({
      executionStatus: "ready",
      execution,
      validationStatus: "ready",
      validation,
      evaluationStatus: "ready",
      evaluation: { evaluation_status: "completed" } as never,
    });
    expect(step).toBe("copilot");
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

  it("keeps future steps unavailable until dependencies exist", () => {
    const states = deriveWorkflowStepStates({
      executionStatus: "idle",
      execution: null,
      validationStatus: "idle",
      validation: null,
      evaluationStatus: "idle",
      evaluation: null,
    });
    expect(states.validation).toBe("unavailable");
    expect(states.evaluation).toBe("unavailable");
    expect(states.copilot).toBe("unavailable");
  });
});
