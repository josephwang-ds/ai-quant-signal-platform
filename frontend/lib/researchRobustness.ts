/**
 * PR-024 Research Robustness Center — management projection only.
 *
 * Derives checklist status from existing Validation / Evaluation evidence.
 * Does not invent metrics, run stress tests, or invent failure frequencies.
 */

import type { ResearchEvaluationResult } from "@/types/researchEvaluation";
import type { ResearchValidationResult } from "@/types/researchValidation";

export type RobustnessItemStatus =
  | "completed"
  | "pending"
  | "blocked";

export type RobustnessItemId =
  | "parameter_sensitivity"
  | "benchmark_comparison"
  | "transaction_cost"
  | "data_quality";

export type RobustnessScopeBoundaryId =
  | "market_regime"
  | "walk_forward"
  | "monte_carlo"
  | "liquidity_capacity";

export type RobustnessMatrixItem = {
  id: RobustnessItemId;
  /** Canonical English label used to match evaluation stage labels. */
  label: string;
  /** Validation stage key when the check is implemented in PR-009. */
  validationStage: string | null;
  /** Exact evaluation stage labels (English) when present in evaluation payloads. */
  evaluationLabels: string[];
};

export type RobustnessOverallStatus =
  | "not_started"
  | "in_progress"
  | "blocked"
  | "complete";

export type RobustnessItemView = RobustnessMatrixItem & {
  status: RobustnessItemStatus;
};

export type RobustnessCenterModel = {
  overallStatus: RobustnessOverallStatus;
  items: RobustnessItemView[];
  scopeBoundaryIds: RobustnessScopeBoundaryId[];
  nextItemId: RobustnessItemId | null;
  nextActionKind:
    | "resolve_blocker"
    | "continue_item"
    | "start_observation"
    | "none";
  hasEvaluationEvidence: boolean;
  hasValidationEvidence: boolean;
};

/** Fixed catalogue — order matches the product matrix. */
export const ROBUSTNESS_MATRIX_ITEMS: readonly RobustnessMatrixItem[] = [
  {
    id: "parameter_sensitivity",
    label: "Parameter Sensitivity",
    validationStage: "parameter_sensitivity",
    evaluationLabels: ["Parameter sensitivity"],
  },
  {
    id: "benchmark_comparison",
    label: "Benchmark Comparison",
    validationStage: "benchmark_comparison",
    evaluationLabels: ["Benchmark comparison"],
  },
  {
    id: "transaction_cost",
    label: "Transaction Cost",
    validationStage: "transaction_cost_sensitivity",
    evaluationLabels: ["Transaction-cost sensitivity"],
  },
  {
    id: "data_quality",
    label: "Data Quality",
    validationStage: "data_quality",
    evaluationLabels: ["Data quality"],
  },
] as const;

/** Concise disclosure, not executable checklist items. */
export const ROBUSTNESS_SCOPE_BOUNDARIES: readonly RobustnessScopeBoundaryId[] = [
  "market_regime",
  "walk_forward",
  "monte_carlo",
  "liquidity_capacity",
] as const;

function normalize(value: string): string {
  return value.trim().toLowerCase();
}

function matchesEvaluationLabel(
  item: RobustnessMatrixItem,
  label: string
): boolean {
  const n = normalize(label);
  return item.evaluationLabels.some((candidate) => normalize(candidate) === n);
}

function evaluationStageStatus(
  evaluation: ResearchEvaluationResult,
  item: RobustnessMatrixItem
): RobustnessItemStatus | null {
  const summary = (evaluation.evidence_summary ?? []).find((row) =>
    matchesEvaluationLabel(item, row.label)
  );
  if (summary) {
    if (summary.status === "completed") return "completed";
    if (summary.status === "failed" || summary.status === "blocked") {
      return "blocked";
    }
    if (summary.status === "incomplete") return "pending";
    if (summary.status === "unavailable") return "pending";
  }

  if (
    (evaluation.completed_stages ?? []).some((label) =>
      matchesEvaluationLabel(item, label)
    )
  ) {
    return "completed";
  }

  if (
    (evaluation.incomplete_stages ?? []).some((label) =>
      matchesEvaluationLabel(item, label)
    )
  ) {
    return "pending";
  }

  if (
    (evaluation.unavailable_stages ?? []).some((label) =>
      matchesEvaluationLabel(item, label)
    )
  ) {
    return "pending";
  }

  return null;
}

