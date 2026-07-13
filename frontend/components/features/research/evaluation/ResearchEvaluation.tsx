"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Button from "@/components/ui/Button";
import ErrorAlert from "@/components/ui/ErrorAlert";
import LoadingState from "@/components/ui/LoadingState";
import type { Language } from "@/lib/i18n";
import {
  loadMockEvaluation,
  MockEvaluationError,
} from "@/lib/mockEvaluationCatalog";
import {
  buildEvaluationOverview,
  filterEvaluationDimensions,
  getEvaluationWeightsTotal,
} from "@/lib/researchEvaluation";
import type { ResearchDetail } from "@/types/research";
import type { EvaluationSnapshot } from "@/types/evaluation";
import {
  DEFAULT_EVALUATION_FILTERS,
  type EvaluationFilters,
} from "@/types/evaluation";
import ResearchWorkspaceSkeleton from "../ResearchWorkspaceSkeleton";
import ConfidenceBreakdown, {
  type ConfidenceBreakdownLabels,
} from "./ConfidenceBreakdown";
import EvaluationBlockers, {
  type EvaluationBlockersLabels,
} from "./EvaluationBlockers";
import EvaluationDimensionCard, {
  type EvaluationDimensionCardLabels,
} from "./EvaluationDimensionCard";
import EvaluationEmptyState from "./EvaluationEmptyState";
import EvaluationFiltersBar, {
  type EvaluationFiltersLabels,
} from "./EvaluationFilters";
import EvaluationHistory, {
  type EvaluationHistoryLabels,
} from "./EvaluationHistory";
import EvaluationOverview, {
  type EvaluationOverviewLabels,
} from "./EvaluationOverview";
import EvaluationRecommendationPanelView, {
  type EvaluationRecommendationLabels,
} from "./EvaluationRecommendation";
import EvaluationStrengthsWeaknesses, {
  type EvaluationStrengthsWeaknessesLabels,
} from "./EvaluationStrengthsWeaknesses";
import ReadinessRules, {
  type ReadinessRulesLabels,
} from "./ReadinessRules";

export type ResearchEvaluationLabels = {
  title: string;
  loading: string;
  errorTitle: string;
  retry: string;
  emptyTitle: string;
  emptyDescription: string;
  filterEmptyTitle: string;
  filterEmptyDescription: string;
  missingValidationTitle: string;
  missingValidationDescription: string;
  requestReview: string;
  requestReviewHint: string;
  demoLoading: string;
  demoError: string;
  dimensionsTitle: string;
  overview: EvaluationOverviewLabels;
  breakdown: ConfidenceBreakdownLabels;
  readiness: ReadinessRulesLabels;
  blockers: EvaluationBlockersLabels;
  strengthsWeaknesses: EvaluationStrengthsWeaknessesLabels;
  recommendation: EvaluationRecommendationLabels;
  history: EvaluationHistoryLabels;
  filters: EvaluationFiltersLabels;
  dimensionCard: EvaluationDimensionCardLabels;
};

type LoadStatus = "loading" | "ready" | "error";

export type ResearchEvaluationProps = {
  research: ResearchDetail;
  language: Language;
  labels: ResearchEvaluationLabels;
};

/**
 * Research Evaluation 主视图（PR-007）。
 * TODO(backend): Evaluation / Research Confidence 经 Application + 确定性引擎。
 * TODO(governance): Request Review / Publish Strategy 为受治理工作流。
 */
