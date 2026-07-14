"use client";

import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import ErrorAlert from "@/components/ui/ErrorAlert";
import LoadingState from "@/components/ui/LoadingState";
import type { Language } from "@/lib/i18n";
import {
  loadMockExperiments,
  MockExperimentError,
} from "@/lib/mockExperimentCatalog";
import {
  countActiveExperiments,
  createLocalExperiment,
  createNotebookEntryFromExperiment,
  createTimelineEventFromExperiment,
  filterAndSortExperiments,
  hasExperimentComposerErrors,
  validateExperimentComposer,
} from "@/lib/researchExperiments";
import type { ResearchDetail } from "@/types/research";
import type { NotebookEntry, ResearchTimelineEvent } from "@/types/notebook";
import {
  DEFAULT_EXPERIMENT_FILTERS,
  EMPTY_EXPERIMENT_COMPOSER,
  type ExperimentFilters,
  type ResearchExperiment,
} from "@/types/experiment";
import ResearchWorkspaceSkeleton from "../ResearchWorkspaceSkeleton";
import ExperimentCard from "./ExperimentCard";
import ExperimentComposer from "./ExperimentComposer";
import ExperimentDetail, {
  type ExperimentDetailLabels,
} from "./ExperimentDetail";
import ExperimentEmptyState from "./ExperimentEmptyState";
import ExperimentFiltersBar from "./ExperimentFilters";

export type ResearchExperimentsLabels = {
  title: string;
  totalCount: string;
  activeCount: string;
  newExperiment: string;
  loading: string;
  errorTitle: string;
  retry: string;
  emptyTitle: string;
  emptyDescription: string;
  filterEmptyTitle: string;
  filterEmptyDescription: string;
  notFoundTitle: string;
  notFoundDescription: string;
  backToList: string;
  filters: {
    search: string;
    searchPlaceholder: string;
    status: string;
    type: string;
    sort: string;
    all: string;
    sortUpdated: string;
    sortCreated: string;
    sortResult: string;
  };
  card: {
    hypothesis: string;
    dataset: string;
    window: string;
    benchmark: string;
    owner: string;
    updated: string;
    result: string;
    readiness: string;
    parameters: string;
    linkedNotes: string;
    openDetail: string;
    sharpe: string;
    maxDrawdown: string;
  };
  composer: {
    title: string;
    name: string;
    hypothesis: string;
    experimentType: string;
    dataset: string;
    startDate: string;
    endDate: string;
    benchmark: string;
    parameters: string;
    parametersHint: string;
    successCriteria: string;
    falsification: string;
    notes: string;
    save: string;
    cancel: string;
    nameRequired: string;
    hypothesisRequired: string;
    typeRequired: string;
    datasetRequired: string;
    startRequired: string;
    endRequired: string;
    dateRangeInvalid: string;
    successRequired: string;
    falsificationRequired: string;
  };
  detail: ExperimentDetailLabels;
};

type LoadStatus = "loading" | "ready" | "error";

export type ResearchExperimentsProps = {
  research: ResearchDetail;
  language: Language;
  labels: ResearchExperimentsLabels;
  sessionExperiments: ResearchExperiment[];
  selectedExperimentId: string | null;
  onSelectExperiment: (id: string | null) => void;
  onExperimentDesigned: (payload: {
    experiment: ResearchExperiment;
    notebookEntry: NotebookEntry;
    timelineEvent: ResearchTimelineEvent;
  }) => void;
  executedExperiments?: ResearchExperiment[] | null;
  provenanceSlot?: React.ReactNode;
};

/**
 * Research Experiments 主视图（PR-005）。
 * TODO(backend): Experiment 变更经 Application 用例；禁止 UI 执行引擎。
 */
