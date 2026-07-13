"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Button from "@/components/ui/Button";
import ErrorAlert from "@/components/ui/ErrorAlert";
import LoadingState from "@/components/ui/LoadingState";
import type { Language } from "@/lib/i18n";
import {
  loadMockNotebookEntries,
  MockNotebookError,
} from "@/lib/mockNotebookCatalog";
import {
  createLocalNotebookEntry,
  createTimelineEventFromNotebookEntry,
  filterAndSortNotebookEntries,
  getNotebookLastUpdated,
  hasNotebookComposerErrors,
  parseTagsInput,
  validateNotebookComposer,
} from "@/lib/researchNotebook";
import type { ResearchDetail } from "@/types/research";
import {
  DEFAULT_NOTEBOOK_FILTERS,
  EMPTY_NOTEBOOK_COMPOSER,
  type NotebookEntry,
  type NotebookFilters,
  type ResearchTimelineEvent,
} from "@/types/notebook";
import NotebookEmptyState from "./NotebookEmptyState";
import NotebookEntryCard from "./NotebookEntryCard";
import NotebookEntryComposer from "./NotebookEntryComposer";
import NotebookFiltersBar from "./NotebookFilters";
import ResearchWorkspaceSkeleton from "../ResearchWorkspaceSkeleton";

function formatDateTime(value: string, language: Language): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString(language === "zh" ? "zh-CN" : "en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export type ResearchNotebookLabels = {
  title: string;
  entryCount: string;
  lastUpdated: string;
  newEntry: string;
  loading: string;
  errorTitle: string;
  retry: string;
  emptyTitle: string;
  emptyDescription: string;
  filterEmptyTitle: string;
  filterEmptyDescription: string;
  filters: {
    filterType: string;
    filterAll: string;
    sort: string;
    sortNewest: string;
    sortOldest: string;
  };
  card: {
    author: string;
    created: string;
    edited: string;
    related: string;
    tags: string;
  };
  composer: {
    title: string;
    entryType: string;
    entryTitle: string;
    content: string;
    tags: string;
    tagsHint: string;
    relatedArtifact: string;
    relatedNone: string;
    save: string;
    cancel: string;
    entryTypeRequired: string;
    titleRequired: string;
    bodyRequired: string;
  };
};

type LoadStatus = "loading" | "ready" | "error";

export type ResearchNotebookProps = {
  research: ResearchDetail;
  language: Language;
  labels: ResearchNotebookLabels;
  sessionEntries: NotebookEntry[];
  onSessionEntrySaved: (entry: NotebookEntry, timelineEvent: ResearchTimelineEvent) => void;
};

/**
 * Research Notebook 主视图（PR-004）。
 * TODO(backend): NotebookEntry 变更通过 Application 用例持久化。
 */
