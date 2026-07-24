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
import type {
  BenchmarkVerdict,
  DeterministicEvidenceCheck,
  DeterministicCheckStatus,
} from "@/types/researchBenchmark";
import type { ResearchExecutionResult } from "@/types/researchExecution";
import type { FactorValidationResult } from "@/types/factorValidation";
import type { ResearchValidationResult } from "@/types/researchValidation";

export type DecisionStatus = "not_ready" | "under_review" | "ready";
export type SuggestedResearchDecision = "promote" | "hold" | "reject";

export type DecisionCheckView = DeterministicEvidenceCheck;

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
  suggestedDecision: SuggestedResearchDecision;
  benchmarkVerdict: BenchmarkVerdict;
  evidenceSummary: string;
  checks: DecisionCheckView[];
  passedChecks: DecisionCheckView[];
  failedChecks: DecisionCheckView[];
  inconclusiveChecks: DecisionCheckView[];
  missingChecks: DecisionCheckView[];
  conflictingEvidence: string[];
  requiredNextSteps: string[];
};

function makeCheck(input: {
  checkId: string;
  name: string;
  status: DeterministicCheckStatus;
  observedValue?: number | null;
  threshold?: number | null;
  explanation: string;
  evidenceSource: string;
  severity?: string;
}): DecisionCheckView {
  return {
    check_id: input.checkId,
    name: input.name,
    status: input.status,
    observed_value: input.observedValue ?? null,
    configured_threshold: input.threshold ?? null,
    explanation: input.explanation,
    evidence_source: input.evidenceSource,
    severity: input.severity ?? "supporting",
  };
}

function ratio(numerator: number | null, denominator: number | null): number | null {
  if (
    numerator === null ||
    denominator === null ||
    !Number.isFinite(numerator) ||
    !Number.isFinite(denominator) ||
    denominator === 0
  ) {
    return null;
  }
  return numerator / denominator;
}

