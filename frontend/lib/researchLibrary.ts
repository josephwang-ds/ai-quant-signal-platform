/**
 * PR-027 Research Library — homepage projection only.
 *
 * Organises existing research threads. Does not invent projects, activity, or metrics.
 */

import { getMockTimelineEvents } from "@/lib/mockNotebookCatalog";
import type { ResearchLifecycleStatus, ResearchListItem } from "@/types/research";
import type { ResearchTimelineEvent } from "@/types/notebook";

export type LibraryLifecycleStageId =
  | "research"
  | "experiment"
  | "validation"
  | "robustness"
  | "paper"
  | "decision"
  | "archive";

export const LIBRARY_LIFECYCLE_STAGES: readonly LibraryLifecycleStageId[] = [
  "research",
  "experiment",
  "validation",
  "robustness",
  "paper",
  "decision",
  "archive",
] as const;

export type LibraryLifecycleProgress = {
  completed: LibraryLifecycleStageId[];
  current: LibraryLifecycleStageId | null;
};

/**
 * Map operational lifecycle status onto the product spine stages.
 * Only stages that are already past are marked completed.
 */
export function getLibraryLifecycleProgress(
  status: ResearchLifecycleStatus
): LibraryLifecycleProgress {
  switch (status) {
    case "Draft":
    case "Data Integration":
      return { completed: [], current: "research" };
    case "Running":
      return { completed: ["research"], current: "experiment" };
    case "Review":
      return {
        completed: ["research", "experiment"],
        current: "validation",
      };
    case "Validated":
      return {
        completed: ["research", "experiment", "validation"],
        current: "robustness",
      };
    case "Paper Trading":
      return {
        completed: ["research", "experiment", "validation", "robustness"],
        current: "paper",
      };
    case "Monitoring":
      return {
        completed: [
          "research",
          "experiment",
          "validation",
          "robustness",
          "paper",
        ],
        current: "decision",
      };
    case "Archived":
      return {
        completed: [...LIBRARY_LIFECYCLE_STAGES],
        current: null,
      };
    default:
      return { completed: [], current: "research" };
  }
}

/** Most recently updated research — never invents a project. */
export function selectContinueResearch(
  items: ResearchListItem[]
): ResearchListItem | null {
  if (items.length === 0) return null;
  return [...items].sort((a, b) => {
    const aTime = Date.parse(a.updatedAt);
    const bTime = Date.parse(b.updatedAt);
    const aValid = Number.isFinite(aTime);
    const bValid = Number.isFinite(bTime);
    if (aValid && bValid) return bTime - aTime;
    if (aValid) return -1;
    if (bValid) return 1;
    return a.name.localeCompare(b.name);
  })[0];
}

/**
 * Recent activity for a research id — reuses catalog timeline when present.
 * Returns [] when no real activity exists (do not invent logs).
 */
export function getLibraryRecentActivity(
  researchId: string | null
): ResearchTimelineEvent[] {
  if (!researchId) return [];
  return getMockTimelineEvents(researchId);
}

export function libraryStageLabel(
  stage: LibraryLifecycleStageId,
  labels: Record<LibraryLifecycleStageId, string>
): string {
  return labels[stage];
}

/** Current spine stage label for cards — falls back to Research. */
export function getCurrentLibraryStage(
  status: ResearchLifecycleStatus
): LibraryLifecycleStageId {
  return getLibraryLifecycleProgress(status).current ?? "archive";
}
