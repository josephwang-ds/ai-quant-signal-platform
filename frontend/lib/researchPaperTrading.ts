/**
 * Paper-observation eligibility derived from implemented evidence.
 *
 * Session state comes from a real browser-local observation record. The model
 * never invents orders, fills, positions, returns, or PnL.
 */

import { buildRobustnessCenterModel } from "@/lib/researchRobustness";
import type { PaperObservationStatus } from "@/lib/researchPaperObservation";
import type { ResearchDetail } from "@/types/research";
import type { ResearchEvaluationResult } from "@/types/researchEvaluation";
import type { ResearchValidationResult } from "@/types/researchValidation";

export type PaperEligibilityStatus =
  | "not_eligible"
  | "needs_review"
  | "eligible"
  | "active"
  | "completed";

export type PaperEligibilityReason =
  | "no_validation"
  | "blocked"
  | "incomplete"
  | "eligible"
  | "active"
  | "completed";

export type PaperTradingCenterModel = {
  researchName: string;
  experimentLabel: string;
  benchmark: string;
  eligibility: PaperEligibilityStatus;
  eligibilityReasonKey: PaperEligibilityReason;
  sessionStatus: PaperObservationStatus | null;
  hasValidationEvidence: boolean;
  hasEvaluationEvidence: boolean;
};

function buildExperimentLabel(research: ResearchDetail): string {
  const { symbol, strategyName, parameterLines } = research.configuration;
  const params = parameterLines.slice(0, 2).join(" / ");
  if (params) return `${symbol} · ${strategyName} · ${params}`;
  return `${symbol} · ${strategyName}`;
}

export function buildPaperTradingCenterModel(input: {
  research: ResearchDetail;
  validation: ResearchValidationResult | null;
  evaluation: ResearchEvaluationResult | null;
  sessionStatus?: PaperObservationStatus | null;
}): PaperTradingCenterModel {
  const sessionStatus = input.sessionStatus ?? null;
  const robustness = buildRobustnessCenterModel({
    validation: input.validation,
    evaluation: input.evaluation,
  });

  let eligibility: PaperEligibilityStatus;
  let eligibilityReasonKey: PaperEligibilityReason;

  if (sessionStatus === "active") {
    eligibility = "active";
    eligibilityReasonKey = "active";
  } else if (sessionStatus === "completed") {
    eligibility = "completed";
    eligibilityReasonKey = "completed";
  } else if (!input.validation) {
    eligibility = "not_eligible";
    eligibilityReasonKey = "no_validation";
  } else if (
    input.validation.validation_status === "failed" ||
    input.evaluation?.evaluation_status === "blocked" ||
    robustness.items.some((item) => item.status === "blocked")
  ) {
    eligibility = "needs_review";
    eligibilityReasonKey = "blocked";
  } else if (
    input.validation.validation_status !== "completed" ||
    input.evaluation?.evaluation_status !== "completed" ||
    robustness.items.some((item) => item.status !== "completed")
  ) {
    eligibility = "needs_review";
    eligibilityReasonKey = "incomplete";
  } else {
    eligibility = "eligible";
    eligibilityReasonKey = "eligible";
  }

  return {
    researchName: input.research.name,
    experimentLabel: buildExperimentLabel(input.research),
    benchmark: input.research.configuration.benchmark,
    eligibility,
    eligibilityReasonKey,
    sessionStatus,
    hasValidationEvidence: Boolean(input.validation),
    hasEvaluationEvidence: Boolean(input.evaluation),
  };
}
