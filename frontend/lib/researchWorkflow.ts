/**
 * Guided research workflow — product spine only.
 *
 * Research → Experiment → Validation → Robustness → Paper Trading → Decision → Archive
 */

import type { ResearchLifecycleStatus } from "@/types/research";
import type { ResearchExecutionResult, ResearchExecutionStatus } from "@/types/researchExecution";
import type {
  ResearchEvaluationResult,
  ResearchEvaluationRequestStatus,
} from "@/types/researchEvaluation";
import type { ResearchValidationResult, ResearchValidationStatus } from "@/types/researchValidation";

export type WorkflowStepId =
  | "research"
  | "experiment"
  | "validation"
  | "robustness"
  | "paper"
  | "decision"
  | "archive";

export const WORKFLOW_STEP_ORDER: readonly WorkflowStepId[] = [
  "research",
  "experiment",
  "validation",
  "robustness",
  "paper",
  "decision",
  "archive",
] as const;

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
  /** Optional lifecycle status for Paper / Decision / Archive progression. */
  researchStatus?: ResearchLifecycleStatus;
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

function paperReached(status: ResearchLifecycleStatus | undefined): boolean {
  return (
    status === "Paper Trading" ||
    status === "Monitoring" ||
    status === "Archived"
  );
}

function decisionReached(status: ResearchLifecycleStatus | undefined): boolean {
  return status === "Monitoring" || status === "Archived";
}

function archiveReached(status: ResearchLifecycleStatus | undefined): boolean {
  return status === "Archived";
}

/**
 * First unfinished spine step.
 * Experiment completes with Research execution evidence.
 * Evaluation remains folded into Validation (URL `?tab=evaluation` still works).
 */
export function derivePrimaryWorkflowStep(input: WorkflowInput): WorkflowStepId {
  if (!executionReady(input.executionStatus, input.execution)) return "research";
  if (!validationReady(input.validationStatus, input.validation)) return "validation";
  if (!evaluationReady(input.evaluationStatus, input.evaluation)) return "validation";
  if (!paperReached(input.researchStatus)) return "robustness";
  if (!decisionReached(input.researchStatus)) return "paper";
  if (!archiveReached(input.researchStatus)) return "decision";
  return "archive";
}

function stepState(
  step: WorkflowStepId,
  primary: WorkflowStepId,
  input: WorkflowInput
): WorkflowStepState {
  const execReady = executionReady(input.executionStatus, input.execution);
  const valReady = validationReady(input.validationStatus, input.validation);
  const evalReady = evaluationReady(input.evaluationStatus, input.evaluation);
  const status = input.researchStatus;

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

  if (step === "experiment") {
    if (!execReady) return "unavailable";
    return "completed";
  }

  if (step === "validation") {
    if (!execReady) return "unavailable";
    if (input.validationStatus === "loading" || input.evaluationStatus === "loading") {
      return primary === "validation" ? "loading" : "not_started";
    }
    if (input.validationStatus === "error" || input.evaluationStatus === "error") {
      return primary === "validation" ? "failed" : "not_started";
    }
    if (evalReady) return "completed";
    return primary === "validation" ? "current" : "not_started";
  }

  if (step === "robustness") {
    if (!evalReady) return "unavailable";
    if (paperReached(status)) return "completed";
    return primary === "robustness" ? "current" : "not_started";
  }

  if (step === "paper") {
    if (!evalReady) return "unavailable";
    if (decisionReached(status) || paperReached(status)) return "completed";
    return primary === "paper" ? "current" : "not_started";
  }

  if (step === "decision") {
    if (!evalReady) return "unavailable";
    if (!paperReached(status) && primary !== "decision") return "unavailable";
    if (archiveReached(status) || decisionReached(status)) return "completed";
    return primary === "decision" ? "current" : "not_started";
  }

  // archive
  if (!evalReady) return "unavailable";
  if (!decisionReached(status) && primary !== "archive") return "unavailable";
  if (archiveReached(status)) return "completed";
  return primary === "archive" ? "current" : "not_started";
}

export function deriveWorkflowStepStates(input: WorkflowInput): Record<
  WorkflowStepId,
  WorkflowStepState
> {
  const primary = derivePrimaryWorkflowStep(input);
  return {
    research: stepState("research", primary, input),
    experiment: stepState("experiment", primary, input),
    validation: stepState("validation", primary, input),
    robustness: stepState("robustness", primary, input),
    paper: stepState("paper", primary, input),
    decision: stepState("decision", primary, input),
    archive: stepState("archive", primary, input),
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
    return {
      step,
      disabled:
        input.validationStatus === "loading" ||
        input.evaluationStatus === "loading",
    };
  }
  return { step, disabled: false };
}

/** Map spine step → workspace tab (backward-compatible section ids). */
export function workflowStepToSection(
  step: WorkflowStepId
):
  | "overview"
  | "experiments"
  | "validation"
  | "robustness"
  | "paper"
  | "decision"
  | "archive" {
  if (step === "research") return "overview";
  if (step === "experiment") return "experiments";
  if (step === "validation") return "validation";
  if (step === "robustness") return "robustness";
  if (step === "paper") return "paper";
  if (step === "decision") return "decision";
  return "archive";
}

/** Map primary workspace tab → spine step. */
export function sectionToWorkflowStep(
  section:
    | "overview"
    | "experiments"
    | "validation"
    | "evaluation"
    | "robustness"
    | "paper"
    | "decision"
    | "archive"
): WorkflowStepId {
  if (section === "overview") return "research";
  if (section === "experiments") return "experiment";
  if (section === "validation" || section === "evaluation") return "validation";
  if (section === "robustness") return "robustness";
  if (section === "paper") return "paper";
  if (section === "decision") return "decision";
  return "archive";
}

/** Visual progress chip for primary tabs (tab bar doubles as lifecycle indicator). */
export type PrimaryTabProgress = "completed" | "current" | "locked" | "open";

export function derivePrimaryTabProgress(
  state: WorkflowStepState
): PrimaryTabProgress {
  if (state === "unavailable") return "locked";
  if (state === "completed") return "completed";
  if (state === "current" || state === "loading" || state === "failed") {
    return "current";
  }
  return "open";
}
