/** Research Notebook 领域投影类型（前端 mock；后端接入后对齐 API）。 */

export const NOTEBOOK_ENTRY_TYPES = [
  "Observation",
  "Hypothesis",
  "Decision",
  "Action",
  "Result",
  "Reflection",
] as const;

export type NotebookEntryType = (typeof NOTEBOOK_ENTRY_TYPES)[number];

export type RelatedArtifactKind = "experiment" | "validation" | "evidence";

export type NotebookRelatedArtifact = {
  id: string;
  label: string;
  kind: RelatedArtifactKind;
};

export type NotebookEntry = {
  id: string;
  researchId: string;
  entryType: NotebookEntryType;
  title: string;
  body: string;
  author: string;
  createdAt: string;
  updatedAt?: string;
  edited?: boolean;
  tags: string[];
  relatedArtifact?: NotebookRelatedArtifact;
};

export type NotebookTypeFilter = NotebookEntryType | "all";

export type NotebookSort = "newest" | "oldest";

export type NotebookFilters = {
  type: NotebookTypeFilter;
  sort: NotebookSort;
};

export const DEFAULT_NOTEBOOK_FILTERS: NotebookFilters = {
  type: "all",
  sort: "newest",
};

/** 轻量本地时间线事件（PR-004 session 边界；非全局事件总线）。 */
export type ResearchTimelineEventKind =
  | "notebook_entry"
  | "stage_change"
  | "validation"
  | "experiment";

export type ResearchTimelineEvent = {
  id: string;
  researchId: string;
  occurredAt: string;
  title: string;
  summary: string;
  kind: ResearchTimelineEventKind;
  /** 关联 notebook entry（若由条目创建触发） */
  sourceEntryId?: string;
};

export type NotebookComposerValues = {
  entryType: NotebookEntryType | "";
  title: string;
  body: string;
  tags: string;
  relatedArtifactId: string;
};

export const EMPTY_NOTEBOOK_COMPOSER: NotebookComposerValues = {
  entryType: "",
  title: "",
  body: "",
  tags: "",
  relatedArtifactId: "",
};