export default function ResearchNotebook({
  research,
  language,
  labels,
  sessionEntries,
  onSessionEntrySaved,
}: ResearchNotebookProps) {
  const [baselineEntries, setBaselineEntries] = useState<NotebookEntry[]>([]);
  const [loadStatus, setLoadStatus] = useState<LoadStatus>("loading");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);
  const [filters, setFilters] = useState<NotebookFilters>(DEFAULT_NOTEBOOK_FILTERS);
  const [composerOpen, setComposerOpen] = useState(false);
  const [composerValues, setComposerValues] = useState(EMPTY_NOTEBOOK_COMPOSER);
  const [composerErrors, setComposerErrors] = useState<
    ReturnType<typeof validateNotebookComposer>
  >({});

  const loadEntries = useCallback(async () => {
    setLoadStatus("loading");
    setLoadError(null);
    try {
      const data = await loadMockNotebookEntries(research.id);
      setBaselineEntries(data);
      setLoadStatus("ready");
    } catch (error) {
      const message =
        error instanceof MockNotebookError
          ? error.message
          : "The research notebook could not be loaded.";
      setLoadError(message);
      setLoadStatus("error");
    }
  }, [research.id]);

  useEffect(() => {
    void loadEntries();
  }, [loadEntries, reloadToken]);

  const allEntries = useMemo(
    () => [...baselineEntries, ...sessionEntries],
    [baselineEntries, sessionEntries]
  );

  const visibleEntries = useMemo(
    () => filterAndSortNotebookEntries(allEntries, filters),
    [allEntries, filters]
  );

  const lastUpdated = getNotebookLastUpdated(allEntries);

  const artifactOptions = useMemo(
    () =>
      research.evidenceItems.map((item) => ({
        id: item.id,
        label: `${item.label} (${item.status})`,
      })),
    [research.evidenceItems]
  );

  function openComposer() {
    setComposerValues(EMPTY_NOTEBOOK_COMPOSER);
    setComposerErrors({});
    setComposerOpen(true);
  }

  function handleSaveEntry() {
    const errors = validateNotebookComposer(composerValues, {
      entryTypeRequired: labels.composer.entryTypeRequired,
      titleRequired: labels.composer.titleRequired,
      bodyRequired: labels.composer.bodyRequired,
    });
    setComposerErrors(errors);
    if (hasNotebookComposerErrors(errors)) {
      return;
    }

    const related = research.evidenceItems.find(
      (item) => item.id === composerValues.relatedArtifactId
    );

    const entry = createLocalNotebookEntry({
      researchId: research.id,
      author: research.owner,
      entryType: composerValues.entryType as NotebookEntry["entryType"],
      title: composerValues.title,
      body: composerValues.body,
      tags: parseTagsInput(composerValues.tags),
      relatedArtifact: related
        ? {
            id: related.id,
            label: related.label,
            kind: "evidence",
          }
        : undefined,
    });

    const timelineEvent = createTimelineEventFromNotebookEntry(entry);
    onSessionEntrySaved(entry, timelineEvent);
    setComposerOpen(false);
    setComposerValues(EMPTY_NOTEBOOK_COMPOSER);
    setComposerErrors({});
  }

  const isFilterEmpty =
    loadStatus === "ready" && allEntries.length > 0 && visibleEntries.length === 0;
  const isCatalogEmpty = loadStatus === "ready" && allEntries.length === 0;

  return (
    <section className="research-notebook" aria-label={labels.title}>
      <header className="research-notebook__header">
        <div className="research-notebook__header-copy">
          <h2 className="research-notebook__title">{labels.title}</h2>
          <p className="research-notebook__subtitle">{research.name}</p>
          <p className="section-meta">
            {allEntries.length} {labels.entryCount}
            {lastUpdated ? (
              <>
                {" "}
                · {labels.lastUpdated} {formatDateTime(lastUpdated, language)}
              </>
            ) : null}
          </p>
        </div>
        <Button primary onClick={openComposer} disabled={loadStatus === "loading"}>
          {labels.newEntry}
        </Button>
      </header>

      <NotebookFiltersBar
        filters={filters}
        labels={labels.filters}
        onChange={setFilters}
        disabled={loadStatus !== "ready"}
      />

      <NotebookEntryComposer
        open={composerOpen}
        values={composerValues}
        errors={composerErrors}
        artifactOptions={artifactOptions}
        labels={labels.composer}
        onChange={setComposerValues}
        onSave={handleSaveEntry}
        onCancel={() => setComposerOpen(false)}
      />

      <div className="research-notebook__body" aria-live="polite">
        {loadStatus === "loading" ? (
          <div className="research-notebook__loading">
            <LoadingState message={labels.loading} />
            <ResearchWorkspaceSkeleton />
          </div>
        ) : null}

        {loadStatus === "error" && loadError ? (
          <div className="research-notebook__error">
            <ErrorAlert title={labels.errorTitle} message={loadError} />
            <Button primary onClick={() => setReloadToken((token) => token + 1)}>
              {labels.retry}
            </Button>
          </div>
        ) : null}

        {loadStatus === "ready" ? (
          <>
            {isCatalogEmpty ? (
              <NotebookEmptyState
                title={labels.emptyTitle}
                description={labels.emptyDescription}
                actionLabel={labels.newEntry}
                onAction={openComposer}
                variant="catalog"
              />
            ) : null}

            {isFilterEmpty ? (
              <NotebookEmptyState
                title={labels.filterEmptyTitle}
                description={labels.filterEmptyDescription}
                variant="filter"
              />
            ) : null}

            {visibleEntries.length > 0 ? (
              <div className="research-notebook__entries">
                {visibleEntries.map((entry) => (
                  <NotebookEntryCard
                    key={entry.id}
                    entry={entry}
                    language={language}
                    labels={labels.card}
                  />
                ))}
              </div>
            ) : null}
          </>
        ) : null}
      </div>
    </section>
  );
}
