"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import ErrorAlert from "@/components/ui/ErrorAlert";
import LoadingState from "@/components/ui/LoadingState";
import type { Language } from "@/lib/i18n";
import {
  loadMockValidationPipeline,
  MockValidationError,
} from "@/lib/mockValidationCatalog";
import {
  buildValidationOverview,
  filterValidationStages,
  getValidationStageById,
} from "@/lib/researchValidation";
import type { ResearchDetail } from "@/types/research";
import type { ValidationPipelineSnapshot } from "@/types/validation";
import {
  DEFAULT_VALIDATION_FILTERS,
  type ValidationFilters,
} from "@/types/validation";
import ResearchWorkspaceSkeleton from "../ResearchWorkspaceSkeleton";
import ValidationBlockers, {
  type ValidationBlockersLabels,
} from "./ValidationBlockers";
import ValidationDetail, {
  type ValidationDetailLabels,
} from "./ValidationDetail";
import ValidationEmptyState from "./ValidationEmptyState";
import ValidationFiltersBar, {
  type ValidationFiltersLabels,
} from "./ValidationFilters";
import ValidationOverview, {
  type ValidationOverviewLabels,
} from "./ValidationOverview";
import ValidationPipeline, {
  type ValidationPipelineLabels,
} from "./ValidationPipeline";

export type ResearchValidationLabels = {
  title: string;
  stageCount: string;
  loading: string;
  errorTitle: string;
  retry: string;
  emptyTitle: string;
  emptyDescription: string;
  filterEmptyTitle: string;
  filterEmptyDescription: string;
  notFoundTitle: string;
  notFoundDescription: string;
  backToPipeline: string;
  runValidation: string;
  runValidationHint: string;
  demoLoading: string;
  overview: ValidationOverviewLabels;
  blockers: ValidationBlockersLabels;
  filters: ValidationFiltersLabels;
  pipeline: ValidationPipelineLabels;
  detail: ValidationDetailLabels;
};

type LoadStatus = "loading" | "ready" | "error";

export type ResearchValidationProps = {
  research: ResearchDetail;
  language: Language;
  labels: ResearchValidationLabels;
  selectedStageId: string | null;
  onSelectStage: (id: string | null) => void;
};

/**
 * Research Validation Pipeline 主视图（PR-006）。
 * TODO(backend): ValidationRun 经 Application 用例；闸口由确定性引擎产出。
 * TODO(engine): Run Validation 为受治理工作流，UI 不得直接执行计算。
 */
export default function ResearchValidation({
  research,
  language,
  labels,
  selectedStageId,
  onSelectStage,
}: ResearchValidationProps) {
  const [snapshot, setSnapshot] = useState<ValidationPipelineSnapshot | null>(
    null
  );
  const [loadStatus, setLoadStatus] = useState<LoadStatus>("loading");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);
  const [filters, setFilters] = useState<ValidationFilters>(
    DEFAULT_VALIDATION_FILTERS
  );
  const [forceLoading, setForceLoading] = useState(false);

  const loadPipeline = useCallback(async () => {
    setLoadStatus("loading");
    setLoadError(null);
    try {
      const data = await loadMockValidationPipeline(research.id, {
        delayMs: forceLoading ? 1200 : 360,
      });
      setSnapshot(data);
      setLoadStatus("ready");
    } catch (error) {
      const message =
        error instanceof MockValidationError
          ? error.message
          : "The validation pipeline could not be loaded.";
      setLoadError(message);
      setLoadStatus("error");
    }
  }, [research.id, forceLoading]);

  useEffect(() => {
    void loadPipeline();
  }, [loadPipeline, reloadToken]);

  const stages = snapshot?.stages ?? [];
  const blockers = snapshot?.blockers ?? [];

  const overview = useMemo(
    () =>
      snapshot
        ? buildValidationOverview(snapshot)
        : null,
    [snapshot]
  );

  const visible = useMemo(
    () => filterValidationStages(stages, filters),
    [stages, filters]
  );

  const selected = useMemo(() => {
    if (!selectedStageId) {
      return null;
    }
    return getValidationStageById(stages, selectedStageId);
  }, [stages, selectedStageId]);

  const isFilterEmpty =
    loadStatus === "ready" && stages.length > 0 && visible.length === 0;
  const isCatalogEmpty = loadStatus === "ready" && stages.length === 0;
  const isDetailMissing =
    loadStatus === "ready" &&
    selectedStageId !== null &&
    selected === null;

  return (
    <section className="research-validation" aria-label={labels.title}>
      <header className="research-validation__header">
        <div>
          <h2 className="research-validation__title">{labels.title}</h2>
          <p className="research-validation__subtitle">{research.name}</p>
          <p className="section-meta">
            {stages.length} {labels.stageCount}
          </p>
        </div>
        <div className="research-validation__actions">
          <label className="research-validation__demo-toggle">
            <input
              type="checkbox"
              checked={forceLoading}
              onChange={(event) => {
                setForceLoading(event.target.checked);
                setReloadToken((token) => token + 1);
              }}
            />
            {labels.demoLoading}
          </label>
          <Button primary disabled title={labels.runValidationHint}>
            {labels.runValidation}
          </Button>
        </div>
      </header>

      <ValidationFiltersBar
        filters={filters}
        labels={labels.filters}
        onChange={setFilters}
        disabled={loadStatus !== "ready"}
      />

      {isDetailMissing ? (
        <EmptyState
          title={labels.notFoundTitle}
          description={labels.notFoundDescription}
          action={
            <Button onClick={() => onSelectStage(null)}>
              {labels.backToPipeline}
            </Button>
          }
        />
      ) : null}

      {selected ? (
        <ValidationDetail
          stage={selected}
          language={language}
          labels={labels.detail}
          onClose={() => onSelectStage(null)}
        />
      ) : null}

      <div className="research-validation__body" aria-live="polite">
        {loadStatus === "loading" ? (
          <div>
            <LoadingState message={labels.loading} />
            <ResearchWorkspaceSkeleton />
          </div>
        ) : null}

        {loadStatus === "error" && loadError ? (
          <div className="research-validation__error">
            <ErrorAlert title={labels.errorTitle} message={loadError} />
            <Button primary onClick={() => setReloadToken((token) => token + 1)}>
              {labels.retry}
            </Button>
          </div>
        ) : null}

        {loadStatus === "ready" && overview && !selected ? (
          <>
            <ValidationOverview
              stats={overview}
              language={language}
              labels={labels.overview}
            />

            <ValidationBlockers
              blockers={blockers}
              labels={labels.blockers}
              onInspectStage={onSelectStage}
            />

            {isCatalogEmpty ? (
              <ValidationEmptyState
                title={labels.emptyTitle}
                description={labels.emptyDescription}
              />
            ) : null}

            {isFilterEmpty ? (
              <ValidationEmptyState
                title={labels.filterEmptyTitle}
                description={labels.filterEmptyDescription}
                variant="filter"
              />
            ) : null}

            {visible.length > 0 ? (
              <ValidationPipeline
                stages={visible}
                language={language}
                labels={labels.pipeline}
                selectedStageId={selectedStageId}
                onSelectStage={onSelectStage}
              />
            ) : null}
          </>
        ) : null}
      </div>
    </section>
  );
}
