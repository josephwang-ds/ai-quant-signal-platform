/**
 * PR-026 Decision Center — research approval projection only.
 *
 * Derives decision readiness from Validation, Robustness, and Paper Trading
 * evidence. Does not invent approvals, scores, or trading results.
 */

import {
  buildPaperTradingCenterModel,
  type PaperEligibilityStatus,
} from "@/lib/researchPaperTrading";
import {
  buildRobustnessCenterModel,
  ROBUSTNESS_FAILURE_CONDITIONS,
  type RobustnessFailureConditionId,
  type RobustnessOverallStatus,
} from "@/lib/researchRobustness";
import type { ResearchDetail } from "@/types/research";
import type { ResearchEvaluationResult } from "@/types/researchEvaluation";
import type { ResearchValidationResult } from "@/types/researchValidation";

export type DecisionStatus =
  | "not_ready"
  | "under_review"
  | "approved_for_paper"
  | "rejected"
  | "archived";

export type DecisionEvidenceId = "validation" | "robustness" | "paper_trading";

export type DecisionEvidenceStatus = "completed" | "pending";

export type DecisionChecklistId =
  | "validation_completed"
  | "robustness_reviewed"
  | "observation_plan_prepared"
  | "limitations_documented";

export type DecisionChecklistStatus = "completed" | "pending";

export type DecisionRiskId =
  | RobustnessFailureConditionId
  | "implemented_robustness_pending";

export type DecisionNextActionKind =
  | "complete_validation"
  | "complete_robustness"
  | "prepare_paper_trading"
  | "continue_paper_observation"
  | "archive_research"
  | "none";

export type DecisionEvidenceView = {
  id: DecisionEvidenceId;
  status: DecisionEvidenceStatus;
};

export type DecisionChecklistView = {
  id: DecisionChecklistId;
  status: DecisionChecklistStatus;
};

export type DecisionCenterModel = {
  researchName: string;
  experimentLabel: string;
  decisionStatus: DecisionStatus;
  evidence: DecisionEvidenceView[];
  remainingRiskIds: DecisionRiskId[];
  checklist: DecisionChecklistView[];
  /** Null when no real decision notes exist — never invent copy. */
  decisionNotes: string | null;
  nextActionKind: DecisionNextActionKind;
  hasValidationEvidence: boolean;
  hasEvaluationEvidence: boolean;
};

function buildExperimentLabel(research: ResearchDetail): string {
  const { symbol, strategyName, parameterLines } = research.configuration;
  const params = parameterLines.slice(0, 2).join(" / ");
  if (params) return `${symbol} · ${strategyName} · ${params}`;
  return `${symbol} · ${strategyName}`;
}

function validationEvidenceCompleted(
  validation: ResearchValidationResult | null,
  evaluation: ResearchEvaluationResult | null
): boolean {
  if (evaluation?.evaluation_status === "completed") return true;
  if (validation?.validation_status === "completed") return true;
  return false;
}

function robustnessEvidenceCompleted(
  overall: RobustnessOverallStatus,
  hasPendingImplemented: boolean
): boolean {
  if (hasPendingImplemented) return false;
  if (overall === "blocked" || overall === "not_started" || overall === "in_progress") {
    return false;
  }
  // planned_remaining / complete — implemented checks done; planned work may remain.
  return overall === "planned_remaining" || overall === "complete";
}

function paperEvidenceCompleted(
  research: ResearchDetail,
  eligibility: PaperEligibilityStatus,
  hasSession: boolean
): boolean {
  if (hasSession) return true;
  if (research.status === "Paper Trading" || research.status === "Monitoring") {
    return true;
  }
  // Eligibility alone is not completed paper evidence.
  void eligibility;
  return false;
}

function deriveDecisionStatus(input: {
  research: ResearchDetail;
  validation: ResearchValidationResult | null;
  evaluation: ResearchEvaluationResult | null;
  paperEligibility: PaperEligibilityStatus;
  robustnessBlocked: boolean;
}): DecisionStatus {
  const { research, validation, evaluation, paperEligibility, robustnessBlocked } =
    input;

  if (research.status === "Archived") return "archived";

  // Only map Approved when lifecycle already reflects paper deployment.
  if (
    research.status === "Paper Trading" ||
    research.status === "Monitoring"
  ) {
    return "approved_for_paper";
  }

  // Rejected is never invented — no rejection artifact exists in this slice.
  void evaluation;

  if (!validation) return "not_ready";

  if (
    robustnessBlocked ||
    paperEligibility === "needs_review" ||
    paperEligibility === "not_eligible" ||
    evaluation?.evaluation_status === "blocked" ||
    evaluation?.evaluation_status === "incomplete" ||
    validation.validation_status === "incomplete" ||
    validation.validation_status === "failed"
  ) {
    if (paperEligibility === "not_eligible" && !validation) {
      return "not_ready";
    }
    if (paperEligibility === "not_eligible") return "not_ready";
    return "under_review";
  }

  if (paperEligibility === "eligible") return "under_review";

  return "not_ready";
}

