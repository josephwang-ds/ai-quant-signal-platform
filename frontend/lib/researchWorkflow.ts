import type { ResearchExecutionResult, ResearchExecutionStatus } from "@/types/researchExecution";
import type {
  ResearchEvaluationResult,
  ResearchEvaluationRequestStatus,
} from "@/types/researchEvaluation";
import type { ResearchValidationResult, ResearchValidationStatus } from "@/types/researchValidation";

export type WorkflowStepId = "research" | "validation" | "evaluation" | "copilot";

export type WorkflowStepState =
  | "not_started"
  | "current"
  | "loading"
  | "completed"
  | "unavailable"
  | "failed";

export type WorkflowInput = {
  executionStatus: ResearchExecutionStatus;
  execution: ResearchExecutionResult | null;
  validationStatus: ResearchValidationStatus;
  validation: ResearchValidationResult | null;
  evaluationStatus: ResearchEvaluationRequestStatus;
  evaluation: ResearchEvaluationResult | null;
};

export type WorkflowPrimaryAction = {
  step: WorkflowStepId;
  disabled: boolean;
};

export function executionReady(
  executionStatus: ResearchExecutionStatus,
  execution: ResearchExecutionResult | null
): boolean {
  return executionStatus === "ready" && Boolean(execution);
}

export function validationReady(
  validationStatus: ResearchValidationStatus,
  validation: ResearchValidationResult | null
): boolean {
  return validationStatus === "ready" && Boolean(validation?.validation_run_id);
}

export function evaluationReady(
  evaluationStatus: ResearchEvaluationRequestStatus,
  evaluation: ResearchEvaluationResult | null
): boolean {
  return evaluationStatus === "ready" && Boolean(evaluation);
}

export function derivePrimaryWorkflowStep(input: WorkflowInput): WorkflowStepId {
  if (!executionReady(input.executionStatus, input.execution)) return "research";
  if (!validationReady(input.validationStatus, input.validation)) return "validation";
  if (!evaluationReady(input.evaluationStatus, input.evaluation)) return "evaluation";
  return "copilot";
}

function stepState(
  step: WorkflowStepId,
  primary: WorkflowStepId,
  input: WorkflowInput
): WorkflowStepState {
  const execReady = executionReady(input.executionStatus, input.execution);
  const valReady = validationReady(input.validationStatus, input.validation);
  const evalReady = evaluationReady(input.evaluationStatus, input.evaluation);

  if (step === "research") {
    if (input.executionStatus === "loading" || input.executionStatus === "idle") {
      return primary === "research" ? "loading" : "not_started";
    }
    if (input.executionStatus === "error") {
      return primary === "research" ? "failed" : "not_started";
    }
    if (execReady) return "completed";
    return primary === "research" ? "current" : "not_started";
  }

  if (step === "validation") {
    if (!execReady) return "unavailable";
    if (input.validationStatus === "loading") {
      return primary === "validation" ? "loading" : "not_started";
    }
    if (input.validationStatus === "error") {
      return primary === "validation" ? "failed" : "not_started";
    }
    if (valReady) return "completed";
    return primary === "validation" ? "current" : "not_started";
  }

  if (step === "evaluation") {
    if (!valReady) return "unavailable";
    if (input.evaluationStatus === "loading") {
      return primary === "evaluation" ? "loading" : "not_started";
    }
    if (input.evaluationStatus === "error") {
      return primary === "evaluation" ? "failed" : "not_started";
    }
    if (evalReady) return "completed";
    return primary === "evaluation" ? "current" : "not_started";
  }

  if (!valReady) return "unavailable";
  if (!evalReady) return "unavailable";
  return primary === "copilot" ? "current" : "completed";
}

export function deriveWorkflowStepStates(input: WorkflowInput): Record<
  WorkflowStepId,
  WorkflowStepState
> {
  const primary = derivePrimaryWorkflowStep(input);
  return {
    research: stepState("research", primary, input),
    validation: stepState("validation", primary, input),
    evaluation: stepState("evaluation", primary, input),
    copilot: stepState("copilot", primary, input),
  };
}

export function deriveResearchListNextStep(
  validationStatus: string,
  evaluationStatus: string,
  labels: {
    runResearch: string;
    validate: string;
    evaluate: string;
    review: string;
  }
): string {
  if (
    validationStatus === "Not Started" ||
    validationStatus === "Awaiting Data" ||
    validationStatus === "Awaiting Engine"
  ) {
    return labels.runResearch;
  }
  if (validationStatus !== "Completed") {
    return labels.validate;
  }
  if (evaluationStatus === "Completed" || evaluationStatus === "Blocked") {
    return labels.review;
  }
  return labels.evaluate;
}

export function deriveWorkflowPrimaryAction(input: WorkflowInput): WorkflowPrimaryAction {
  const step = derivePrimaryWorkflowStep(input);
  if (step === "research") {
    const loading =
      input.executionStatus === "loading" || input.executionStatus === "idle";
    return { step, disabled: loading };
  }
  if (step === "validation") {
    return { step, disabled: input.validationStatus === "loading" };
  }
  if (step === "evaluation") {
    return { step, disabled: input.evaluationStatus === "loading" };
  }
  return { step, disabled: false };
}