export default function ResearchExperiments({
  research,
  language,
  labels,
  sessionExperiments,
  selectedExperimentId,
  onSelectExperiment,
  onExperimentDesigned,
  executedExperiments = null,
  provenanceSlot = null,
}: ResearchExperimentsProps) {
  const [baseline, setBaseline] = useState<ResearchExperiment[]>([]);
  const [loadStatus, setLoadStatus] = useState<LoadStatus>("loading");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);
  const [filters, setFilters] = useState<ExperimentFilters>(DEFAULT_EXPERIMENT_FILTERS);
  const [composerOpen, setComposerOpen] = useState(false);
  const [composerValues, setComposerValues] = useState(EMPTY_EXPERIMENT_COMPOSER);
  const [composerErrors, setComposerErrors] = useState<
    ReturnType<typeof validateExperimentComposer>
  >({});

  const loadList = useCallback(async () => {
    setLoadStatus("loading");
    setLoadError(null);
    try {
      const data = await loadMockExperiments(research.id);
      setBaseline(data);
      setLoadStatus("ready");
    } catch (error) {
      const message =
        error instanceof MockExperimentError
          ? error.message
          : "The experiments list could not be loaded.";
      setLoadError(message);
      setLoadStatus("error");
    }
  }, [research.id]);

  useEffect(() => {
    void loadList();
  }, [loadList, reloadToken]);

  const allExperiments = useMemo(() => {
    const catalog = executedExperiments ?? baseline;
    return [...sessionExperiments, ...catalog];
  }, [sessionExperiments, baseline, executedExperiments]);

  const visible = useMemo(
    () => filterAndSortExperiments(allExperiments, filters),
    [allExperiments, filters]
  );

  const selected = useMemo(() => {
    if (!selectedExperimentId) {
      return null;
    }
    return (
      allExperiments.find((item) => item.id === selectedExperimentId) ?? null
    );
  }, [allExperiments, selectedExperimentId]);

  const activeCount = countActiveExperiments(allExperiments);

  function openComposer() {
    setComposerValues(EMPTY_EXPERIMENT_COMPOSER);
    setComposerErrors({});
    setComposerOpen(true);
    onSelectExperiment(null);
  }

  function handleSave() {
    const errors = validateExperimentComposer(composerValues, {
      nameRequired: labels.composer.nameRequired,
      hypothesisRequired: labels.composer.hypothesisRequired,
      typeRequired: labels.composer.typeRequired,
      datasetRequired: labels.composer.datasetRequired,
      startRequired: labels.composer.startRequired,
      endRequired: labels.composer.endRequired,
      dateRangeInvalid: labels.composer.dateRangeInvalid,
      successRequired: labels.composer.successRequired,
      falsificationRequired: labels.composer.falsificationRequired,
    });
    setComposerErrors(errors);
    if (hasExperimentComposerErrors(errors)) {
      return;
    }

    const experiment = createLocalExperiment({
      researchId: research.id,
      owner: research.owner,
      values: composerValues,
    });
    const notebookEntry = createNotebookEntryFromExperiment(experiment);
    const timelineEvent = createTimelineEventFromExperiment(experiment);

    onExperimentDesigned({ experiment, notebookEntry, timelineEvent });
    setComposerOpen(false);
    setComposerValues(EMPTY_EXPERIMENT_COMPOSER);
    setComposerErrors({});
    onSelectExperiment(experiment.id);
  }

  const isFilterEmpty =
    loadStatus === "ready" && allExperiments.length > 0 && visible.length === 0;
  const isCatalogEmpty = loadStatus === "ready" && allExperiments.length === 0;
  const isDetailMissing =
    loadStatus === "ready" &&
    selectedExperimentId !== null &&
    selected === null;

  return (
    <section className="research-experiments" aria-label={labels.title}>
      <header className="research-experiments__header">
        <div>
          <h2 className="research-experiments__title">{labels.title}</h2>
          <p className="research-experiments__subtitle">{research.name}</p>
          <p className="section-meta">
            {allExperiments.length} {labels.totalCount}
            {" · "}
            {activeCount} {labels.activeCount}
          </p>
        </div>
        <Button primary onClick={openComposer} disabled={loadStatus === "loading"}>
          {labels.newExperiment}
        </Button>
      </header>

      {provenanceSlot}

      <ExperimentFiltersBar
        filters={filters}
        labels={labels.filters}
        onChange={setFilters}
        disabled={loadStatus !== "ready"}
      />

      <ExperimentComposer
        open={composerOpen}
        values={composerValues}
        errors={composerErrors}
        labels={labels.composer}
        onChange={setComposerValues}
        onSave={handleSave}
        onCancel={() => setComposerOpen(false)}
      />

      {isDetailMissing ? (
        <EmptyState
          title={labels.notFoundTitle}
          description={labels.notFoundDescription}
          action={
            <Button onClick={() => onSelectExperiment(null)}>
              {labels.backToList}
            </Button>
          }
        />
      ) : null}

      {selected ? (
        <ExperimentDetail
          experiment={selected}
          language={language}
          labels={labels.detail}
          onClose={() => onSelectExperiment(null)}
        />
      ) : null}

      <div className="research-experiments__body" aria-live="polite">
        {loadStatus === "loading" ? (
          <div>
            <LoadingState message={labels.loading} />
            <ResearchWorkspaceSkeleton />
          </div>
        ) : null}

        {loadStatus === "error" && loadError ? (
          <div className="research-experiments__error">
            <ErrorAlert title={labels.errorTitle} message={loadError} />
            <Button primary onClick={() => setReloadToken((token) => token + 1)}>
              {labels.retry}
            </Button>
          </div>
        ) : null}

        {loadStatus === "ready" && !selected ? (
          <>
            {isCatalogEmpty ? (
              <ExperimentEmptyState
                title={labels.emptyTitle}
                description={labels.emptyDescription}
                actionLabel={labels.newExperiment}
                onAction={openComposer}
              />
            ) : null}
            {isFilterEmpty ? (
              <ExperimentEmptyState
                title={labels.filterEmptyTitle}
                description={labels.filterEmptyDescription}
                variant="filter"
              />
            ) : null}
            {visible.length > 0 ? (
              <div className="research-experiments__list">
                {visible.map((experiment) => (
                  <ExperimentCard
                    key={experiment.id}
                    experiment={experiment}
                    language={language}
                    labels={labels.card}
                    selected={experiment.id === selectedExperimentId}
                    onSelect={onSelectExperiment}
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
