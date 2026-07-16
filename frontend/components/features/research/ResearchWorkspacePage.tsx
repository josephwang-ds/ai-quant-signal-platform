"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
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
import ProvenanceBanner from "@/components/features/research/execution/ProvenanceBanner";
import { useResearchExecution } from "@/components/features/research/execution/useResearchExecution";
import ResearchValidationPanel from "@/components/features/research/validation/ResearchValidationPanel";
import { useResearchValidation } from "@/components/features/research/validation/useResearchValidation";
import ResearchEvaluationPanel from "@/components/features/research/evaluation/ResearchEvaluationPanel";
import { useResearchEvaluation } from "@/components/features/research/evaluation/useResearchEvaluation";
import ResearchCopilotPanel from "@/components/features/research/copilot/ResearchCopilotPanel";
import { useResearchCopilot } from "@/components/features/research/copilot/useResearchCopilot";
import {
  applyExecutionToExperiments,
  applyExecutionToResearch,
} from "@/lib/applyResearchExecution";
import { getMockExperiments } from "@/lib/mockExperimentCatalog";
import { METRIC_NOT_CALCULATED } from "@/lib/researchExperiments";
import {
  canRequestEvaluation,
  shouldReloadEvaluationOnAction,
  shouldReloadValidationOnAction,
} from "@/lib/workspaceActionTriggers";

type LoadStatus = "loading" | "ready" | "error" | "not_found";

type PlaceholderCopy = {
  titleKey: TranslationKey;
  summaryKey: TranslationKey;
  capabilityKeys: TranslationKey[];
};

