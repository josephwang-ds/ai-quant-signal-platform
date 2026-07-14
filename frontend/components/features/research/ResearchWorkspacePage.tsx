"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import AppShell from "@/components/layout/AppShell";
import EvidenceSummary from "@/components/features/research/EvidenceSummary";
import OverviewSection from "@/components/features/research/OverviewSection";
import ResearchNotebook from "@/components/features/research/notebook/ResearchNotebook";
import ResearchExperiments from "@/components/features/research/experiments/ResearchExperiments";
import ResearchActionPanel from "@/components/features/research/ResearchActionPanel";
import ResearchTimeline from "@/components/features/research/ResearchTimeline";
import ResearchWorkspaceHeader from "@/components/features/research/ResearchWorkspaceHeader";
import ResearchWorkspaceNavigation from "@/components/features/research/ResearchWorkspaceNavigation";
import ResearchWorkspaceSkeleton from "@/components/features/research/ResearchWorkspaceSkeleton";
import WorkspacePlaceholder from "@/components/features/research/WorkspacePlaceholder";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import ErrorAlert from "@/components/ui/ErrorAlert";
import LoadingState from "@/components/ui/LoadingState";
import SectionCard from "@/components/ui/SectionCard";
import type { TranslationKey } from "@/lib/i18n";
import { getMockTimelineEvents } from "@/lib/mockNotebookCatalog";
import {
  loadMockResearchById,
  MockResearchError,
} from "@/lib/mockResearchCatalog";
import { getCanonicalResearchPackage } from "@/lib/canonicalMaCrossover";
import { mergeTimelineEvents } from "@/lib/researchNotebook";
import {
  isResearchWorkspaceSection,
  resolveWorkspaceSection,
} from "@/lib/researchWorkspace";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";
import type { ResearchExperiment } from "@/types/experiment";
import type { NotebookEntry, ResearchTimelineEvent } from "@/types/notebook";
import type {
  ResearchDetail,
  ResearchWorkspaceSection,
} from "@/types/research";
import ValidationPendingPanel from "@/components/features/research/ValidationPendingPanel";
import ProvenanceBanner from "@/components/features/research/execution/ProvenanceBanner";
import { useResearchExecution } from "@/components/features/research/execution/useResearchExecution";
import {
  applyExecutionToExperiments,
  applyExecutionToResearch,
  HISTORICAL_DISCLAIMER,
  validationDisplayStatus,
} from "@/lib/applyResearchExecution";
import { getMockExperiments } from "@/lib/mockExperimentCatalog";
import { METRIC_NOT_CALCULATED } from "@/lib/researchExperiments";

type LoadStatus = "loading" | "ready" | "error" | "not_found";

type PlaceholderCopy = {
  titleKey: TranslationKey;
  summaryKey: TranslationKey;
  capabilityKeys: TranslationKey[];
};

const PLACEHOLDER_COPY: Record<
  Exclude<
    ResearchWorkspaceSection,
    "overview" | "notebook" | "timeline" | "experiments" | "validation" | "evaluation"
  >,
  PlaceholderCopy
> = {
  files: {
    titleKey: "researchWsFilesTitle",
    summaryKey: "researchWsFilesSummary",
    capabilityKeys: [
      "researchWsFilesCap1",
      "researchWsFilesCap2",
      "researchWsFilesCap3",
    ],
  },
  settings: {
    titleKey: "researchWsSettingsTitle",
    summaryKey: "researchWsSettingsSummary",
    capabilityKeys: [
      "researchWsSettingsCap1",
      "researchWsSettingsCap2",
      "researchWsSettingsCap3",
    ],
  },
};

export type ResearchWorkspacePageProps = {
  researchId: string;
};

/**
 * Research Workspace Detail（PR-003 + PR-004 Notebook）。
 * TODO(backend): 用 getResearch(id) 替换 loadMockResearchById。
 */
