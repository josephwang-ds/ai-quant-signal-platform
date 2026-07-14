/**
 * Design notes + product timeline for the canonical MA Crossover research.
 */

import {
  CANONICAL_RESEARCH_ID,
  getCanonicalResearchPackage,
} from "@/lib/canonicalMaCrossover";
import type { NotebookEntry, ResearchTimelineEvent } from "@/types/notebook";

function buildNotebook(): NotebookEntry[] {
  const pkg = getCanonicalResearchPackage();
  const documentedAt =
    pkg.timelineEvents[0]?.occurredAt ?? "2026-07-14T04:00:00.000Z";
  return pkg.designNotes.map((note) => ({
    id: note.id,
    researchId: CANONICAL_RESEARCH_ID,
    entryType: note.entryType,
    title: note.title,
    body: note.body,
    author: pkg.definition.ownerLabel,
    createdAt: documentedAt,
    tags: [...note.tags, "research-design-notes"],
  }));
}

function buildTimeline(): ResearchTimelineEvent[] {
  const pkg = getCanonicalResearchPackage();
  return pkg.timelineEvents.map((event) => ({
    id: event.id,
    researchId: CANONICAL_RESEARCH_ID,
    occurredAt: event.occurredAt,
    title: event.title,
    summary: event.summary,
    kind: event.kind,
  }));
}

export const MOCK_NOTEBOOK_BY_RESEARCH: Record<string, NotebookEntry[]> = {
  [CANONICAL_RESEARCH_ID]: buildNotebook(),
};

export const MOCK_TIMELINE_BY_RESEARCH: Record<string, ResearchTimelineEvent[]> = {
  [CANONICAL_RESEARCH_ID]: buildTimeline(),
};

export function getMockNotebookEntries(researchId: string): NotebookEntry[] {
  const entries = MOCK_NOTEBOOK_BY_RESEARCH[researchId] ?? [];
  return entries.map((entry) => ({
    ...entry,
    tags: [...entry.tags],
    relatedArtifact: entry.relatedArtifact
      ? { ...entry.relatedArtifact }
      : undefined,
  }));
}

export function getMockTimelineEvents(researchId: string): ResearchTimelineEvent[] {
  return (MOCK_TIMELINE_BY_RESEARCH[researchId] ?? []).map((event) => ({ ...event }));
}

export class MockNotebookError extends Error {
  constructor(message = "Unable to load the research notebook.") {
    super(message);
    this.name = "MockNotebookError";
  }
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

function shouldForceMockError(): boolean {
  if (typeof window === "undefined") {
    return false;
  }
  return new URLSearchParams(window.location.search).get("mockError") === "1";
}

export async function loadMockNotebookEntries(
  researchId: string,
  options?: { delayMs?: number }
): Promise<NotebookEntry[]> {
  await delay(options?.delayMs ?? 320);
  if (shouldForceMockError()) {
    throw new MockNotebookError(
      "Mock notebook load failed. Remove mockError=1 from the URL or retry."
    );
  }
  return getMockNotebookEntries(researchId);
}
