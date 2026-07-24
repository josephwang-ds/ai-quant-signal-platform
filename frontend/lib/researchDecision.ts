/**
 * Decision readiness derived from implemented evidence only.
 *
 * A human-authored decision record is stored separately; this model never
 * invents approval, rejection, paper-trading state, or performance.
 */

import {
  buildRobustnessCenterModel,
  type RobustnessItemId,
} from "@/lib/researchRobustness";
import type { ResearchDetail } from "@/types/research";
import type { ResearchEvaluationResult } from "@/types/researchEvaluation";
import type { ResearchValidationResult } from "@/types/researchValidation";

export type DecisionStatus = "not_ready" | "under_review" | "ready";

export type DecisionEvidenceId = "validation" | "robustness";

export type DecisionEvidenceStatus = "completed" | "pending";

export type DecisionChecklistId =
  | "validation_completed"
  | "robustness_reviewed"
  | "limitations_documented";

export type DecisionChecklistStatus = "completed" | "pending";

export type DecisionRiskId = RobustnessItemId;

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
  return (
    evaluation?.evaluation_status === "completed" ||
    validation?.validation_status === "completed"
  );
}

export function buildDecisionCenterModel(input: {
  research: ResearchDetail;
  validation: ResearchValidationResult | null;
  evaluation: ResearchEvaluationResult | null;
}): DecisionCenterModel {
  const robustness = buildRobustnessCenterModel({
    validation: input.validation,
    evaluation: input.evaluation,
  });
  const validationDone = validationEvidenceCompleted(
    input.validation,
    input.evaluation
  );
  const robustnessDone = robustness.items.every(
    (item) => item.status === "completed"
  );

  const evidence: DecisionEvidenceView[] = [
    { id: "validation", status: validationDone ? "completed" : "pending" },
    { id: "robustness", status: robustnessDone ? "completed" : "pending" },
  ];

  const remainingRiskIds = robustness.items
    .filter((item) => item.status !== "completed")
    .map((item) => item.id);

  const limitationsDocumented =
    robustness.scopeBoundaryIds.length > 0 ||
    Boolean(input.evaluation?.limitations.length);

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
      id: "limitations_documented",
      status: limitationsDocumented ? "completed" : "pending",
    },
  ];

  const decisionStatus: DecisionStatus = !input.validation
    ? "not_ready"
    : validationDone && robustnessDone
      ? "ready"
      : "under_review";

  return {
    researchName: input.research.name,
    experimentLabel: buildExperimentLabel(input.research),
    decisionStatus,
    evidence,
    remainingRiskIds,
    checklist,
    hasValidationEvidence: Boolean(input.validation),
    hasEvaluationEvidence: Boolean(input.evaluation),
  };
}