function trendValidationChecks(
  validation: ResearchValidationResult | null
): DecisionCheckView[] {
  if (!validation) {
    return [
      makeCheck({
        checkId: "oos",
        name: "Out-of-sample risk-adjusted comparison",
        status: "unavailable",
        explanation: "Run validation to calculate chronological OOS evidence.",
        evidenceSource: "validation.oos",
        severity: "core",
      }),
      makeCheck({
        checkId: "parameter_robustness",
        name: "Nearby-parameter robustness",
        status: "unavailable",
        explanation: "Run validation to calculate the bounded parameter grid.",
        evidenceSource: "validation.parameter_sensitivity",
      }),
      makeCheck({
        checkId: "cost",
        name: "Return after configured transaction cost",
        status: "unavailable",
        explanation: "Run validation to calculate transaction-cost sensitivity.",
        evidenceSource: "validation.transaction_cost_sensitivity",
        severity: "core",
      }),
      makeCheck({
        checkId: "data_quality",
        name: "Blocking data-quality issues",
        status: "unavailable",
        explanation: "Run validation to inspect data quality and provenance.",
        evidenceSource: "validation.data_quality",
        severity: "blocking",
      }),
    ];
  }

  const oosSharpe = validation.oos.out_of_sample_metrics?.sharpe_ratio ?? null;
  const oosBenchmarkSharpe =
    validation.oos.oos_benchmark_metrics?.sharpe_ratio ?? null;
  const oosDifference =
    oosSharpe !== null && oosBenchmarkSharpe !== null
      ? oosSharpe - oosBenchmarkSharpe
      : null;
  const valid = validation.parameter_sensitivity.valid_combination_count;
  const positive = validation.parameter_sensitivity.positive_sharpe_count;
  const positiveRatio = ratio(positive, valid);
  const canonicalCost =
    validation.transaction_cost_sensitivity.canonical_cost_result?.total_return ??
    null;
  const fatalCount = validation.data_quality.fatal_issues.length;

  return [
    makeCheck({
      checkId: "oos",
      name: "Out-of-sample Sharpe versus benchmark",
      status:
        oosDifference === null
          ? "unavailable"
          : oosDifference >= 0
            ? "pass"
            : "fail",
      observedValue: oosDifference,
      threshold: 0,
      explanation:
        oosDifference === null
          ? "OOS strategy or benchmark Sharpe is unavailable."
          : `OOS Sharpe difference is ${oosDifference.toFixed(4)} versus the configured zero margin.`,
      evidenceSource:
        "validation.oos.out_of_sample_metrics.sharpe_ratio - validation.oos.oos_benchmark_metrics.sharpe_ratio",
      severity: "core",
    }),
    makeCheck({
      checkId: "parameter_robustness",
      name: "Positive-Sharpe share across bounded parameter grid",
      status:
        positiveRatio === null
          ? "unavailable"
          : positiveRatio >= 0.5
            ? "pass"
            : "fail",
      observedValue: positiveRatio,
      threshold: 0.5,
      explanation:
        positiveRatio === null
          ? "The parameter grid did not produce comparable results."
          : `${(positiveRatio * 100).toFixed(1)}% of valid parameter cells have positive Sharpe.`,
      evidenceSource:
        "validation.parameter_sensitivity.positive_sharpe_count / valid_combination_count",
    }),
    makeCheck({
      checkId: "cost",
      name: "Return after configured transaction cost",
      status:
        canonicalCost === null
          ? "unavailable"
          : canonicalCost > 0
            ? "pass"
            : "fail",
      observedValue: canonicalCost,
      threshold: 0,
      explanation:
        canonicalCost === null
          ? "The configured-cost result is unavailable."
          : `Configured-cost total return is ${(canonicalCost * 100).toFixed(2)}%.`,
      evidenceSource:
        "validation.transaction_cost_sensitivity.canonical_cost_result.total_return",
      severity: "core",
    }),
    makeCheck({
      checkId: "data_quality",
      name: "Blocking data-quality issues",
      status: fatalCount === 0 ? "pass" : "fail",
      observedValue: fatalCount,
      threshold: 0,
      explanation:
        fatalCount === 0
          ? "No fatal data-quality issues were reported."
          : `${fatalCount} fatal data-quality issue(s) were reported.`,
      evidenceSource: "validation.data_quality.fatal_issues",
      severity: "blocking",
    }),
  ];
}

function buildExperimentLabel(research: ResearchDetail): string {
  const { symbol, strategyName, parameterLines } = research.configuration;
  const params = parameterLines.slice(0, 2).join(" / ");
  if (params) return `${symbol} · ${strategyName} · ${params}`;
  return `${symbol} · ${strategyName}`;
}

function validationEvidenceCompleted(
  validation: ResearchValidationResult | null,
  evaluation: ResearchEvaluationResult | null,
  factorValidationCompleted = false
): boolean {
  return (
    factorValidationCompleted ||
    evaluation?.evaluation_status === "completed" ||
    validation?.validation_status === "completed"
  );
}