function deriveNextAction(
  status: DecisionStatus,
  evidence: DecisionEvidenceView[],
  paperEligibility: PaperEligibilityStatus
): DecisionNextActionKind {
  if (status === "archived") return "none";
  if (status === "rejected") return "archive_research";

  const validationPending =
    evidence.find((row) => row.id === "validation")?.status === "pending";
  const robustnessPending =
    evidence.find((row) => row.id === "robustness")?.status === "pending";
  const paperPending =
    evidence.find((row) => row.id === "paper_trading")?.status === "pending";

  if (validationPending) return "complete_validation";
  if (robustnessPending) return "complete_robustness";
  if (
    paperPending &&
    (paperEligibility === "eligible" ||
      paperEligibility === "needs_review" ||
      paperEligibility === "not_eligible")
  ) {
    if (paperEligibility === "not_eligible") return "complete_validation";
    if (paperEligibility === "needs_review") return "complete_robustness";
    return "prepare_paper_trading";
  }
  if (status === "approved_for_paper" && paperPending) {
    return "continue_paper_observation";
  }
  if (status === "approved_for_paper") return "archive_research";
  if (status === "under_review" && !paperPending) return "archive_research";
  if (status === "under_review") return "prepare_paper_trading";
  return "complete_robustness";
}

/**
 * Build the Decision Center model from existing research evidence only.
 */
export function buildDecisionCenterModel(input: {
  research: ResearchDetail;
  validation: ResearchValidationResult | null;
  evaluation: ResearchEvaluationResult | null;
  /** Reserved — callers must pass false until a real session exists. */
  hasSession?: boolean;
  /** Reserved — callers must pass null until real decision notes exist. */
  decisionNotes?: string | null;
}): DecisionCenterModel {
  const hasSession = input.hasSession === true;
  const robustness = buildRobustnessCenterModel({
    validation: input.validation,
    evaluation: input.evaluation,
  });
  const paper = buildPaperTradingCenterModel({
    research: input.research,
    validation: input.validation,
    evaluation: input.evaluation,
    hasSession,
  });

  const hasPendingImplemented = robustness.items.some(
    (item) => item.implemented && item.status === "pending"
  );
  const robustnessBlocked =
    robustness.overallStatus === "blocked" ||
    robustness.items.some((item) => item.status === "blocked");

  const validationDone = validationEvidenceCompleted(
    input.validation,
    input.evaluation
  );
  const robustnessDone = robustnessEvidenceCompleted(
    robustness.overallStatus,
    hasPendingImplemented
  );
  const paperDone = paperEvidenceCompleted(
    input.research,
    paper.eligibility,
    hasSession
  );

  const evidence: DecisionEvidenceView[] = [
    { id: "validation", status: validationDone ? "completed" : "pending" },
    { id: "robustness", status: robustnessDone ? "completed" : "pending" },
    { id: "paper_trading", status: paperDone ? "completed" : "pending" },
  ];

  const remainingRiskIds: DecisionRiskId[] = [
    ...ROBUSTNESS_FAILURE_CONDITIONS.filter((condition) => {
      const related = robustness.items.find(
        (item) => item.id === condition.relatedItemId
      );
      return related?.status !== "completed";
    }).map((condition) => condition.id),
  ];
  if (hasPendingImplemented) {
    remainingRiskIds.push("implemented_robustness_pending");
  }

  const limitationsDocumented =
    Boolean(input.evaluation?.limitations.length) ||
    robustness.failureConditionIds.length > 0;

  const observationPlanPrepared = paper.observationItems.some(
    (item) => item.status === "pending" || item.status === "configured"
  );

  const checklist: DecisionChecklistView[] = [
    {
      id: "validation_completed",
      status: validationDone ? "completed" : "pending",
    },
    {
      id: "robustness_reviewed",
      status: robustnessDone ? "completed" : "pending",
    },
    {
      id: "observation_plan_prepared",
      status: observationPlanPrepared ? "completed" : "pending",
    },
    {
      id: "limitations_documented",
      status: limitationsDocumented ? "completed" : "pending",
    },
  ];

  const decisionStatus = deriveDecisionStatus({
    research: input.research,
    validation: input.validation,
    evaluation: input.evaluation,
    paperEligibility: paper.eligibility,
    robustnessBlocked,
  });

  const notes =
    typeof input.decisionNotes === "string" && input.decisionNotes.trim()
      ? input.decisionNotes.trim()
      : null;

  return {
    researchName: input.research.name,
    experimentLabel: buildExperimentLabel(input.research),
    decisionStatus,
    evidence,
    remainingRiskIds,
    checklist,
    decisionNotes: notes,
    nextActionKind: deriveNextAction(
      decisionStatus,
      evidence,
      paper.eligibility
    ),
    hasValidationEvidence: Boolean(input.validation),
    hasEvaluationEvidence: Boolean(input.evaluation),
  };
}
