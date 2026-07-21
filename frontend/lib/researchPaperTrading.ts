/**
 * PR-025 Research Deployment Center (Paper Trading) — management projection only.
 *
 * Organises paper-trading readiness from existing Validation / Evaluation /
 * Robustness evidence. Does not invent sessions, returns, orders, or PnL.
 */

import {
  buildRobustnessCenterModel,
  type RobustnessItemStatus,
} from "@/lib/researchRobustness";
import type { ResearchDetail, ResearchLifecycleStatus } from "@/types/research";
import type { ResearchEvaluationResult } from "@/types/researchEvaluation";
import type { ResearchValidationResult } from "@/types/researchValidation";

export type PaperEligibilityStatus =
  | "not_eligible"
  | "needs_review"
  | "eligible"
  | "active"
  | "completed"
  | "stopped";

export type ObservationItemStatus = "configured" | "pending" | "planned";

export type ObservationItemId =
  | "signal_consistency"
  | "benchmark_behaviour"
  | "transaction_cost_drift"
  | "drawdown_behaviour"
  | "data_quality"
  | "position_changes";

export type ReviewCriterionId =
  | "signal_consistent"
  | "costs_acceptable"
  | "drawdown_within_assumptions"
  | "no_validation_issues"
  | "benchmark_explainable";

export type ReviewCriterionStatus = "awaiting_observation";

export type PaperNextActionKind =
  | "continue_validation"
  | "continue_robustness"
  | "begin_observation"
  | "continue_observation"
  | "proceed_decision"
  | "archive"
  | "none";

export type ObservationItemView = {
  id: ObservationItemId;
  status: ObservationItemStatus;
};

export type ReviewCriterionView = {
  id: ReviewCriterionId;
  status: ReviewCriterionStatus;
};

export type ResearchDeploymentInfo = {
  researchName: string;
  experimentLabel: string;
  benchmark: string;
  strategy: string;
  currentStatus: ResearchLifecycleStatus;
};

export type PaperTradingCenterModel = {
  deployment: ResearchDeploymentInfo;
  eligibility: PaperEligibilityStatus;
  eligibilityReasonKey:
    | "no_validation"
    | "blocked"
    | "incomplete"
    | "eligible"
    | "active"
    | "completed"
    | "stopped";
  observationItems: ObservationItemView[];
  /** Always false until a real paper session exists in storage/API. */
  hasSession: boolean;
  reviewCriteria: ReviewCriterionView[];
  nextActionKind: PaperNextActionKind;
  hasValidationEvidence: boolean;
  hasEvaluationEvidence: boolean;
};

const OBSERVATION_ITEMS: readonly ObservationItemId[] = [
  "signal_consistency",
  "benchmark_behaviour",
  "transaction_cost_drift",
  "drawdown_behaviour",
  "data_quality",
  "position_changes",
] as const;

const REVIEW_CRITERIA: readonly ReviewCriterionId[] = [
  "signal_consistent",
  "costs_acceptable",
  "drawdown_within_assumptions",
  "no_validation_issues",
  "benchmark_explainable",
] as const;

function robustnessStatusById(
  items: ReturnType<typeof buildRobustnessCenterModel>["items"],
  id: string
): RobustnessItemStatus | null {
  return items.find((item) => item.id === id)?.status ?? null;
}

/**
 * Observation monitors are never Configured without a real session.
 * Pending = related validation/robustness evidence exists and is completed.
 * Planned = otherwise (unimplemented or incomplete).
 */
function deriveObservationStatus(
  id: ObservationItemId,
  hasSession: boolean,
  robustnessItems: ReturnType<typeof buildRobustnessCenterModel>["items"]
): ObservationItemStatus {
  if (hasSession) {
    return "configured";
  }

  const relatedRobustnessId =
    id === "benchmark_behaviour"
      ? "benchmark_comparison"
      : id === "transaction_cost_drift"
        ? "transaction_cost"
        : id === "data_quality"
          ? "data_quality"
          : id === "signal_consistency"
            ? "parameter_sensitivity"
            : null;

  if (relatedRobustnessId) {
    const status = robustnessStatusById(robustnessItems, relatedRobustnessId);
    if (status === "completed") return "pending";
  }

  return "planned";
}