const PLACEHOLDER_COPY: Record<
  Exclude<
    ResearchWorkspaceSection,
    | "overview"
    | "notebook"
    | "timeline"
    | "experiments"
    | "validation"
    | "evaluation"
    | "copilot"
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
  const router = useRouter();
  const searchParams = useSearchParams();
  const activeSection = resolveWorkspaceSection(
    searchParams.get("tab"),
    searchParams.get("section")
  );

  const navigateToSection = useCallback(
    (section: ResearchWorkspaceSection) => {
      const href =
        section === "overview"
          ? `/research/${encodeURIComponent(researchId)}`
          : `/research/${encodeURIComponent(researchId)}?tab=${section}`;
      router.push(href);
    },
    [researchId, router]
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
  const validationEvidenceActive =
    activeSection === "validation" ||
    activeSection === "evaluation" ||
    activeSection === "copilot";
  const {
    enabled: validationEnabled,
    status: validationStatus,
    validation,
    error: validationError,
    reload: reloadValidation,
  } = useResearchValidation(researchId, validationEvidenceActive);
  const validationRunId = validation?.validation_run_id ?? null;
  const {
    enabled: evaluationEnabled,
    status: evaluationStatus,
    evaluation,
    error: evaluationError,
    reload: reloadEvaluation,
  } = useResearchEvaluation(
    researchId,
    activeSection === "evaluation",
    validationRunId
  );
  const [copilotQuestion, setCopilotQuestion] = useState("");
  const {
    enabled: copilotEnabled,
    status: copilotStatus,
    result: copilotResult,
    error: copilotError,
    ask: askCopilot,
    reset: resetCopilot,
  } = useResearchCopilot(
    researchId,
    activeSection === "copilot",
    validationRunId
  );

  /**
   * Validation trigger design (PR-020):
   * - Navigate to Validation first.
   * - If validation evidence was not yet active, the existing tab hook owns the
   *   single auto-fetch when the section becomes active.
   * - If validation evidence was already active (validation/evaluation/copilot),
   *   call reloadValidation() exactly once to re-run without creating a second hook.
   */
  const handleRunValidation = useCallback(() => {
    navigateToSection("validation");
    if (shouldReloadValidationOnAction(validationEvidenceActive)) {
      reloadValidation();
    }
  }, [navigateToSection, reloadValidation, validationEvidenceActive]);

  const handleRequestEvaluation = useCallback(() => {
    if (!canRequestEvaluation(validationRunId)) {
      return;
    }
    navigateToSection("evaluation");
    if (shouldReloadEvaluationOnAction(validationRunId, activeSection)) {
      reloadEvaluation();
    }
  }, [
    activeSection,
    navigateToSection,
    reloadEvaluation,
    validationRunId,
  ]);

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
      assetClass: tr("researchExecAssetClass"),
      adjustment: tr("researchExecAdjustment"),
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

  useEffect(() => {
    if (activeSection !== "copilot") {
      resetCopilot();
      setCopilotQuestion("");
    }
  }, [activeSection, resetCopilot]);

  const copilotSampleQuestions = useMemo(
    () => [
      tr("researchCopilotSample1"),
      tr("researchCopilotSample2"),
      tr("researchCopilotSample3"),
      tr("researchCopilotSample4"),
      tr("researchCopilotSample5"),
    ],
    [tr]
  );

  const navLabels = useMemo(
    () => ({
      overview: tr("researchWsNavOverview"),
      notebook: tr("researchWsNavNotebook"),
      experiments: tr("researchWsNavExperiments"),
      validation: tr("researchWsNavValidation"),
      evaluation: tr("researchWsNavEvaluation"),
      copilot: tr("researchWsNavCopilot"),
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
      if (!validationEnabled) {
        return (
          <ErrorAlert
            title={tr("researchValUnavailableTitle")}
            message={tr("researchValUnavailableDescription")}
          />
        );
      }
      if (validationStatus === "loading") {
        return <LoadingState message={tr("researchValLoading")} />;
      }
      if (validationStatus === "error") {
        return (
          <div className="research-execution-error">
            <ErrorAlert
              title={tr("researchValUnavailableTitle")}
              message={validationError ?? tr("researchValUnavailableDescription")}
            />
            <Button primary onClick={reloadValidation}>
              {tr("researchValRetry")}
            </Button>
          </div>
        );
      }
      if (validationStatus !== "ready" || !validation) {
        return null;
      }
      return (
        <ResearchValidationPanel
          validation={validation}
          labels={{
            title: tr("researchWsValidationTitle"),
            summary: tr("researchValSummary"),
            status: tr("researchValStatus"),
            evidenceComplete: tr("researchValEvidenceComplete"),
            yes: tr("researchValYes"),
            no: tr("researchValNo"),
            completed: tr("researchWsValidationCompleted"),
            incomplete: tr("researchValIncomplete"),
            failed: tr("researchValFailed"),
            unavailable: tr("researchValUnavailable"),
            source: tr("researchValSource"),
            generated: tr("researchValGenerated"),
            rules: tr("researchValRules"),
            warnings: tr("researchValWarnings"),
            blockers: tr("researchValBlockers"),
            evidence: tr("researchValEvidence"),
            oosTitle: tr("researchValOosTitle"),
            splitDate: tr("researchValSplitDate"),
            inSampleRatio: tr("researchValInSampleRatio"),
            minimumOos: tr("researchValMinimumOos"),
            boundary: tr("researchValBoundary"),
            inSample: tr("researchValInSample"),
            outOfSample: tr("researchValOutOfSample"),
            benchmark: tr("researchValBenchmark"),
            observations: tr("researchValObservations"),
            metric: tr("researchValMetric"),
            totalReturn: tr("researchValTotalReturn"),
            cagr: tr("researchValCagr"),
            sharpe: tr("researchValSharpe"),
            maxDrawdown: tr("researchValMaxDrawdown"),
            volatility: tr("researchValVolatility"),
            trades: tr("researchValTrades"),
            totalCosts: tr("researchValTotalCosts"),
            parameterTitle: tr("researchValParameterTitle"),
            validCombinations: tr("researchValValidCombinations"),
            profitableCombinations: tr("researchValProfitableCombinations"),
            positiveSharpe: tr("researchValPositiveSharpe"),
            medianSharpe: tr("researchValMedianSharpe"),
            sharpeRange: tr("researchValSharpeRange"),
            medianDrawdown: tr("researchValMedianDrawdown"),
            canonicalPercentile: tr("researchValCanonicalPercentile"),
            shortWindow: tr("researchValShortWindow"),
            longWindow: tr("researchValLongWindow"),
            canonical: tr("researchValCanonical"),
            costTitle: tr("researchValCostTitle"),
            transactionCost: tr("researchValTransactionCost"),
            returnDegradation: tr("researchValReturnDegradation"),
            sharpeDegradation: tr("researchValSharpeDegradation"),
            mathematicallyValid: tr("researchValMathematicallyValid"),
            canonicalCost: tr("researchValCanonicalCost"),
            dataQualityTitle: tr("researchValDataQualityTitle"),
            provider: tr("researchValProvider"),
            dateRange: tr("researchValDateRange"),
            cache: tr("researchValCache"),
            cacheHit: tr("researchValCacheHit"),
            cacheMiss: tr("researchValCacheMiss"),
            fatalIssues: tr("researchValFatalIssues"),
            checks: tr("researchValChecks"),
            check: tr("researchValCheck"),
            severity: tr("researchValSeverity"),
            details: tr("researchValDetails"),
            notAvailable: tr("researchValNotAvailable"),
          }}
          />
      );
    }

    if (activeSection === "evaluation") {
      if (!evaluationEnabled) {
        return (
          <ErrorAlert
            title={tr("researchEvalUnavailableTitle")}
            message={tr("researchEvalUnavailableDescription")}
          />
        );
      }
      if (evaluationStatus === "awaiting_validation") {
        return (
          <div className="research-execution-error">
            <ErrorAlert
              title={tr("researchEvalAwaitingValidationTitle")}
              message={tr("researchEvalAwaitingValidationDescription")}
            />
            <Link
              href={`/research/${encodeURIComponent(researchId)}?tab=validation`}
              className="btn btn--primary"
            >
              {tr("researchEvalGoToValidation")}
            </Link>
          </div>
        );
      }
      if (evaluationStatus === "loading") {
        return <LoadingState message={tr("researchEvalLoading")} />;
      }
      if (evaluationStatus === "error") {
        return (
          <div className="research-execution-error">
            <ErrorAlert
              title={tr("researchEvalUnavailableTitle")}
              message={evaluationError ?? tr("researchEvalUnavailableDescription")}
            />
            <Button primary onClick={reloadEvaluation}>
              {tr("researchEvalRetry")}
            </Button>
          </div>
        );
      }
      if (evaluationStatus !== "ready" || !evaluation) {
        return null;
      }
      return (
        <>
          <ResearchEvaluationPanel
            evaluation={evaluation}
            labels={{
              title: tr("researchWsEvaluationTitle"),
              summary: tr("researchEvalSummary"),
              status: tr("researchEvalStatus"),
              completed: tr("researchEvalCompleted"),
              incomplete: tr("researchEvalIncomplete"),
              blocked: tr("researchEvalBlocked"),
              source: tr("researchEvalSource"),
              generated: tr("researchEvalGenerated"),
              coverageTitle: tr("researchEvalCoverageTitle"),
              implementedStages: tr("researchEvalImplementedStages"),
              completedStagesCount: tr("researchEvalCompletedStagesCount"),
              coveragePercentage: tr("researchEvalCoveragePercentage"),
              coverageDisclaimer: tr("researchEvalCoverageDisclaimer"),
              evidenceSummaryTitle: tr("researchEvalEvidenceSummaryTitle"),
              stageColumn: tr("researchEvalStageColumn"),
              statusColumn: tr("researchEvalStatusColumn"),
              summaryColumn: tr("researchEvalSummaryColumn"),
              completedEvidenceTitle: tr("researchEvalCompletedEvidenceTitle"),
              incompleteEvidenceTitle: tr("researchEvalIncompleteEvidenceTitle"),
              outstandingEvidenceTitle: tr("researchEvalOutstandingEvidenceTitle"),
              limitationsTitle: tr("researchEvalLimitationsTitle"),
              blockersTitle: tr("researchEvalBlockersTitle"),
              none: tr("researchEvalNone"),
              notAvailable: tr("researchEvalNotAvailable"),
            }}
          />
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
        </>
      );
    }

    if (activeSection === "copilot") {
      if (!copilotEnabled) {
        return (
          <ErrorAlert
            title={tr("researchCopilotUnavailableTitle")}
            message={tr("researchCopilotUnavailableDescription")}
          />
        );
      }
      return (
        <ResearchCopilotPanel
          labels={{
            title: tr("researchCopilotTitle"),
            subtitle: tr("researchCopilotSubtitle"),
            disclaimer: tr("researchCopilotDisclaimer"),
            sampleQuestionsTitle: tr("researchCopilotSampleQuestionsTitle"),
            questionPlaceholder: tr("researchCopilotQuestionPlaceholder"),
            askButton: tr("researchCopilotAskButton"),
            askingButton: tr("researchCopilotAskingButton"),
            answerTitle: tr("researchCopilotAnswerTitle"),
            citationsTitle: tr("researchCopilotCitationsTitle"),
            warningsTitle: tr("researchCopilotWarningsTitle"),
            groundingTitle: tr("researchCopilotGroundingTitle"),
            generatedAt: tr("researchCopilotGeneratedAt"),
            grounded: tr("researchCopilotGrounded"),
            partiallyGrounded: tr("researchCopilotPartiallyGrounded"),
            unavailable: tr("researchCopilotUnavailable"),
            awaitingValidationTitle: tr("researchCopilotAwaitingValidationTitle"),
            awaitingValidationDescription: tr(
              "researchCopilotAwaitingValidationDescription"
            ),
            goToValidation: tr("researchCopilotGoToValidation"),
            notConfigured: tr("researchCopilotNotConfigured"),
            limitations: tr("researchCopilotLimitations"),
          }}
          sampleQuestions={copilotSampleQuestions}
          status={
            validationEvidenceActive && validationStatus === "loading"
              ? "loading"
              : copilotStatus
          }
          result={copilotResult}
          error={
            copilotError ??
            (validationEvidenceActive && validationStatus === "error"
              ? validationError
              : null)
          }
          question={copilotQuestion}
          onQuestionChange={setCopilotQuestion}
          onAsk={() => void askCopilot(copilotQuestion)}
          onSampleQuestion={(sample) => {
            setCopilotQuestion(sample);
            void askCopilot(sample);
          }}
          onGoToValidation={() => {
            window.location.href = `/research/${encodeURIComponent(researchId)}?tab=validation`;
          }}
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
    activeSection !== "evaluation" &&
    activeSection !== "copilot";

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
                  runningValidation: tr("researchWsActionValidationRunning"),
                  requestEvaluation: tr("researchWsActionEvaluation"),
                  openCopilot: tr("researchWsActionCopilot"),
                  exportResearch: tr("researchWsActionExport"),
                  hintNotebook: tr("researchWsActionHintNotebook"),
                  hintExperiment: tr("researchWsActionHintExperiment"),
                  hintValidation: tr("researchWsActionHintValidation"),
                  hintEvaluation: tr("researchWsActionHintEvaluation"),
                  hintEvaluationDisabled: tr(
                    "researchWsActionHintEvaluationDisabled"
                  ),
                  hintCopilot: tr("researchWsActionHintCopilot"),
                  hintCopilotDisabled: tr(
                    "researchWsActionHintCopilotDisabled"
                  ),
                  hintExport: tr("researchWsActionHintExport"),
                }}
                activeSection={activeSection}
                onNavigate={navigateToSection}
                onRunValidation={handleRunValidation}
                onRequestEvaluation={handleRequestEvaluation}
                validationStatus={validationStatus}
                validationRunId={validationRunId}
                evaluationStatus={evaluationStatus}
              />
            </div>
          </div>
        ) : null}
      </SectionCard>
    </AppShell>
  );
}
