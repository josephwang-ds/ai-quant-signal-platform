/**
 * Research Evaluation 纯函数：权重校验、置信度推导、就绪规则、筛选。
 *
 * TODO(backend): 替换为 Research Evaluation Engine；AI 不得计算这些值。
 */

import {
  EVALUATION_DIMENSION_KEYS,
  EVALUATION_DIMENSION_WEIGHTS,
  type ConfidenceLevel,
  type DecisionReadiness,
  type EvaluationDimension,
  type EvaluationFilters,
  type EvaluationIssue,
  type EvaluationOverviewStats,
  type EvaluationSnapshot,
  type ResearchHealth,
} from "@/types/evaluation";

export function getEvaluationWeightsTotal(): number {
  return EVALUATION_DIMENSION_KEYS.reduce(
    (sum, key) => sum + EVALUATION_DIMENSION_WEIGHTS[key],
    0
  );
}

export function computeWeightedContribution(
  score: number,
  weight: number
): number {
  return (score * weight) / 100;
}

/**
 * Research Confidence = Σ (dimensionScore × weight / 100)，四舍五入为整数。
 * Demo-only；非收益预测概率。
 */
export function computeResearchConfidence(
  dimensions: Pick<EvaluationDimension, "score" | "weight">[]
): number {
  const total = dimensions.reduce(
    (sum, dimension) =>
      sum + computeWeightedContribution(dimension.score, dimension.weight),
    0
  );
  return Math.round(total);
}

export function deriveConfidenceLevel(score: number): ConfidenceLevel {
  if (score >= 90) {
    return "High";
  }
  if (score >= 80) {
    return "Moderate";
  }
  if (score >= 60) {
    return "Low";
  }
  return "Insufficient Evidence";
}

function dimensionByKey(
  dimensions: EvaluationDimension[],
  key: EvaluationDimension["key"]
): EvaluationDimension | undefined {
  return dimensions.find((item) => item.key === key);
}

function isPassingStatus(status: EvaluationDimension["status"]): boolean {
  return status === "Strong" || status === "Acceptable";
}

function hasCriticalBlocker(issues: EvaluationIssue[]): boolean {
  return issues.some(
    (issue) => issue.kind === "blocker" && issue.severity === "critical"
  );
}

/**
 * 确定性就绪推荐（mock 规则，非投资建议）。
 */
export function deriveDecisionReadiness(
  snapshot: Pick<
    EvaluationSnapshot,
    "dimensions" | "issues" | "dataConfidence" | "hasValidationData" | "status"
  >,
  confidenceScore: number
): DecisionReadiness {
  if (!snapshot.hasValidationData || snapshot.status === "Missing Validation") {
    return "Continue Research";
  }

  const critical = hasCriticalBlocker(snapshot.issues);
  const stress = dimensionByKey(snapshot.dimensions, "stress_test_resilience");
  const oos = dimensionByKey(snapshot.dimensions, "out_of_sample_performance");
  const risk = dimensionByKey(snapshot.dimensions, "risk_review");
  const dataOk =
    snapshot.dataConfidence === "high" || snapshot.dataConfidence === "medium";

  const dataInvalid =
    snapshot.dataConfidence === "degraded" ||
    dimensionByKey(snapshot.dimensions, "data_quality")?.status === "Failed";

  if (
    dataInvalid ||
    stress?.status === "Failed" ||
    risk?.status === "Failed" ||
    (critical && confidenceScore < 60)
  ) {
    if (stress?.status === "Failed" || risk?.status === "Failed") {
      // Mandatory criteria failed but work continues → Continue Validation
      // unless evidence is catastrophic
      if (confidenceScore < 60 || dataInvalid) {
        return "Rework Required";
      }
      return "Continue Validation";
    }
    if (dataInvalid) {
      return "Rework Required";
    }
  }

  const readyForPaper =
    confidenceScore >= 85 &&
    oos !== undefined &&
    isPassingStatus(oos.status) &&
    stress !== undefined &&
    isPassingStatus(stress.status) &&
    risk !== undefined &&
    isPassingStatus(risk.status) &&
    !critical &&
    dataOk;

  if (readyForPaper) {
    return "Ready for Paper Trading";
  }

  const requiredComplete = snapshot.dimensions.every(
    (dimension) =>
      dimension.status !== "Missing" && dimension.status !== "Inconclusive"
  );
  const noCritical = !critical;
  const coverageOk = snapshot.dimensions.filter((d) => d.evidenceRefs.length > 0)
    .length >= 8;

  if (
    requiredComplete &&
    noCritical &&
    coverageOk &&
    confidenceScore >= 80 &&
    stress &&
    isPassingStatus(stress.status)
  ) {
    return "Ready for Evaluation Review";
  }

  if (confidenceScore < 50 && snapshot.dimensions.every((d) => d.status === "Missing")) {
    return "Archive Research";
  }

  return "Continue Validation";
}

