/**
 * Research Readiness — workflow completeness, not a performance or AI confidence score.
 */

import { getResearchDecisionRecord } from "@/lib/researchDecisionRecord";
import { buildDecisionCenterModel } from "@/lib/researchDecision";
import type { ResearchDetail } from "@/types/research";
import type { ResearchEvaluationResult } from "@/types/researchEvaluation";
import type { ResearchValidationResult } from "@/types/researchValidation";
import type { FactorValidationResult } from "@/types/factorValidation";

export type ResearchReadinessItemId =
  | "research_question"
  | "hypothesis"
  | "protocol"
  | "validation"
  | "robustness"
  | "decision"
  | "limitations";

export type ResearchReadinessItem = {
  id: ResearchReadinessItemId;
  complete: boolean;
};

export type ResearchReadinessModel = {
  items: ResearchReadinessItem[];
  completedCount: number;
  totalCount: number;
};

function hasText(value: string | undefined | null): boolean {
  return Boolean(value && value.trim().length > 0);
}

function protocolDefined(research: ResearchDetail): boolean {
  if (research.runConfiguration) return true;
  return (
    research.configuration.parameterLines.length > 0 &&
    hasText(research.configuration.symbol)
  );
}

function validationCompleted(input: {
  validation: ResearchValidationResult | null;
  factorValidation: FactorValidationResult | null;
}): boolean {
  if (input.factorValidation?.validation_status === "completed") return true;
  if (input.factorValidation?.ic?.summary?.n_periods) {
    return input.factorValidation.ic.summary.n_periods > 0;
  }
  return input.validation?.validation_status === "completed";
}

export function buildResearchReadinessModel(input: {
  research: ResearchDetail;
  validation?: ResearchValidationResult | null;
  evaluation?: ResearchEvaluationResult | null;
  factorValidation?: FactorValidationResult | null;
  decisionRecorded?: boolean;
}): ResearchReadinessModel {
  const validation = input.validation ?? null;
  const evaluation = input.evaluation ?? null;
  const factorValidation = input.factorValidation ?? null;

  const decisionModel = buildDecisionCenterModel({
    research: input.research,
    validation,
    evaluation,
    factorValidationCompleted: validationCompleted({
      validation,
      factorValidation,
    }),
  });

  const robustnessReviewed =
    decisionModel.checklist.find((item) => item.id === "robustness_reviewed")
      ?.status === "completed";

  const limitationsAcknowledged =
    input.research.knownWeaknesses.length > 0 ||
    decisionModel.checklist.find((item) => item.id === "limitations_documented")
      ?.status === "completed";

  const decisionRecorded =
    input.decisionRecorded ??
    Boolean(getResearchDecisionRecord(input.research.id));

  const items: ResearchReadinessItem[] = [
    {
      id: "research_question",
      complete: hasText(input.research.researchQuestion),
    },
    {
      id: "hypothesis",
      complete: hasText(input.research.hypothesis),
    },
    {
      id: "protocol",
      complete: protocolDefined(input.research),
    },
    {
      id: "validation",
      complete: validationCompleted({ validation, factorValidation }),
    },
    {
      id: "robustness",
      complete: robustnessReviewed,
    },
    {
      id: "decision",
      complete: decisionRecorded,
    },
    {
      id: "limitations",
      complete: limitationsAcknowledged,
    },
  ];

  return {
    items,
    completedCount: items.filter((item) => item.complete).length,
    totalCount: items.length,
  };
}