export function buildDecisionCenterModel(input: {
  research: ResearchDetail;
  validation: ResearchValidationResult | null;
  evaluation: ResearchEvaluationResult | null;
  /** Factor studies use RankIC/quantile completion instead of MA stages. */
  factorValidationCompleted?: boolean;
  execution?: ResearchExecutionResult | null;
  factorValidation?: FactorValidationResult | null;
}): DecisionCenterModel {
  const robustness = buildRobustnessCenterModel({
    validation: input.validation,
    evaluation: input.evaluation,
  });
  const factorDone = Boolean(input.factorValidationCompleted);
  const validationDone = validationEvidenceCompleted(
    input.validation,
    input.evaluation,
    factorDone
  );
  // Factor path has no MA robustness stages; treat validation completion as reviewed.
  const robustnessDone = factorDone
    ? validationDone
    : robustness.items.every((item) => item.status === "completed");

  const evidence: DecisionEvidenceView[] = [
    { id: "validation", status: validationDone ? "completed" : "pending" },
    { id: "robustness", status: robustnessDone ? "completed" : "pending" },
  ];

  const remainingRiskIds = factorDone
    ? []
    : robustness.items
        .filter((item) => item.status !== "completed")
        .map((item) => item.id);

  const limitationsDocumented =
    input.research.knownWeaknesses.length > 0 ||
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

  const hasAnyEvidence =
    Boolean(input.execution) || Boolean(input.validation) || factorDone;

  const benchmark =
    input.factorValidation?.benchmark ??
    input.validation?.benchmark_evaluation ??
    input.execution?.benchmark_comparison;
  const candidateChecks: DecisionCheckView[] = benchmark?.checks?.length
    ? benchmark.checks
    : factorDone
      ? []
      : trendValidationChecks(input.validation);
  const checks = Array.from(
    new Map(candidateChecks.map((item) => [item.check_id, item])).values()
  );
  const passedChecks = checks.filter((item) => item.status === "pass");
  const failedChecks = checks.filter((item) => item.status === "fail");
  const inconclusiveChecks = checks.filter(
    (item) => item.status === "inconclusive"
  );
  const missingChecks = checks.filter((item) => item.status === "unavailable");
  const blockingFailure = failedChecks.some(
    (item) => item.severity === "blocking"
  );
  const coreChecks = checks.filter((item) => item.severity === "core");
  const passedCore = coreChecks.filter((item) => item.status === "pass");
  const failedCore = coreChecks.filter((item) => item.status === "fail");
  const unresolvedCore = coreChecks.filter(
    (item) =>
      item.status === "inconclusive" || item.status === "unavailable"
  );
  const benchmarkVerdict = benchmark?.verdict ?? "unavailable";
  const mixedCoreEvidence = passedCore.length > 0 && failedCore.length > 0;
  const allAvailableCoreFailed =
    failedCore.length > 0 &&
    passedCore.length === 0 &&
    unresolvedCore.length === 0;
  const suggestedDecision: SuggestedResearchDecision =
    blockingFailure || allAvailableCoreFailed
      ? "reject"
      : mixedCoreEvidence
        ? "hold"
        : benchmarkVerdict === "pass" &&
            unresolvedCore.length === 0 &&
            failedCore.length === 0 &&
            robustnessDone &&
            validationDone
        ? "promote"
        : "hold";
  const conflictingEvidence =
    passedChecks.length > 0 && failedChecks.length > 0
      ? [
          `${passedChecks.length} check(s) passed while ${failedChecks.length} failed.`,
        ]
      : [];
  const requiredNextSteps = [
    ...missingChecks.map((item) => `Complete: ${item.name}`),
    ...inconclusiveChecks.map((item) => `Resolve: ${item.name}`),
    ...failedChecks.map((item) => `Review failure: ${item.name}`),
  ];
  const evidenceSummary =
    checks.length === 0
      ? "No deterministic decision checks are available yet."
      : `${passedChecks.length} passed · ${failedChecks.length} failed · ${inconclusiveChecks.length} inconclusive · ${missingChecks.length} unavailable.`;

  const decisionStatus: DecisionStatus = !hasAnyEvidence
    ? "not_ready"
    : suggestedDecision === "promote" && validationDone && robustnessDone
      ? "ready"
      : "under_review";

  return {
    researchName: input.research.name,
    experimentLabel: buildExperimentLabel(input.research),
    decisionStatus,
    evidence,
    remainingRiskIds,
    checklist,
    hasValidationEvidence: hasAnyEvidence,
    hasEvaluationEvidence: Boolean(input.evaluation),
    suggestedDecision,
    benchmarkVerdict,
    evidenceSummary,
    checks,
    passedChecks,
    failedChecks,
    inconclusiveChecks,
    missingChecks,
    conflictingEvidence,
    requiredNextSteps,
  };
}