function deriveEligibility(input: {
  research: ResearchDetail;
  validation: ResearchValidationResult | null;
  evaluation: ResearchEvaluationResult | null;
  robustnessOverall: ReturnType<typeof buildRobustnessCenterModel>["overallStatus"];
  robustnessItems: ReturnType<typeof buildRobustnessCenterModel>["items"];
  hasSession: boolean;
}): {
  eligibility: PaperEligibilityStatus;
  reasonKey: PaperTradingCenterModel["eligibilityReasonKey"];
} {
  const { research, validation, evaluation, robustnessOverall, robustnessItems, hasSession } =
    input;

  // Session-backed states only when a real session exists — never fabricate.
  if (hasSession) {
    if (research.status === "Archived" || research.status === "Monitoring") {
      return { eligibility: "completed", reasonKey: "completed" };
    }
    if (research.status === "Paper Trading") {
      return { eligibility: "active", reasonKey: "active" };
    }
    return { eligibility: "stopped", reasonKey: "stopped" };
  }

  if (!validation) {
    return { eligibility: "not_eligible", reasonKey: "no_validation" };
  }

  if (
    evaluation?.evaluation_status === "blocked" ||
    robustnessOverall === "blocked" ||
    robustnessItems.some((item) => item.status === "blocked") ||
    validation.validation_status === "failed"
  ) {
    return { eligibility: "needs_review", reasonKey: "blocked" };
  }

  const implementedPending = robustnessItems.some(
    (item) => item.implemented && item.status === "pending"
  );
  const validationIncomplete =
    validation.validation_status === "incomplete" ||
    evaluation?.evaluation_status === "incomplete";

  if (implementedPending || validationIncomplete || robustnessOverall === "in_progress") {
    return { eligibility: "needs_review", reasonKey: "incomplete" };
  }

  return { eligibility: "eligible", reasonKey: "eligible" };
}

function deriveNextAction(
  eligibility: PaperEligibilityStatus,
  hasSession: boolean
): PaperNextActionKind {
  if (eligibility === "not_eligible") return "continue_validation";
  if (eligibility === "needs_review") return "continue_robustness";
  if (eligibility === "eligible" && !hasSession) return "begin_observation";
  if (eligibility === "active" && hasSession) return "continue_observation";
  if (eligibility === "completed") return "proceed_decision";
  if (eligibility === "stopped") return "archive";
  return "none";
}

function buildExperimentLabel(research: ResearchDetail): string {
  const { symbol, strategyName, parameterLines } = research.configuration;
  const params = parameterLines.slice(0, 2).join(" / ");
  if (params) return `${symbol} · ${strategyName} · ${params}`;
  return `${symbol} · ${strategyName}`;
}

/**
 * Build the Paper Trading Research Deployment Center model.
 * `hasSession` is always false until a real session record exists.
 */
export function buildPaperTradingCenterModel(input: {
  research: ResearchDetail;
  validation: ResearchValidationResult | null;
  evaluation: ResearchEvaluationResult | null;
  /** Reserved for future real session wiring — callers must pass false today. */
  hasSession?: boolean;
}): PaperTradingCenterModel {
  const hasSession = input.hasSession === true;
  const robustness = buildRobustnessCenterModel({
    validation: input.validation,
    evaluation: input.evaluation,
  });

  const { eligibility, reasonKey } = deriveEligibility({
    research: input.research,
    validation: input.validation,
    evaluation: input.evaluation,
    robustnessOverall: robustness.overallStatus,
    robustnessItems: robustness.items,
    hasSession,
  });

  const observationItems: ObservationItemView[] = OBSERVATION_ITEMS.map((id) => ({
    id,
    status: deriveObservationStatus(id, hasSession, robustness.items),
  }));

  const reviewCriteria: ReviewCriterionView[] = REVIEW_CRITERIA.map((id) => ({
    id,
    status: "awaiting_observation",
  }));

  return {
    deployment: {
      researchName: input.research.name,
      experimentLabel: buildExperimentLabel(input.research),
      benchmark: input.research.configuration.benchmark,
      strategy: input.research.configuration.strategyName,
      currentStatus: input.research.status,
    },
    eligibility,
    eligibilityReasonKey: reasonKey,
    observationItems,
    hasSession,
    reviewCriteria,
    nextActionKind: deriveNextAction(eligibility, hasSession),
    hasValidationEvidence: Boolean(input.validation),
    hasEvaluationEvidence: Boolean(input.evaluation),
  };
}
