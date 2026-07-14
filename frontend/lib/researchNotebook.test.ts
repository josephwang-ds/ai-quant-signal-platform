import { describe, expect, it } from "vitest";
import { getMockNotebookEntries } from "@/lib/mockNotebookCatalog";
import { CANONICAL_RESEARCH_ID } from "@/lib/mockResearchCatalog";
import {
  createLocalNotebookEntry,
  createTimelineEventFromNotebookEntry,
  filterAndSortNotebookEntries,
  hasNotebookComposerErrors,
  mergeTimelineEvents,
  validateNotebookComposer,
} from "@/lib/researchNotebook";
import { renderNotebookMarkdown } from "@/lib/notebookMarkdown";
import { DEFAULT_NOTEBOOK_FILTERS } from "@/types/notebook";

describe("notebook catalog", () => {
  it("provides coherent MA crossover notebook entries", () => {
    const entries = getMockNotebookEntries(CANONICAL_RESEARCH_ID);
    expect(entries.length).toBeGreaterThanOrEqual(5);
    expect(entries.some((e) => e.entryType === "Hypothesis")).toBe(true);
    expect(entries.some((e) => e.entryType === "Decision")).toBe(true);
    expect(entries.every((e) => e.researchId === CANONICAL_RESEARCH_ID)).toBe(
      true
    );
    expect(
      entries.some((e) =>
        e.body.includes("Research Execution Engine")
      )
    ).toBe(true);
  });

  it("returns empty for non-canonical research ids", () => {
    expect(getMockNotebookEntries("rs-rsi-002")).toEqual([]);
  });
});

describe("filterAndSortNotebookEntries", () => {
  const entries = getMockNotebookEntries(CANONICAL_RESEARCH_ID);

  it("filters by entry type", () => {
    const filtered = filterAndSortNotebookEntries(entries, {
      ...DEFAULT_NOTEBOOK_FILTERS,
      type: "Action",
    });
    expect(filtered.length).toBeGreaterThan(0);
    expect(filtered.every((e) => e.entryType === "Action")).toBe(true);
  });

  it("sorts newest first by default", () => {
    const sorted = filterAndSortNotebookEntries(entries, DEFAULT_NOTEBOOK_FILTERS);
    expect(Date.parse(sorted[0].createdAt)).toBeGreaterThanOrEqual(
      Date.parse(sorted[sorted.length - 1].createdAt)
    );
  });

  it("sorts oldest first when requested", () => {
    const sorted = filterAndSortNotebookEntries(entries, {
      ...DEFAULT_NOTEBOOK_FILTERS,
      sort: "oldest",
    });
    expect(Date.parse(sorted[0].createdAt)).toBeLessThanOrEqual(
      Date.parse(sorted[sorted.length - 1].createdAt)
    );
  });
});

describe("validateNotebookComposer", () => {
  const messages = {
    entryTypeRequired: "Type required",
    titleRequired: "Title required",
    bodyRequired: "Body required",
  };

  it("requires type, title, and body", () => {
    const errors = validateNotebookComposer(
      { entryType: "", title: "", body: "", tags: "", relatedArtifactId: "" },
      messages
    );
    expect(hasNotebookComposerErrors(errors)).toBe(true);
    expect(errors.entryType).toBeDefined();
    expect(errors.title).toBeDefined();
    expect(errors.body).toBeDefined();
  });

  it("passes when required fields are present", () => {
    const errors = validateNotebookComposer(
      {
        entryType: "Observation",
        title: "Note",
        body: "Body text",
        tags: "",
        relatedArtifactId: "",
      },
      messages
    );
    expect(hasNotebookComposerErrors(errors)).toBe(false);
  });
});

describe("local notebook + timeline integration", () => {
  it("creates a timeline event when a notebook entry is saved locally", () => {
    const entry = createLocalNotebookEntry({
      researchId: CANONICAL_RESEARCH_ID,
      author: "Research Desk",
      entryType: "Observation",
      title: "Session note",
      body: "Local session entry.",
      tags: ["session"],
      now: "2026-07-13T12:00:00.000Z",
    });
    const event = createTimelineEventFromNotebookEntry(entry);
    expect(event.kind).toBe("notebook_entry");
    expect(event.sourceEntryId).toBe(entry.id);
    expect(event.researchId).toBe(CANONICAL_RESEARCH_ID);
  });

  it("merges baseline and session timeline events newest-first", () => {
    const merged = mergeTimelineEvents(
      [
        {
          id: "tl-1",
          researchId: CANONICAL_RESEARCH_ID,
          occurredAt: "2026-01-01T00:00:00.000Z",
          title: "Older",
          summary: "older",
          kind: "stage_change",
        },
      ],
      [
        {
          id: "tl-2",
          researchId: CANONICAL_RESEARCH_ID,
          occurredAt: "2026-07-13T12:00:00.000Z",
          title: "Newer",
          summary: "newer",
          kind: "notebook_entry",
        },
      ]
    );
    expect(merged[0].id).toBe("tl-2");
    expect(merged[1].id).toBe("tl-1");
  });
});

describe("notebook markdown", () => {
  it("renders bold markdown safely", () => {
    const html = renderNotebookMarkdown("Hello **world**");
    expect(html).toContain("<strong>");
    expect(html).toContain("world");
  });
});
