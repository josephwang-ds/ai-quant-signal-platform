/**
 * Validation Pipeline 纯函数：筛选、概览统计、就绪度推导。
 *
 * TODO(backend): 替换为 Validation Application 用例；闸口结果由确定性引擎产出，非 AI。
 */

import type {
  ValidationBlocker,
  ValidationFilters,
  ValidationOverviewStats,
  ValidationPipelineSnapshot,
  ValidationReadinessLabel,
  ValidationStage,
  ValidationStatus,
} from "@/types/validation";

const TERMINAL_COMPLETED: ValidationStatus[] = [
  "Passed",
  "Failed",
  "Inconclusive",
  "Invalidated",
];

export function isCompletedValidationStatus(status: ValidationStatus): boolean {
  return TERMINAL_COMPLETED.includes(status);
}

/**
 * 确定性就绪度（mock 规则，非投资建议）。
 *
 * - Ready for Evaluation: 全部阶段 Passed 且无 blocking
 * - Insufficient Evidence: 完成阶段 < 4，且尚未形成可继续的失败叙事
 * - Blocked: 证据不足且存在 blocking，几乎无法推进（如数据接合阻塞）
 * - Continue Validation: 其余情况（含 Failed / Inconclusive 需继续验证；
 *   主 demo：Stress Failed → Continue Validation）
 */
export function deriveValidationReadiness(
  stages: ValidationStage[],
  blockers: ValidationBlocker[]
): ValidationReadinessLabel {
  const blocking = blockers.filter((item) => item.severity === "blocking");
  const completed = stages.filter((stage) =>
    isCompletedValidationStatus(stage.status)
  );
  const passed = stages.filter((stage) => stage.status === "Passed");

  if (
    stages.length > 0 &&
    stages.every((stage) => stage.status === "Passed") &&
    blocking.length === 0
  ) {
    return "Ready for Evaluation";
  }

  if (completed.length < 4) {
    if (blocking.length > 0 && passed.length < 2) {
      return "Blocked";
    }
    return "Insufficient Evidence";
  }

  // Enough completed checks; open failures / inconclusive / blockers → continue
  return "Continue Validation";
}

export function buildValidationOverview(
  snapshot: ValidationPipelineSnapshot
): ValidationOverviewStats {
  const { stages, blockers, lastValidationAt } = snapshot;
  const passedCount = stages.filter((s) => s.status === "Passed").length;
  const failedCount = stages.filter((s) => s.status === "Failed").length;
  const inconclusiveCount = stages.filter(
    (s) => s.status === "Inconclusive"
  ).length;
  const notStartedCount = stages.filter((s) => s.status === "Not Started").length;
  const runningCount = stages.filter((s) => s.status === "Running").length;
  const completedCount = stages.filter((s) =>
    isCompletedValidationStatus(s.status)
  ).length;

  let overallStatus: ValidationOverviewStats["overallStatus"] = "Mixed";
  if (failedCount > 0) {
    overallStatus = "Failed";
  } else if (runningCount > 0) {
    overallStatus = "Running";
  } else if (
    completedCount === stages.length &&
    passedCount === stages.length
  ) {
    overallStatus = "Passed";
  } else if (
    completedCount === stages.length &&
    inconclusiveCount > 0 &&
    failedCount === 0
  ) {
    overallStatus = "Inconclusive";
  } else if (completedCount === 0 && notStartedCount === stages.length) {
    overallStatus = "Not Started";
  }

  return {
    overallStatus,
    completedCount,
    passedCount,
    failedCount,
    inconclusiveCount,
    notStartedCount,
    runningCount,
    blockingCount: blockers.filter((b) => b.severity === "blocking").length,
    lastValidationAt,
    readiness: deriveValidationReadiness(stages, blockers),
  };
}

export function filterValidationStages(
  stages: ValidationStage[],
  filters: ValidationFilters
): ValidationStage[] {
  const query = filters.query.trim().toLowerCase();
  return stages.filter((stage) => {
    if (filters.status !== "all" && stage.status !== filters.status) {
      return false;
    }
    if (!query) {
      return true;
    }
    const haystack = [
      stage.name,
      stage.purpose,
      stage.keyResult,
      stage.owner,
      ...stage.warnings,
      ...stage.evidenceRefs,
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(query);
  });
}

export function getValidationStageById(
  stages: ValidationStage[],
  stageId: string
): ValidationStage | null {
  return stages.find((stage) => stage.id === stageId) ?? null;
}