export default function ResearchWorkspacePage({
  researchId,
}: ResearchWorkspacePageProps) {
  const { language, setLanguage, tr } = useWorkspaceLanguage();
  const searchParams = useSearchParams();
  const activeSection = resolveWorkspaceSection(
    searchParams.get("tab"),
    searchParams.get("section")
  );

  const [research, setResearch] = useState<ResearchDetail | null>(null);
  const [loadStatus, setLoadStatus] = useState<LoadStatus>("loading");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);
  const [sessionNotebookEntries, setSessionNotebookEntries] = useState<
    NotebookEntry[]
  >([]);
  const [sessionTimelineEvents, setSessionTimelineEvents] = useState<
    ResearchTimelineEvent[]
  >([]);
  const [sessionExperiments, setSessionExperiments] = useState<
    ResearchExperiment[]
  >([]);
  const [selectedExperimentId, setSelectedExperimentId] = useState<string | null>(
    null
  );

  const {
    enabled: executionEnabled,
    status: executionStatus,
    execution,
    error: executionError,
    reload: reloadExecution,
  } = useResearchExecution(researchId);

  const displayResearch = useMemo(() => {
    if (!research) {
      return null;
    }
    if (executionEnabled && executionStatus === "ready" && execution) {
      return applyExecutionToResearch(research, execution);
    }
    return research;
  }, [research, executionEnabled, executionStatus, execution]);

  const executedExperiments = useMemo(() => {
    if (!executionEnabled || executionStatus !== "ready" || !execution) {
      return null;
    }
    return applyExecutionToExperiments(
      getMockExperiments(researchId),
      execution
    );
  }, [executionEnabled, executionStatus, execution, researchId]);

  const provenanceLabels = useMemo(
    () => ({
      realData: tr("researchExecRealData"),
      cached: tr("researchExecCached"),
      stale: tr("researchExecStale"),
      provider: tr("researchExecProvider"),
      symbol: tr("researchExecSymbol"),
      range: tr("researchExecRange"),
      retrieved: tr("researchExecRetrieved"),
      disclaimer: tr("researchExecDisclaimer"),
    }),
    [tr]
  );

  function formatMetric(value: number | null, kind: "pct" | "num" | "raw"): string {
    if (value === null || Number.isNaN(value)) {
      return METRIC_NOT_CALCULATED;
    }
    if (kind === "pct") {
      return `${(value * 100).toFixed(1)}%`;
    }
    if (kind === "num") {
      return value.toFixed(2);
    }
    return String(Math.round(value));
  }

  const loadDetail = useCallback(async () => {
    setLoadStatus("loading");
    setLoadError(null);
    try {
      const data = await loadMockResearchById(researchId);
      if (!data) {
        setResearch(null);
        setLoadStatus("not_found");
        return;
      }
      setResearch(data);
      setLoadStatus("ready");
    } catch (error) {
      const message =
        error instanceof MockResearchError
          ? error.message
          : "The research workspace could not be loaded. Please retry.";
      setResearch(null);
      setLoadError(message);
      setLoadStatus("error");
    }
  }, [researchId]);

  useEffect(() => {
    void loadDetail();
  }, [loadDetail, reloadToken]);

  useEffect(() => {
    setSessionNotebookEntries([]);
    setSessionTimelineEvents([]);
    setSessionExperiments([]);
    setSelectedExperimentId(searchParams.get("experimentId"));
    // Only reset session state when switching research projects.
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional: seed from URL once per researchId
  }, [researchId]);

  const navLabels = useMemo(
    () => ({
      overview: tr("researchWsNavOverview"),
      notebook: tr("researchWsNavNotebook"),
      experiments: tr("researchWsNavExperiments"),
      validation: tr("researchWsNavValidation"),
      evaluation: tr("researchWsNavEvaluation"),
      timeline: tr("researchWsNavTimeline"),
      files: tr("researchWsNavFiles"),
      settings: tr("researchWsNavSettings"),
    }),
    [tr]
  );

  const timelineEvents = useMemo(() => {
    if (!research) {
      return [];
    }
    return mergeTimelineEvents(
      getMockTimelineEvents(research.id),
      sessionTimelineEvents
    );
  }, [research, sessionTimelineEvents]);

  function handleSessionEntrySaved(
    entry: NotebookEntry,
    timelineEvent: ResearchTimelineEvent
  ) {
    setSessionNotebookEntries((prev) => [entry, ...prev]);
    setSessionTimelineEvents((prev) => [timelineEvent, ...prev]);
  }

  function handleExperimentDesigned(payload: {
    experiment: ResearchExperiment;
    notebookEntry: NotebookEntry;
    timelineEvent: ResearchTimelineEvent;
  }) {
    setSessionExperiments((prev) => [payload.experiment, ...prev]);
    setSessionNotebookEntries((prev) => [payload.notebookEntry, ...prev]);
    setSessionTimelineEvents((prev) => [payload.timelineEvent, ...prev]);
  }

  function renderMainSection() {
    if (!displayResearch) {
      return null;
    }

    const provenanceSlot =
      executionEnabled && executionStatus === "ready" && execution ? (
        <ProvenanceBanner
          provenance={execution.provenance}
          labels={provenanceLabels}
          warnings={execution.warnings}
        />
      ) : executionEnabled && executionStatus === "error" ? (
        <div className="research-execution-error">
          <ErrorAlert
            title={tr("researchExecUnavailableTitle")}
            message={executionError ?? tr("researchExecUnavailableDescription")}
          />
          <Button primary onClick={reloadExecution}>
            {tr("researchExecRetry")}
          </Button>
        </div>
      ) : executionEnabled && executionStatus === "loading" ? (
        <LoadingState message={tr("researchExecLoading")} />
      ) : null;

    const calculatedMetrics =
      executionEnabled && executionStatus === "ready" && execution
        ? {
            totalReturn: formatMetric(execution.metrics.total_return, "pct"),
            benchmarkReturn: formatMetric(
              execution.benchmark_metrics.total_return,
              "pct"
            ),
            cagr: formatMetric(execution.metrics.cagr, "pct"),
            sharpe: formatMetric(execution.metrics.sharpe_ratio, "num"),
            maxDrawdown: formatMetric(execution.metrics.maximum_drawdown, "pct"),
            volatility: formatMetric(
              execution.metrics.annualized_volatility,
              "pct"
            ),
            tradeCount: formatMetric(execution.metrics.trade_count, "raw"),
          }
        : null;

    if (activeSection === "overview") {
      return (
        <OverviewSection
          research={displayResearch}
          calculatedMetrics={calculatedMetrics}
          provenanceSlot={provenanceSlot}
          labels={{
            researchQuestion: tr("researchWsQuestion"),
            hypothesis: tr("researchWsHypothesis"),
            researchObjective: tr("researchWsObjective"),
            currentStage: tr("researchWsCurrentStage"),
            researchConfidence: tr("researchWsConfidence"),
            currentRecommendation: tr("researchListRecommendation"),
            researchSummary: tr("researchWsSummary"),
            evidenceNarrative: tr("researchWsEvidenceNarrative"),
            validationSummary: tr("researchWsValidationSummary"),
            keyStrengths: tr("researchWsKeyStrengths"),
            knownWeaknesses: tr("researchWsKnownWeaknesses"),
            openQuestions: tr("researchWsOpenQuestions"),
            nextActions: tr("researchWsNextActions"),
            lifecycleTitle: tr("researchWsLifecycleTitle"),
            lifecycleDescription: tr("researchWsLifecycleDescription"),
            evidenceTitle: tr("researchWsEvidenceTitle"),
            evidenceDescription: tr("researchWsEvidenceDescription"),
            confidence: tr("researchListEvaluationArea"),
            strategyConfig: tr("researchWsStrategyConfig"),
            dataRequirements: tr("researchWsDataRequirements"),
            symbol: tr("researchListSymbol"),
            benchmark: tr("researchListBenchmark"),
            strategy: tr("researchListStrategy"),
            dataStatus: tr("researchListDataStatus"),
            metricsStatus: tr("researchListMetricsStatus"),
            calculatedMetricsTitle: tr("researchWsCalculatedMetrics"),
            metricTotalReturn: tr("researchWsMetricTotalReturn"),
            metricBenchmarkReturn: tr("researchWsMetricBenchReturn"),
            metricCagr: tr("researchExpMetricCagr"),
            metricSharpe: tr("researchExpMetricSharpe"),
            metricMaxDd: tr("researchExpMetricMaxDD"),
            metricVol: tr("researchExpMetricVol"),
            metricTrades: tr("researchExpMetricTrades"),
          }}
        />
      );
    }

    if (activeSection === "notebook") {
      return (
        <ResearchNotebook
          research={displayResearch}
          language={language}
          sessionEntries={sessionNotebookEntries}
          onSessionEntrySaved={handleSessionEntrySaved}
          labels={{
            title: tr("researchNbDesignNotesTitle"),
            entryCount: tr("researchNbEntryCount"),
            lastUpdated: tr("researchNbLastUpdated"),
            newEntry: tr("researchNbNewEntry"),
            loading: tr("researchNbLoading"),
            errorTitle: tr("researchNbErrorTitle"),
            retry: tr("researchNbRetry"),
            emptyTitle: tr("researchNbEmptyTitle"),
            emptyDescription: tr("researchNbEmptyDescription"),
            filterEmptyTitle: tr("researchNbFilterEmptyTitle"),
            filterEmptyDescription: tr("researchNbFilterEmptyDescription"),
            filters: {
              filterType: tr("researchNbFilterType"),
              filterAll: tr("researchNbFilterAll"),
              sort: tr("researchNbSort"),
              sortNewest: tr("researchNbSortNewest"),
              sortOldest: tr("researchNbSortOldest"),
            },
            card: {
              author: tr("researchNbCardAuthor"),
              created: tr("researchNbCardCreated"),
              edited: tr("researchNbCardEdited"),
              related: tr("researchNbCardRelated"),
              tags: tr("researchWsTags"),
            },
            composer: {
              title: tr("researchNbComposerTitle"),
              entryType: tr("researchNbComposerType"),
              entryTitle: tr("researchNbComposerEntryTitle"),
              content: tr("researchNbComposerContent"),
              tags: tr("researchNbComposerTags"),
              tagsHint: tr("researchNbComposerTagsHint"),
              relatedArtifact: tr("researchNbComposerArtifact"),
              relatedNone: tr("researchNbComposerArtifactNone"),
              save: tr("researchNbComposerSave"),
              cancel: tr("researchNbComposerCancel"),
              entryTypeRequired: tr("researchNbValidationType"),
              titleRequired: tr("researchNbValidationTitle"),
              bodyRequired: tr("researchNbValidationBody"),
            },
          }}
        />
      );
    }

    if (activeSection === "experiments") {
      return (
        <ResearchExperiments
          research={displayResearch}
          language={language}
          sessionExperiments={sessionExperiments}
          selectedExperimentId={selectedExperimentId}
          onSelectExperiment={setSelectedExperimentId}
          onExperimentDesigned={handleExperimentDesigned}
          executedExperiments={executedExperiments}
          provenanceSlot={provenanceSlot}
          labels={{
            title: tr("researchExpTitle"),
            totalCount: tr("researchExpTotalCount"),
            activeCount: tr("researchExpActiveCount"),
            newExperiment: tr("researchExpNew"),
            loading: tr("researchExpLoading"),
            errorTitle: tr("researchExpErrorTitle"),
            retry: tr("researchExpRetry"),
            emptyTitle: tr("researchExpEmptyTitle"),
            emptyDescription: tr("researchExpEmptyDescription"),
            filterEmptyTitle: tr("researchExpFilterEmptyTitle"),
            filterEmptyDescription: tr("researchExpFilterEmptyDescription"),
            notFoundTitle: tr("researchExpNotFoundTitle"),
            notFoundDescription: tr("researchExpNotFoundDescription"),
            backToList: tr("researchExpBackToList"),
            filters: {
              search: tr("researchExpSearch"),
              searchPlaceholder: tr("researchExpSearchPlaceholder"),
              status: tr("researchExpFilterStatus"),
              type: tr("researchExpFilterType"),
              sort: tr("researchExpSort"),
              all: tr("researchExpFilterAll"),
              sortUpdated: tr("researchExpSortUpdated"),
              sortCreated: tr("researchExpSortCreated"),
              sortResult: tr("researchExpSortResult"),
            },
            card: {
              hypothesis: tr("researchExpCardHypothesis"),
              dataset: tr("researchExpCardDataset"),
              window: tr("researchExpCardWindow"),
              benchmark: tr("researchExpCardBenchmark"),
              owner: tr("researchListOwner"),
              updated: tr("researchListUpdated"),
              result: tr("researchExpCardResult"),
              readiness: tr("researchExpCardReadiness"),
              parameters: tr("researchExpCardParameters"),
              linkedNotes: tr("researchExpCardLinkedNotes"),
              openDetail: tr("researchExpOpenDetail"),
              sharpe: tr("researchExpMetricSharpe"),
              maxDrawdown: tr("researchExpMetricMaxDD"),
            },
            composer: {
              title: tr("researchExpComposerTitle"),
              name: tr("researchExpComposerName"),
              hypothesis: tr("researchExpComposerHypothesis"),
              experimentType: tr("researchExpComposerType"),
              dataset: tr("researchExpComposerDataset"),
              startDate: tr("researchExpComposerStart"),
              endDate: tr("researchExpComposerEnd"),
              benchmark: tr("researchExpComposerBenchmark"),
              parameters: tr("researchExpComposerParameters"),
              parametersHint: tr("researchExpComposerParametersHint"),
              successCriteria: tr("researchExpComposerSuccess"),
              falsification: tr("researchExpComposerFalsify"),
              notes: tr("researchExpComposerNotes"),
              save: tr("researchExpComposerSave"),
              cancel: tr("researchExpComposerCancel"),
              nameRequired: tr("researchExpValidationName"),
              hypothesisRequired: tr("researchExpValidationHypothesis"),
              typeRequired: tr("researchExpValidationType"),
              datasetRequired: tr("researchExpValidationDataset"),
              startRequired: tr("researchExpValidationStart"),
              endRequired: tr("researchExpValidationEnd"),
              dateRangeInvalid: tr("researchExpValidationDateRange"),
              successRequired: tr("researchExpValidationSuccess"),
              falsificationRequired: tr("researchExpValidationFalsify"),
            },
            detail: {
              title: tr("researchExpDetailTitle"),
              close: tr("researchExpDetailClose"),
              overview: tr("researchExpDetailOverview"),
              hypothesis: tr("researchExpCardHypothesis"),
              configuration: tr("researchExpDetailConfig"),
              parameters: tr("researchExpCardParameters"),
              results: tr("researchExpCardResult"),
              notes: tr("researchExpComposerNotes"),
              relatedEvidence: tr("researchExpDetailEvidence"),
              linkedNotebook: tr("researchExpDetailNotebook"),
              validationReadiness: tr("researchExpCardReadiness"),
              dataset: tr("researchExpCardDataset"),
              window: tr("researchExpCardWindow"),
              benchmark: tr("researchExpCardBenchmark"),
              owner: tr("researchListOwner"),
              created: tr("researchWsCreated"),
              updated: tr("researchListUpdated"),
              success: tr("researchExpComposerSuccess"),
              falsification: tr("researchExpComposerFalsify"),
              none: tr("researchExpNone"),
              lifecycle: {
                title: tr("researchExpLifecycleTitle"),
                description: tr("researchExpLifecycleDescription"),
                completed: tr("researchExpLifecycleCompleted"),
                current: tr("researchExpLifecycleCurrent"),
                upcoming: tr("researchExpLifecycleUpcoming"),
                terminalNote: tr("researchExpLifecycleTerminal"),
                governedNote: tr("researchExpLifecycleGoverned"),
              },
              metrics: {
                title: tr("researchExpMetricsTitle"),
                disclaimer: tr("researchExpMetricsDisclaimer"),
                sharpe: tr("researchExpMetricSharpe"),
                cagr: tr("researchExpMetricCagr"),
                maxDrawdown: tr("researchExpMetricMaxDD"),
                volatility: tr("researchExpMetricVol"),
                tradeCount: tr("researchExpMetricTrades"),
                winRate: tr("researchExpMetricWinRate"),
                totalTransactionCost: tr("researchExpMetricCost"),
              },
            },
          }}
        />
      );
    }

    if (activeSection === "validation") {
      return (
        <>
          {provenanceSlot}
          <ValidationPendingPanel
            stages={getCanonicalResearchPackage().plannedValidationStages}
            statusForStage={(stageId) =>
              validationDisplayStatus(
                stageId,
                executionStatus === "ready" ? execution : null
              )
            }
            labels={{
              title: tr("researchWsValidationTitle"),
              summary: tr("researchWsValidationSectionSummary"),
              notStarted: tr("researchWsValidationNotStarted"),
              awaitingData: tr("researchWsValidationAwaitingData"),
              completed: tr("researchWsValidationCompleted"),
              note:
                executionStatus === "ready"
                  ? HISTORICAL_DISCLAIMER
                  : tr("researchWsExecutionPendingNote"),
            }}
          />
        </>
      );
    }

    if (activeSection === "evaluation") {
      return (
        <WorkspacePlaceholder
          title={tr("researchWsEvaluationTitle")}
          summary={tr("researchWsEvaluationUnavailable")}
          plannedCapabilities={[
            tr("researchWsEvaluationCap1"),
            tr("researchWsEvaluationCap2"),
            tr("researchWsEvaluationCap3"),
          ]}
          deferredNote={tr("researchWsExecutionPendingNote")}
        />
      );
    }

    if (activeSection === "timeline") {
      return (
        <ResearchTimeline
          events={timelineEvents}
          language={language}
          labels={{
            title: tr("researchTlTitle"),
            description: tr("researchTlDescription"),
            sessionNote: tr("researchTlSessionNote"),
            empty: tr("researchTlEmpty"),
          }}
        />
      );
    }

    if (isResearchWorkspaceSection(activeSection) && activeSection in PLACEHOLDER_COPY) {
      const copy = PLACEHOLDER_COPY[activeSection as keyof typeof PLACEHOLDER_COPY];
      return (
        <WorkspacePlaceholder
          title={tr(copy.titleKey)}
          summary={tr(copy.summaryKey)}
          plannedCapabilities={copy.capabilityKeys.map((key) => tr(key))}
          deferredNote={tr("researchWsDeferredNote")}
        />
      );
    }

    return null;
  }

  const showEvidencePreview =
    activeSection !== "overview" &&
    activeSection !== "notebook" &&
    activeSection !== "timeline" &&
    activeSection !== "experiments" &&
    activeSection !== "validation" &&
    activeSection !== "evaluation";

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <SectionCard>
        {loadStatus === "loading" ? (
          <div className="research-workspace-loading">
            <LoadingState message={tr("researchWsLoading")} />
            <ResearchWorkspaceSkeleton />
          </div>
        ) : null}

        {loadStatus === "error" && loadError ? (
          <div className="research-workspace-error">
            <ErrorAlert title={tr("researchWsErrorTitle")} message={loadError} />
            <Button primary onClick={() => setReloadToken((token) => token + 1)}>
              {tr("researchWsRetry")}
            </Button>
          </div>
        ) : null}

        {loadStatus === "not_found" ? (
          <EmptyState
            title={tr("researchWsNotFoundTitle")}
            description={tr("researchWsNotFoundDescription")}
            action={
              <Link href="/" className="btn btn--primary">
                {tr("researchWsBackToList")}
              </Link>
            }
          />
        ) : null}

        {loadStatus === "ready" && displayResearch ? (
          <div className="research-workspace">
            <ResearchWorkspaceHeader
              research={displayResearch}
              language={language}
              labels={{
                back: tr("researchWsBackToList"),
                moreActions: tr("researchWsMoreActions"),
                moreActionsHint: tr("researchWsMoreActionsHint"),
                owner: tr("researchListOwner"),
                created: tr("researchWsCreated"),
                updated: tr("researchListUpdated"),
                recommendation: tr("researchListRecommendation"),
                confidence: tr("researchListEvaluationArea"),
                tags: tr("researchWsTags"),
              }}
            />

            <ResearchWorkspaceNavigation
              researchId={displayResearch.id}
              activeSection={activeSection}
              labels={navLabels}
            />

            <div className="research-workspace__layout">
              <div className="research-workspace__main">
                {renderMainSection()}

                {showEvidencePreview ? (
                  <div className="research-workspace__placeholder-evidence">
                    <EvidenceSummary
                      items={displayResearch.evidenceItems.slice(0, 3)}
                      title={tr("researchWsEvidencePreviewTitle")}
                      description={tr("researchWsEvidencePreviewDescription")}
                    />
                  </div>
                ) : null}
              </div>

              <ResearchActionPanel
                labels={{
                  title: tr("researchWsActionsTitle"),
                  description: tr("researchWsActionsDescription"),
                  addNotebook: tr("researchWsActionNotebook"),
                  createExperiment: tr("researchWsActionExperiment"),
                  runValidation: tr("researchWsActionValidation"),
                  requestEvaluation: tr("researchWsActionEvaluation"),
                  exportResearch: tr("researchWsActionExport"),
                  comingLater: tr("researchWsComingLater"),
                }}
              />
            </div>
          </div>
        ) : null}
      </SectionCard>
    </AppShell>
  );
}