export function deriveResearchHealth(
  confidenceScore: number,
  issues: EvaluationIssue[],
  readiness: DecisionReadiness
): ResearchHealth {
  if (readiness === "Rework Required" || hasCriticalBlocker(issues)) {
    return "Blocked";
  }
  if (confidenceScore >= 85 && readiness === "Ready for Paper Trading") {
    return "Healthy";
  }
  if (confidenceScore >= 70) {
    return "Watch";
  }
  return "Degraded";
}

export function buildEvaluationOverview(
  snapshot: EvaluationSnapshot
): EvaluationOverviewStats {
  const confidenceScore = computeResearchConfidence(snapshot.dimensions);
  const decisionReadiness = deriveDecisionReadiness(snapshot, confidenceScore);
  const confidenceLevel = deriveConfidenceLevel(confidenceScore);
  const researchHealth = deriveResearchHealth(
    confidenceScore,
    snapshot.issues,
    decisionReadiness
  );

  return {
    confidenceScore,
    confidenceLevel,
    researchHealth,
    decisionReadiness,
    recommendation: decisionReadiness,
    evaluationStatus: snapshot.status,
    lastEvaluatedAt: snapshot.evaluatedAt,
    lifecycleStage: snapshot.lifecycleStage,
    dataConfidence: snapshot.dataConfidence,
    blockerCount: snapshot.issues.filter((issue) => issue.kind === "blocker")
      .length,
    evidenceCoveragePct: snapshot.evidenceCoveragePct,
  };
}

/**
 * Align recommendation panel with derived readiness when catalog is authored.
 * Callers should keep recommendation.recommendation in sync with deriveDecisionReadiness.
 */
export function assertRecommendationMatchesRules(
  snapshot: EvaluationSnapshot
): DecisionReadiness {
  const score = computeResearchConfidence(snapshot.dimensions);
  return deriveDecisionReadiness(snapshot, score);
}

export function filterEvaluationDimensions(
  dimensions: EvaluationDimension[],
  filters: EvaluationFilters
): EvaluationDimension[] {
  const query = filters.query.trim().toLowerCase();
  return dimensions.filter((dimension) => {
    if (filters.status !== "all" && dimension.status !== filters.status) {
      return false;
    }
    if (!query) {
      return true;
    }
    const haystack = [
      dimension.name,
      dimension.summary,
      ...dimension.limitations,
      ...dimension.evidenceRefs,
      ...dimension.evidenceLinks.map((link) => link.claim),
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(query);
  });
}

export function buildPaperTradingRuleChecks(
  snapshot: EvaluationSnapshot,
  confidenceScore: number
): { id: string; rule: string; passed: boolean; observed: string }[] {
  const stress = dimensionByKey(snapshot.dimensions, "stress_test_resilience");
  const oos = dimensionByKey(snapshot.dimensions, "out_of_sample_performance");
  const risk = dimensionByKey(snapshot.dimensions, "risk_review");
  const critical = hasCriticalBlocker(snapshot.issues);
  const dataOk =
    snapshot.dataConfidence === "high" || snapshot.dataConfidence === "medium";

  return [
    {
      id: "rule-confidence",
      rule: "Research Confidence ≥ 85",
      passed: confidenceScore >= 85,
      observed: String(confidenceScore),
    },
    {
      id: "rule-oos",
      rule: "Out-of-sample status Passed (Strong/Acceptable)",
      passed: oos !== undefined && isPassingStatus(oos.status),
      observed: oos?.status ?? "Missing",
    },
    {
      id: "rule-stress",
      rule: "Stress testing Passed (Strong/Acceptable)",
      passed: stress !== undefined && isPassingStatus(stress.status),
      observed: stress?.status ?? "Missing",
    },
    {
      id: "rule-risk",
      rule: "Risk review Approved (Strong/Acceptable)",
      passed: risk !== undefined && isPassingStatus(risk.status),
      observed: risk?.status ?? "Missing",
    },
    {
      id: "rule-blocker",
      rule: "No critical blocker",
      passed: !critical,
      observed: critical ? "critical blocker present" : "none",
    },
    {
      id: "rule-data",
      rule: "Data confidence acceptable (high/medium)",
      passed: dataOk,
      observed: snapshot.dataConfidence,
    },
  ];
}
