/**
 * Transitional re-exports — prefer `@/lib/platformArchitecture`.
 */

export {
  ENGINE_STAGES as WORKFLOW_STAGES,
  FLAGSHIP_RESEARCH,
  US_LIQUID_31_SYMBOLS,
  UNIVERSE_PREVIEW_SYMBOLS,
  getContinueTarget,
  getCurrentEngineStage as getCurrentStage,
  stageStatusLabel,
  type EngineStage as WorkflowStage,
  type EngineStageId as WorkflowStageId,
  type EngineStageStatus as WorkflowStageStatus,
} from "@/lib/platformArchitecture";

/** @deprecated Prefer ENGINE_STAGES status labels */
export type PipelinePhaseStatus = "verified" | "next" | "not_started";

export function pipelineStatusLabel(
  status: PipelinePhaseStatus,
  language: "en" | "zh"
): string {
  if (language === "zh") {
    if (status === "verified") return "已验证";
    if (status === "next") return "下一步";
    return "未开始";
  }
  if (status === "verified") return "Verified";
  if (status === "next") return "Next";
  return "Not Started";
}
