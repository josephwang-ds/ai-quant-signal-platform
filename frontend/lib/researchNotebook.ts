/**
 * Notebook 筛选、校验与本地条目构造。
 *
 * TODO(backend): 替换为 Notebook Application 用例与持久化端口。
 */

import type {
  NotebookComposerValues,
  NotebookEntry,
  NotebookEntryType,
  NotebookFilters,
  ResearchTimelineEvent,
} from "@/types/notebook";
import { NOTEBOOK_ENTRY_TYPES } from "@/types/notebook";

export function filterAndSortNotebookEntries(
  entries: NotebookEntry[],
  filters: NotebookFilters
): NotebookEntry[] {
  const filtered =
    filters.type === "all"
      ? entries
      : entries.filter((entry) => entry.entryType === filters.type);

  const sorted = [...filtered];
  sorted.sort((a, b) => {
    const aTime = Date.parse(a.createdAt);
    const bTime = Date.parse(b.createdAt);
    return filters.sort === "newest" ? bTime - aTime : aTime - bTime;
  });

  return sorted;
}

export function getNotebookLastUpdated(entries: NotebookEntry[]): string | null {
  if (entries.length === 0) {
    return null;
  }
  const latest = entries.reduce((max, entry) => {
    const candidate = entry.updatedAt ?? entry.createdAt;
    return Date.parse(candidate) > Date.parse(max) ? candidate : max;
  }, entries[0].updatedAt ?? entries[0].createdAt);
  return latest;
}

export type NotebookComposerErrors = Partial<
  Record<"entryType" | "title" | "body", string>
>;

export function validateNotebookComposer(
  values: NotebookComposerValues,
  messages: {
    entryTypeRequired: string;
    titleRequired: string;
    bodyRequired: string;
  }
): NotebookComposerErrors {
  const errors: NotebookComposerErrors = {};

  if (!values.entryType || !NOTEBOOK_ENTRY_TYPES.includes(values.entryType)) {
    errors.entryType = messages.entryTypeRequired;
  }
  if (!values.title.trim()) {
    errors.title = messages.titleRequired;
  }
  if (!values.body.trim()) {
    errors.body = messages.bodyRequired;
  }

  return errors;
}

export function hasNotebookComposerErrors(errors: NotebookComposerErrors): boolean {
  return Object.keys(errors).length > 0;
}

export function createLocalNotebookEntry(input: {
  researchId: string;
  author: string;
  entryType: NotebookEntryType;
  title: string;
  body: string;
  tags: string[];
  relatedArtifact?: NotebookEntry["relatedArtifact"];
  now?: string;
}): NotebookEntry {
  const now = input.now ?? new Date().toISOString();
  return {
    id: `nb-local-${input.researchId}-${Date.now()}`,
    researchId: input.researchId,
    entryType: input.entryType,
    title: input.title.trim(),
    body: input.body.trim(),
    author: input.author,
    createdAt: now,
    tags: input.tags,
    relatedArtifact: input.relatedArtifact,
  };
}

/**
 * 由 notebook entry 派生本地时间线事件（session-only 边界）。
 * TODO(api): POST /api/research/{id}/timeline via domain event bus.
 */
export function createTimelineEventFromNotebookEntry(
  entry: NotebookEntry
): ResearchTimelineEvent {
  return {
    id: `tl-nb-${entry.id}`,
    researchId: entry.researchId,
    occurredAt: entry.createdAt,
    title: `${entry.entryType}: ${entry.title}`,
    summary: entry.body.split("\n")[0].slice(0, 160),
    kind: "notebook_entry",
    sourceEntryId: entry.id,
  };
}

export function mergeTimelineEvents(
  baseline: ResearchTimelineEvent[],
  session: ResearchTimelineEvent[]
): ResearchTimelineEvent[] {
  const merged = [...baseline, ...session];
  merged.sort((a, b) => Date.parse(b.occurredAt) - Date.parse(a.occurredAt));
  return merged;
}

export function parseTagsInput(value: string): string[] {
  return value
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
}
