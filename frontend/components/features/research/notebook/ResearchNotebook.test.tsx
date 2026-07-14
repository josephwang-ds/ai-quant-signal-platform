import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useState } from "react";
import ResearchNotebook from "@/components/features/research/notebook/ResearchNotebook";
import {
  CANONICAL_RESEARCH_ID,
  getMockResearchById,
} from "@/lib/mockResearchCatalog";
import type { NotebookEntry, ResearchTimelineEvent } from "@/types/notebook";

vi.mock("@/lib/mockNotebookCatalog", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/mockNotebookCatalog")>();
  return {
    ...actual,
    loadMockNotebookEntries: vi.fn(async (researchId: string) =>
      actual.getMockNotebookEntries(researchId)
    ),
  };
});

const labels = {
  title: "Research Design Notes",
  entryCount: "entries",
  lastUpdated: "Last updated",
  newEntry: "New Entry",
  loading: "Loading…",
  errorTitle: "Error",
  retry: "Retry",
  emptyTitle: "No research notes yet",
  emptyDescription: "Capture the first observation, hypothesis, or decision.",
  filterEmptyTitle: "No entries match",
  filterEmptyDescription: "Try another filter.",
  filters: {
    filterType: "Entry type",
    filterAll: "All",
    sort: "Sort",
    sortNewest: "Newest first",
    sortOldest: "Oldest first",
  },
  card: {
    author: "Author",
    created: "Created",
    edited: "Edited",
    related: "Related",
    tags: "Tags",
  },
  composer: {
    title: "New notebook entry",
    entryType: "Entry type",
    entryTitle: "Title",
    content: "Content",
    tags: "Tags",
    tagsHint: "Comma-separated",
    relatedArtifact: "Related artifact",
    relatedNone: "None",
    save: "Save Entry",
    cancel: "Cancel",
    entryTypeRequired: "Entry type is required.",
    titleRequired: "Title is required.",
    bodyRequired: "Content is required.",
  },
};

afterEach(() => {
  cleanup();
});

describe("ResearchNotebook", () => {
  const research = getMockResearchById(CANONICAL_RESEARCH_ID);
  expect(research).not.toBeNull();

  it("renders research design notes", async () => {
    render(
      <ResearchNotebook
        research={research!}
        language="en"
        labels={labels}
        sessionEntries={[]}
        onSessionEntrySaved={() => undefined}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Primary hypothesis (design)")).toBeInTheDocument();
    });
    expect(
      screen.getByRole("region", { name: "Research Design Notes" })
    ).toBeInTheDocument();
  });

  it("filters entries by type", async () => {
    const user = userEvent.setup();
    render(
      <ResearchNotebook
        research={research!}
        language="en"
        labels={labels}
        sessionEntries={[]}
        onSessionEntrySaved={() => undefined}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Primary hypothesis (design)")).toBeInTheDocument();
    });

    await user.selectOptions(screen.getByLabelText("Entry type"), "Hypothesis");
    const entries = screen.getAllByRole("article");
    expect(entries).toHaveLength(1);
  });

  it("shows validation errors when saving an empty entry", async () => {
    const user = userEvent.setup();
    render(
      <ResearchNotebook
        research={research!}
        language="en"
        labels={labels}
        sessionEntries={[]}
        onSessionEntrySaved={() => undefined}
      />
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "New Entry" })).toBeEnabled();
    });

    await user.click(screen.getByRole("button", { name: "New Entry" }));
    const composer = screen.getByRole("region", { name: "New notebook entry" });
    await user.click(within(composer).getByRole("button", { name: "Save Entry" }));
    expect(within(composer).getByText("Entry type is required.")).toBeInTheDocument();
  });

  it("adds a new entry after successful save", async () => {
    const user = userEvent.setup();

    function Harness() {
      const [sessionEntries, setSessionEntries] = useState<NotebookEntry[]>([]);
      return (
        <ResearchNotebook
          research={research!}
          language="en"
          labels={labels}
          sessionEntries={sessionEntries}
          onSessionEntrySaved={(entry, _event: ResearchTimelineEvent) => {
            setSessionEntries((prev) => [entry, ...prev]);
          }}
        />
      );
    }

    render(<Harness />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "New Entry" })).toBeEnabled();
    });

    await user.click(screen.getByRole("button", { name: "New Entry" }));
    const composer = screen.getByRole("region", { name: "New notebook entry" });
    await user.selectOptions(within(composer).getByLabelText("Entry type"), "Observation");
    await user.type(within(composer).getByLabelText("Title"), "Session observation");
    await user.type(
      within(composer).getByLabelText("Content"),
      "Saved locally in this session."
    );
    await user.click(within(composer).getByRole("button", { name: "Save Entry" }));
    expect(screen.getByText("Session observation")).toBeInTheDocument();
  });
});

describe("ResearchNotebook empty catalog", () => {
  it("shows empty state when notebook load returns no entries", async () => {
    const research = getMockResearchById(CANONICAL_RESEARCH_ID);
    expect(research).not.toBeNull();

    const { loadMockNotebookEntries } = await import("@/lib/mockNotebookCatalog");
    vi.mocked(loadMockNotebookEntries).mockResolvedValueOnce([]);

    render(
      <ResearchNotebook
        research={research!}
        language="en"
        labels={labels}
        sessionEntries={[]}
        onSessionEntrySaved={() => undefined}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("No research notes yet")).toBeInTheDocument();
    });
  });
});
