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

/** Homepage operating spine (4 stages) — projection of the fuller library lifecycle. */
export type OverviewWorkflowStageId =
  | "research"
  | "validation"
  | "risk_review"
  | "deployment";

export const OVERVIEW_WORKFLOW_STAGES: readonly OverviewWorkflowStageId[] = [
  "research",
  "validation",
  "risk_review",
  "deployment",
] as const;

export type OverviewWorkflowProgress = {
  completed: OverviewWorkflowStageId[];
  current: OverviewWorkflowStageId | null;
};

function libraryStageToOverview(
  stage: LibraryLifecycleStageId
): OverviewWorkflowStageId | null {
  switch (stage) {
    case "research":
    case "experiment":
      return "research";
    case "validation":
      return "validation";
    case "robustness":
      return "risk_review";
    case "paper":
    case "decision":
      return "deployment";
    case "archive":
      return null;
    default:
      return "research";
  }
}

/** Map operational status onto the 4-stage homepage workflow. */
export function getOverviewWorkflowProgress(
  status: ResearchLifecycleStatus
): OverviewWorkflowProgress {
  const full = getLibraryLifecycleProgress(status);
  if (status === "Archived") {
    return { completed: [...OVERVIEW_WORKFLOW_STAGES], current: null };
  }
  const completedSet = new Set<OverviewWorkflowStageId>();
  for (const stage of full.completed) {
    const mapped = libraryStageToOverview(stage);
    if (mapped) completedSet.add(mapped);
  }
  const current = full.current ? libraryStageToOverview(full.current) : null;
  // Do not mark the current overview stage as completed.
  if (current) completedSet.delete(current);
  return {
    completed: OVERVIEW_WORKFLOW_STAGES.filter((s) => completedSet.has(s)),
    current,
  };
}

/** Workspace tab target for a homepage workflow stage. */
export function overviewWorkflowTab(
  stage: OverviewWorkflowStageId
): "overview" | "validation" | "robustness" | "paper" {
  switch (stage) {
    case "research":
      return "overview";
    case "validation":
      return "validation";
    case "risk_review":
      return "robustness";
    case "deployment":
      return "paper";
  }
}

/** Progress 0–1 across the non-archive spine (for library cards). */
export function getLibraryProgressRatio(status: ResearchLifecycleStatus): number {
  if (status === "Archived") return 1;
  const progress = getLibraryLifecycleProgress(status);
  const spine = LIBRARY_LIFECYCLE_STAGES.filter((s) => s !== "archive");
  const done = progress.completed.filter((s) => s !== "archive").length;
  return Math.min(1, Math.max(0, done / spine.length));
}

export type WorkspaceOverviewStats = {
  active: number;
  inReview: number;
  paperTrading: number;
  experiments: number;
};

/** Live counts from existing research only — never invents projects. */
export function getWorkspaceOverviewStats(
  items: ResearchListItem[]
): WorkspaceOverviewStats {
  return {
    active: items.length,
    inReview: items.filter((item) =>
      item.status === "Review" || item.status === "Validated"
    ).length,
    paperTrading: items.filter((item) => item.status === "Paper Trading").length,
    experiments: items.reduce((sum, item) => sum + (item.experimentCount || 0), 0),
  };
}

/**
 * Merge catalog timelines for several research ids, newest first.
 * Returns [] when no real activity exists.
 */
export function getLibraryRecentActivityForResearchIds(
  researchIds: readonly string[]
): ResearchTimelineEvent[] {
  const events = researchIds.flatMap((id) => getLibraryRecentActivity(id));
  return [...events].sort((a, b) => {
    const aTime = Date.parse(a.occurredAt);
    const bTime = Date.parse(b.occurredAt);
    const aValid = Number.isFinite(aTime);
    const bValid = Number.isFinite(bTime);
    if (aValid && bValid) return bTime - aTime;
    if (aValid) return -1;
    if (bValid) return 1;
    return a.id.localeCompare(b.id);
  });
}