export default function ResearchEvaluation({
  research,
  language,
  labels,
}: ResearchEvaluationProps) {
  const [snapshot, setSnapshot] = useState<EvaluationSnapshot | null>(null);
  const [loadStatus, setLoadStatus] = useState<LoadStatus>("loading");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);
  const [filters, setFilters] = useState<EvaluationFilters>(
    DEFAULT_EVALUATION_FILTERS
  );
  const [forceLoading, setForceLoading] = useState(false);
  const [forceError, setForceError] = useState(false);
  const [expandedKeys, setExpandedKeys] = useState<Record<string, boolean>>({});

  const loadEvaluation = useCallback(async () => {
    setLoadStatus("loading");
    setLoadError(null);
    try {
      if (forceError) {
        throw new MockEvaluationError(
          "Demo error state enabled. Uncheck Demo error to reload."
        );
      }
      const data = await loadMockEvaluation(research.id, {
        delayMs: forceLoading ? 1200 : 360,
      });
      setSnapshot(data);
      setLoadStatus("ready");
    } catch (error) {
      const message =
        error instanceof MockEvaluationError
          ? error.message
          : "The evaluation could not be loaded.";
      setLoadError(message);
      setLoadStatus("error");
    }
  }, [research.id, forceLoading, forceError]);

  useEffect(() => {
    void loadEvaluation();
  }, [loadEvaluation, reloadToken]);

  const overview = useMemo(
    () => (snapshot ? buildEvaluationOverview(snapshot) : null),
    [snapshot]
  );

  const dimensions = snapshot?.dimensions ?? [];
  const visible = useMemo(
    () => filterEvaluationDimensions(dimensions, filters),
    [dimensions, filters]
  );

  const isMissingValidation =
    loadStatus === "ready" &&
    snapshot !== null &&
    (!snapshot.hasValidationData || snapshot.status === "Missing Validation");
  const isCatalogEmpty =
    loadStatus === "ready" &&
    snapshot !== null &&
    snapshot.dimensions.length === 0 &&
    snapshot.hasValidationData;
  const isFilterEmpty =
    loadStatus === "ready" &&
    dimensions.length > 0 &&
    visible.length === 0;

  function toggleDimension(key: string) {
    setExpandedKeys((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  return (
    <section className="research-evaluation" aria-label={labels.title}>
      <header className="research-evaluation__header">
        <div>
          <h2 className="research-evaluation__title">{labels.title}</h2>
          <p className="research-evaluation__subtitle">{research.name}</p>
        </div>
        <div className="research-evaluation__actions">
          <label className="research-evaluation__demo-toggle">
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
          <label className="research-evaluation__demo-toggle">
            <input
              type="checkbox"
              checked={forceError}
              onChange={(event) => {
                setForceError(event.target.checked);
                setReloadToken((token) => token + 1);
              }}
            />
            {labels.demoError}
          </label>
          <Button primary disabled title={labels.requestReviewHint}>
            {labels.requestReview}
          </Button>
        </div>
      </header>

      <EvaluationFiltersBar
        filters={filters}
        labels={labels.filters}
        onChange={setFilters}
        disabled={loadStatus !== "ready"}
      />

      <div className="research-evaluation__body" aria-live="polite">
        {loadStatus === "loading" ? (
          <div>
            <LoadingState message={labels.loading} />
            <ResearchWorkspaceSkeleton />
          </div>
        ) : null}

        {loadStatus === "error" && loadError ? (
          <div className="research-evaluation__error">
            <ErrorAlert title={labels.errorTitle} message={loadError} />
            <Button primary onClick={() => setReloadToken((token) => token + 1)}>
              {labels.retry}
            </Button>
          </div>
        ) : null}

        {loadStatus === "ready" && snapshot && overview ? (
          <>
            {isMissingValidation ? (
              <EvaluationEmptyState
                title={labels.missingValidationTitle}
                description={labels.missingValidationDescription}
              />
            ) : null}

            {!isMissingValidation ? (
              <>
                <EvaluationOverview
                  stats={overview}
                  language={language}
                  labels={labels.overview}
                />

                <EvaluationRecommendationPanelView
                  panel={snapshot.recommendation}
                  language={language}
                  labels={labels.recommendation}
                />

                <ReadinessRules
                  rules={snapshot.recommendation.ruleChecks}
                  labels={labels.readiness}
                />

                <ConfidenceBreakdown
                  dimensions={dimensions}
                  labels={labels.breakdown}
                  weightsTotal={getEvaluationWeightsTotal()}
                />

                <EvaluationBlockers
                  issues={snapshot.issues}
                  labels={labels.blockers}
                />

                <EvaluationStrengthsWeaknesses
                  items={snapshot.strengthsWeaknesses}
                  labels={labels.strengthsWeaknesses}
                />

                <EvaluationHistory
                  history={snapshot.history}
                  language={language}
                  labels={labels.history}
                />

                <section
                  className="evaluation-dimensions"
                  aria-label={labels.dimensionsTitle}
                >
                  <h3 className="evaluation-dimensions__title">
                    {labels.dimensionsTitle}
                  </h3>

                  {isCatalogEmpty ? (
                    <EvaluationEmptyState
                      title={labels.emptyTitle}
                      description={labels.emptyDescription}
                    />
                  ) : null}

                  {isFilterEmpty ? (
                    <EvaluationEmptyState
                      title={labels.filterEmptyTitle}
                      description={labels.filterEmptyDescription}
                    />
                  ) : null}

                  <div className="evaluation-dimensions__list">
                    {visible.map((dimension) => (
                      <EvaluationDimensionCard
                        key={dimension.key}
                        dimension={dimension}
                        language={language}
                        labels={labels.dimensionCard}
                        expanded={Boolean(expandedKeys[dimension.key])}
                        onToggle={toggleDimension}
                      />
                    ))}
                  </div>
                </section>
              </>
            ) : null}
          </>
        ) : null}
      </div>
    </section>
  );
}