function validationStageStatus(
  validation: ResearchValidationResult,
  item: RobustnessMatrixItem
): RobustnessItemStatus | null {
  if (!item.validationStage) return null;

  const stage = validation.stages?.find(
    (row) => row.stage === item.validationStage
  );
  if (stage) {
    if (stage.status === "completed") return "completed";
    if (stage.status === "failed") return "blocked";
    if (stage.status === "incomplete") return "pending";
    if (stage.status === "unavailable") return "pending";
  }

  // Fallback to nested stage objects when stages[] entry is missing.
  if (item.validationStage === "parameter_sensitivity" && validation.parameter_sensitivity) {
    if (validation.parameter_sensitivity.status === "completed") return "completed";
    if (validation.parameter_sensitivity.status === "failed") return "blocked";
    if (validation.parameter_sensitivity.status === "incomplete") return "pending";
  }
  if (
    item.validationStage === "transaction_cost_sensitivity" &&
    validation.transaction_cost_sensitivity
  ) {
    if (validation.transaction_cost_sensitivity.status === "completed") return "completed";
    if (validation.transaction_cost_sensitivity.status === "failed") return "blocked";
    if (validation.transaction_cost_sensitivity.status === "incomplete") return "pending";
  }
  if (item.validationStage === "data_quality" && validation.data_quality) {
    if (validation.data_quality.status === "completed") return "completed";
    if (validation.data_quality.status === "failed") return "blocked";
    if (validation.data_quality.status === "incomplete") return "pending";
  }
  if (item.validationStage === "benchmark_comparison") {
    const fromStages = validation.stages?.find(
      (row) => row.stage === "benchmark_comparison"
    );
    if (fromStages?.status === "completed") return "completed";
    if (fromStages?.status === "failed") return "blocked";
    if (fromStages?.status === "incomplete") return "pending";
  }

  return null;
}

function deriveItemStatus(
  item: RobustnessMatrixItem,
  validation: ResearchValidationResult | null,
  evaluation: ResearchEvaluationResult | null
): RobustnessItemStatus {
  if (evaluation) {
    const fromEval = evaluationStageStatus(evaluation, item);
    if (fromEval) {
      if (
        fromEval === "pending" &&
        evaluation.evaluation_status === "blocked" &&
        (evaluation.blockers?.length ?? 0) > 0
      ) {
        return "blocked";
      }
      return fromEval;
    }
  }

  if (validation) {
    const fromVal = validationStageStatus(validation, item);
    if (fromVal) return fromVal;
  }

  // Implemented check, but no evidence yet → pending workflow.
  return "pending";
}

function deriveOverallStatus(
  items: RobustnessItemView[]
): RobustnessOverallStatus {
  if (items.some((item) => item.status === "blocked")) return "blocked";
  if (items.every((item) => item.status === "completed")) return "complete";
  if (items.some((item) => item.status === "pending")) return "in_progress";
  return "not_started";
}

export function buildRobustnessCenterModel(input: {
  validation: ResearchValidationResult | null;
  evaluation: ResearchEvaluationResult | null;
}): RobustnessCenterModel {
  const { validation, evaluation } = input;

  const items: RobustnessItemView[] = ROBUSTNESS_MATRIX_ITEMS.map((item) => ({
    ...item,
    status: deriveItemStatus(item, validation, evaluation),
  }));

  const blocked = items.find((item) => item.status === "blocked");
  const pending = items.find((item) => item.status === "pending");

  let nextItemId: RobustnessItemId | null = null;
  let nextActionKind: RobustnessCenterModel["nextActionKind"] = "none";

  if (blocked) {
    nextItemId = blocked.id;
    nextActionKind = "resolve_blocker";
  } else if (pending) {
    nextItemId = pending.id;
    nextActionKind = "continue_item";
  } else if (items.some((item) => item.status === "completed")) {
    nextActionKind = "start_observation";
  }

  return {
    overallStatus:
      !validation && !evaluation ? "not_started" : deriveOverallStatus(items),
    items,
    scopeBoundaryIds: [...ROBUSTNESS_SCOPE_BOUNDARIES],
    nextItemId,
    nextActionKind,
    hasEvaluationEvidence: Boolean(evaluation),
    hasValidationEvidence: Boolean(validation),
  };
}
