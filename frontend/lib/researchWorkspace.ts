/**
 * Research progress helpers（纯函数，便于单测）。
 */

import {
  RESEARCH_PROGRESS_STAGES,
  type ResearchProgressStage,
} from "@/types/research";

export type LifecycleStepState = "completed" | "current" | "upcoming";

export function getLifecycleStepState(
  stage: ResearchProgressStage,
  currentStage: ResearchProgressStage
): LifecycleStepState {
  const stageIndex = RESEARCH_PROGRESS_STAGES.indexOf(stage);
  const currentIndex = RESEARCH_PROGRESS_STAGES.indexOf(currentStage);

  if (stageIndex < 0 || currentIndex < 0) {
    return "upcoming";
  }
  if (stageIndex < currentIndex) {
    return "completed";
  }
  if (stageIndex === currentIndex) {
    return "current";
  }
  return "upcoming";
}

export function isResearchWorkspaceSection(
  value: string | null | undefined
): value is import("@/types/research").ResearchWorkspaceSection {
  return (
    value === "overview" ||
    value === "notebook" ||
    value === "experiments" ||
    value === "validation" ||
    value === "evaluation" ||
    value === "robustness" ||
    value === "paper" ||
    value === "decision" ||
    value === "archive" ||
    value === "copilot" ||
    value === "timeline" ||
    value === "files" ||
    value === "settings"
  );
}

/** 解析 ?tab= 或 ?section=（向后兼容 PR-003）。
 *  ?tab=evaluation 归一到 validation（Evidence 合并标签）。
 */
export function resolveWorkspaceSection(
  tabParam: string | null,
  sectionParam: string | null
): import("@/types/research").ResearchWorkspaceSection {
  const candidate = tabParam ?? sectionParam;
  if (candidate === "evaluation") {
    return "validation";
  }
  return isResearchWorkspaceSection(candidate) ? candidate : "overview";
}
