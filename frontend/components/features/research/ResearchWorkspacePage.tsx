"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import AppShell from "@/components/layout/AppShell";
import EvidenceSummary from "@/components/features/research/EvidenceSummary";
import OverviewSection from "@/components/features/research/OverviewSection";
import ResearchNotebook from "@/components/features/research/notebook/ResearchNotebook";
import ResearchExperiments from "@/components/features/research/experiments/ResearchExperiments";
import ResearchValidation from "@/components/features/research/validation/ResearchValidation";
import ResearchEvaluation from "@/components/features/research/evaluation/ResearchEvaluation";
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
import { getMockValidationTimelineEvents } from "@/lib/mockValidationCatalog";
import { getMockEvaluationTimelineEvents } from "@/lib/mockEvaluationCatalog";
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
  const [selectedValidationStageId, setSelectedValidationStageId] = useState<
    string | null
  >(null);

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
    setSelectedValidationStageId(searchParams.get("validationStageId"));
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
    // TODO(api): replace with domain event stream; validation events from Validation context.
    return mergeTimelineEvents(
      [
        ...getMockTimelineEvents(research.id),
        ...getMockValidationTimelineEvents(research.id),
        ...getMockEvaluationTimelineEvents(research.id),
      ],
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
    if (!research) {
      return null;
    }

    if (activeSection === "overview") {
      return (
        <OverviewSection
          research={research}
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
            confidence: tr("researchListConfidence"),
          }}
        />
      );
    }

    if (activeSection === "notebook") {
      return (
        <ResearchNotebook
          research={research}
          language={language}
          sessionEntries={sessionNotebookEntries}
          onSessionEntrySaved={handleSessionEntrySaved}
          labels={{
            title: tr("researchNbTitle"),
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
          research={research}
          language={language}
          sessionExperiments={sessionExperiments}
          selectedExperimentId={selectedExperimentId}
          onSelectExperiment={setSelectedExperimentId}
          onExperimentDesigned={handleExperimentDesigned}
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
        <ResearchValidation
          research={research}
          language={language}
          selectedStageId={selectedValidationStageId}
          onSelectStage={setSelectedValidationStageId}
          labels={{
            title: tr("researchValTitle"),
            stageCount: tr("researchValStageCount"),
            loading: tr("researchValLoading"),
            errorTitle: tr("researchValErrorTitle"),
            retry: tr("researchValRetry"),
            emptyTitle: tr("researchValEmptyTitle"),
            emptyDescription: tr("researchValEmptyDescription"),
            filterEmptyTitle: tr("researchValFilterEmptyTitle"),
            filterEmptyDescription: tr("researchValFilterEmptyDescription"),
            notFoundTitle: tr("researchValNotFoundTitle"),
            notFoundDescription: tr("researchValNotFoundDescription"),
            backToPipeline: tr("researchValBackToPipeline"),
            runValidation: tr("researchValRun"),
            runValidationHint: tr("researchValRunHint"),
            demoLoading: tr("researchValDemoLoading"),
            overview: {
              title: tr("researchValOverviewTitle"),
              overallStatus: tr("researchValOverallStatus"),
              completed: tr("researchValCompleted"),
              passed: tr("researchValPassed"),
              failed: tr("researchValFailed"),
              inconclusive: tr("researchValInconclusive"),
              blocking: tr("researchValBlocking"),
              lastValidation: tr("researchValLastDate"),
              readiness: tr("researchValReadiness"),
              readinessNote: tr("researchValReadinessNote"),
            },
            blockers: {
              title: tr("researchValBlockersTitle"),
              description: tr("researchValBlockersDescription"),
              severity: tr("researchValGateSeverity"),
              reason: tr("researchValBlockerReason"),
              stage: tr("researchValBlockerStage"),
              nextAction: tr("researchValBlockerNext"),
              empty: tr("researchValBlockersEmpty"),
              inspect: tr("researchValInspect"),
            },
            filters: {
              search: tr("researchValSearch"),
              searchPlaceholder: tr("researchValSearchPlaceholder"),
              status: tr("researchValFilterStatus"),
              all: tr("researchValFilterAll"),
            },
            pipeline: {
              title: tr("researchValPipelineTitle"),
              card: {
                purpose: tr("researchValCardPurpose"),
                lastRun: tr("researchValCardLastRun"),
                owner: tr("researchValCardOwner"),
                evidence: tr("researchValCardEvidence"),
                keyResult: tr("researchValCardKeyResult"),
                warnings: tr("researchValCardWarnings"),
                nextAction: tr("researchValCardNext"),
                openDetail: tr("researchValOpenDetail"),
              },
            },
            detail: {
              title: tr("researchValDetailTitle"),
              close: tr("researchValDetailClose"),
              purpose: tr("researchValPurpose"),
              method: tr("researchValMethod"),
              dataset: tr("researchValDataset"),
              dateRange: tr("researchValDateRange"),
              benchmark: tr("researchValBenchmark"),
              successCriteria: tr("researchValSuccess"),
              falsificationCriteria: tr("researchValFalsify"),
              result: tr("researchValResult"),
              dataConfidence: tr("researchValDataConfidence"),
              limitations: tr("researchValLimitations"),
              warnings: tr("researchValWarnings"),
              recommendation: tr("researchValRecommendation"),
              runHistory: tr("researchValRunHistory"),
              owner: tr("researchListOwner"),
              lastRun: tr("researchValCardLastRun"),
              nextAction: tr("researchValNextAction"),
              none: tr("researchValNone"),
              evidenceTitle: tr("researchValEvidenceTitle"),
              evidenceEmpty: tr("researchValEvidenceEmpty"),
              gates: {
                title: tr("researchValGatesTitle"),
                rule: tr("researchValGateRule"),
                threshold: tr("researchValGateThreshold"),
                observed: tr("researchValGateObserved"),
                result: tr("researchValGateResult"),
                severity: tr("researchValGateSeverity"),
                evidence: tr("researchValGateEvidence"),
                pass: tr("researchValGatePass"),
                fail: tr("researchValGateFail"),
                empty: tr("researchValGatesEmpty"),
                deterministicNote: tr("researchValGatesNote"),
              },
              metrics: {
                title: tr("researchValMetricsTitle"),
                disclaimer: tr("researchValMetricsDisclaimer"),
                historical: tr("researchValMetricHistorical"),
                simulated: tr("researchValMetricSimulated"),
              },
            },
          }}
        />
      );
    }

    if (activeSection === "evaluation") {
      return (
        <ResearchEvaluation
          research={research}
          language={language}
          labels={{
            title: tr("researchEvalTitle"),
            loading: tr("researchEvalLoading"),
            errorTitle: tr("researchEvalErrorTitle"),
            retry: tr("researchEvalRetry"),
            emptyTitle: tr("researchEvalEmptyTitle"),
            emptyDescription: tr("researchEvalEmptyDescription"),
            filterEmptyTitle: tr("researchEvalFilterEmptyTitle"),
            filterEmptyDescription: tr("researchEvalFilterEmptyDescription"),
            missingValidationTitle: tr("researchEvalMissingValidationTitle"),
            missingValidationDescription: tr(
              "researchEvalMissingValidationDescription"
            ),
            requestReview: tr("researchEvalRequestReview"),
            requestReviewHint: tr("researchEvalRequestReviewHint"),
            demoLoading: tr("researchEvalDemoLoading"),
            demoError: tr("researchEvalDemoError"),
            dimensionsTitle: tr("researchEvalDimensionsTitle"),
            overview: {
              title: tr("researchEvalOverviewTitle"),
              confidence: {
                title: tr("researchEvalConfidenceTitle"),
                score: tr("researchEvalConfidenceScore"),
                level: tr("researchEvalConfidenceLevel"),
                disclaimer: tr("researchEvalConfidenceDisclaimer"),
                demoLabel: tr("researchEvalDemoLabel"),
              },
              researchHealth: tr("researchEvalResearchHealth"),
              decisionReadiness: tr("researchEvalDecisionReadiness"),
              recommendation: tr("researchEvalRecommendation"),
              evaluationStatus: tr("researchEvalStatus"),
              lastEvaluated: tr("researchEvalLastEvaluated"),
              lifecycleStage: tr("researchEvalLifecycle"),
              dataConfidence: tr("researchEvalDataConfidence"),
              blockers: tr("researchEvalBlockerCount"),
              evidenceCoverage: tr("researchEvalEvidenceCoverage"),
            },
            breakdown: {
              title: tr("researchEvalBreakdownTitle"),
              formula: tr("researchEvalBreakdownFormula"),
              dimension: tr("researchEvalBreakdownDimension"),
              score: tr("researchEvalBreakdownScore"),
              weight: tr("researchEvalBreakdownWeight"),
              contribution: tr("researchEvalBreakdownContribution"),
              status: tr("researchEvalBreakdownStatus"),
              total: tr("researchEvalBreakdownTotal"),
              weightsTotal: tr("researchEvalBreakdownWeightsTotal"),
            },
            readiness: {
              title: tr("researchEvalReadinessTitle"),
              description: tr("researchEvalReadinessDescription"),
              rule: tr("researchEvalReadinessRule"),
              observed: tr("researchEvalReadinessObserved"),
              result: tr("researchEvalReadinessResult"),
              pass: tr("researchEvalPass"),
              fail: tr("researchEvalFail"),
            },
            blockers: {
              blockersTitle: tr("researchEvalCriticalBlockers"),
              warningsTitle: tr("researchEvalWarnings"),
              missingTitle: tr("researchEvalMissingEvidence"),
              severity: tr("researchEvalSeverity"),
              source: tr("researchEvalSource"),
              reason: tr("researchEvalReason"),
              evidence: tr("researchEvalEvidence"),
              nextAction: tr("researchEvalNextAction"),
              owner: tr("researchListOwner"),
              due: tr("researchEvalDue"),
              emptyBlockers: tr("researchEvalEmptyBlockers"),
              emptyWarnings: tr("researchEvalEmptyWarnings"),
              emptyMissing: tr("researchEvalEmptyMissing"),
            },
            strengthsWeaknesses: {
              title: tr("researchEvalSWTitle"),
              strengths: tr("researchEvalStrengths"),
              weaknesses: tr("researchEvalWeaknesses"),
              empty: tr("researchEvalSWEmpty"),
            },
            recommendation: {
              title: tr("researchEvalRecPanelTitle"),
              current: tr("researchEvalRecCurrent"),
              why: tr("researchEvalRecWhy"),
              blocking: tr("researchEvalRecBlocking"),
              nextActions: tr("researchEvalRecNext"),
              transition: tr("researchEvalRecTransition"),
              owner: tr("researchEvalRecOwner"),
              reassessment: tr("researchEvalRecReassessment"),
              none: tr("researchEvalNone"),
            },
            history: {
              title: tr("researchEvalHistoryTitle"),
              date: tr("researchEvalHistoryDate"),
              score: tr("researchEvalHistoryScore"),
              recommendation: tr("researchEvalHistoryRec"),
              change: tr("researchEvalHistoryChange"),
              trigger: tr("researchEvalHistoryTrigger"),
              superseded: tr("researchEvalHistorySuperseded"),
              active: tr("researchEvalHistoryActive"),
              empty: tr("researchEvalHistoryEmpty"),
            },
            filters: {
              search: tr("researchEvalSearch"),
              searchPlaceholder: tr("researchEvalSearchPlaceholder"),
              status: tr("researchEvalFilterStatus"),
              all: tr("researchEvalFilterAll"),
            },
            dimensionCard: {
              score: tr("researchEvalBreakdownScore"),
              weight: tr("researchEvalBreakdownWeight"),
              contribution: tr("researchEvalBreakdownContribution"),
              evidence: tr("researchEvalEvidence"),
              evidenceEmpty: tr("researchEvalEvidenceEmpty"),
              limitations: tr("researchEvalLimitations"),
              blocking: tr("researchEvalBlockingFlag"),
              blockingYes: tr("researchEvalBlockingYes"),
              blockingNo: tr("researchEvalBlockingNo"),
              lastUpdated: tr("researchEvalLastUpdated"),
              expand: tr("researchEvalExpand"),
              collapse: tr("researchEvalCollapse"),
              none: tr("researchEvalNone"),
            },
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

        {loadStatus === "ready" && research ? (
          <div className="research-workspace">
            <ResearchWorkspaceHeader
              research={research}
              language={language}
              labels={{
                back: tr("researchWsBackToList"),
                moreActions: tr("researchWsMoreActions"),
                moreActionsHint: tr("researchWsMoreActionsHint"),
                owner: tr("researchListOwner"),
                created: tr("researchWsCreated"),
                updated: tr("researchListUpdated"),
                recommendation: tr("researchListRecommendation"),
                confidence: tr("researchListConfidence"),
                tags: tr("researchWsTags"),
              }}
            />

            <ResearchWorkspaceNavigation
              researchId={research.id}
              activeSection={activeSection}
              labels={navLabels}
            />

            <div className="research-workspace__layout">
              <div className="research-workspace__main">
                {renderMainSection()}

                {showEvidencePreview ? (
                  <div className="research-workspace__placeholder-evidence">
                    <EvidenceSummary
                      items={research.evidenceItems.slice(0, 3)}
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
