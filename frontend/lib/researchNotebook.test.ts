import { describe, expect, it } from "vitest";
import { getMockNotebookEntries } from "@/lib/mockNotebookCatalog";
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
  it("provides at least eight coherent entries for the momentum demo", () => {
    const entries = getMockNotebookEntries("rs-momentum-001");
    expect(entries.length).toBeGreaterThanOrEqual(8);
    expect(entries.some((e) => e.entryType === "Hypothesis")).toBe(true);
    expect(entries.some((e) => e.entryType === "Result")).toBe(true);
    expect(entries.some((e) => e.entryType === "Reflection")).toBe(true);
  });

  it("scopes entries to the requested research id", () => {
    const entries = getMockNotebookEntries("rs-rsi-002");
    expect(entries.every((e) => e.researchId === "rs-rsi-002")).toBe(true);
  });
});

describe("filterAndSortNotebookEntries", () => {
  const entries = getMockNotebookEntries("rs-momentum-001");

  it("filters by entry type", () => {
    const filtered = filterAndSortNotebookEntries(entries, {
      ...DEFAULT_NOTEBOOK_FILTERS,
      type: "Reflection",
    });
    expect(filtered.length).toBeGreaterThan(0);
    expect(filtered.every((e) => e.entryType === "Reflection")).toBe(true);
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
      researchId: "rs-momentum-001",
      author: "A. Chen",
      entryType: "Observation",
      title: "Session note",
      body: "Local session entry.",
      tags: ["session"],
      now: "2026-07-13T12:00:00.000Z",
    });
    const event = createTimelineEventFromNotebookEntry(entry);
    expect(event.kind).toBe("notebook_entry");
    expect(event.sourceEntryId).toBe(entry.id);
    expect(event.researchId).toBe("rs-momentum-001");
  });

  it("merges baseline and session timeline events newest-first", () => {
    const merged = mergeTimelineEvents(
      [
        {
          id: "tl-1",
          researchId: "rs-momentum-001",
          occurredAt: "2026-01-01T00:00:00.000Z",
          title: "Older",
          summary: "older",
          kind: "stage_change",
        },
      ],
      [
        {
          id: "tl-2",
          researchId: "rs-momentum-001",
          occurredAt: "2026-07-13T12:00:00.000Z",
          title: "Newer",
          summary: "newer",
          kind: "notebook_entry",
        },
      ]
    );
    expect(merged[0].title).toBe("Newer");
  });
});

describe("renderNotebookMarkdown", () => {
  it("renders headings, lists, and bold text", () => {
    const html = renderNotebookMarkdown("## Title\n\n**Bold** line\n\n- item one");
    expect(html).toContain("<h4");
    expect(html).toContain("<strong>Bold</strong>");
    expect(html).toContain("<li>item one</li>");
  });
});
