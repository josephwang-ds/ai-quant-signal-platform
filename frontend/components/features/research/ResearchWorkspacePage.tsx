"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import AppShell from "@/components/layout/AppShell";
import ResearchSummaryRail from "@/components/features/research/ResearchSummaryRail";
import ResearchWorkspaceHeader from "@/components/features/research/ResearchWorkspaceHeader";
import ResearchWorkspaceSkeleton from "@/components/features/research/ResearchWorkspaceSkeleton";
import ResearchPrimaryTabs from "@/components/features/research/ResearchPrimaryTabs";
import DeleteResearchModal from "@/components/features/research/DeleteResearchModal";
import ResearchWorkspaceMainSection from "@/components/features/research/workspace-tabs/ResearchWorkspaceMainSection";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import ErrorAlert from "@/components/ui/ErrorAlert";
import LoadingState from "@/components/ui/LoadingState";
import SectionCard from "@/components/ui/SectionCard";
import { getMockTimelineEvents } from "@/lib/mockNotebookCatalog";
import { getResearchRepository } from "@/lib/localResearchRepository";
import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";
import { mergeTimelineEvents } from "@/lib/researchNotebook";
import { resolveWorkspaceSection } from "@/lib/researchWorkspace";
import {
  derivePrimaryWorkflowStep,
  deriveWorkflowStepStates,
} from "@/lib/researchWorkflow";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";
import type { ResearchExperiment } from "@/types/experiment";
import type { NotebookEntry, ResearchTimelineEvent } from "@/types/notebook";
import type {
  ResearchDetail,
  ResearchWorkspaceSection,
} from "@/types/research";
import { useResearchExecution } from "@/components/features/research/execution/useResearchExecution";
import { useResearchValidation } from "@/components/features/research/validation/useResearchValidation";
import { useResearchEvaluation } from "@/components/features/research/evaluation/useResearchEvaluation";
import { useResearchCopilot } from "@/components/features/research/copilot/useResearchCopilot";
import {
  applyExecutionToExperiments,
  applyExecutionToResearch,
} from "@/lib/applyResearchExecution";
import { getMockExperiments } from "@/lib/mockExperimentCatalog";
import { METRIC_NOT_CALCULATED } from "@/lib/researchExperiments";
import {
  formatMetricPercent,
  formatMetricSharpe,
  formatMetricTrades,
} from "@/lib/formatters";
import {
  canRequestEvaluation,
  shouldReloadEvaluationOnAction,
  shouldReloadValidationOnAction,
} from "@/lib/workspaceActionTriggers";

type LoadStatus = "loading" | "ready" | "error" | "not_found";

export type ResearchWorkspacePageProps = {
  researchId: string;
};

/**
 * Research Workspace Detail — data orchestration + chrome.
 * Tab bodies live under workspace-tabs/.
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
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deletingResearch, setDeletingResearch] = useState(false);

  const [validationUnlocked, setValidationUnlocked] = useState(false);
  const [evaluationUnlocked, setEvaluationUnlocked] = useState(false);

  const {
    enabled: executionEnabled,
    status: executionStatus,
    execution,
    error: executionError,
    reload: reloadExecution,
  } = useResearchExecution(researchId, research?.runConfiguration);
  const validationEvidenceActive =
    activeSection === "validation" ||
    activeSection === "robustness" ||
    activeSection === "paper" ||
    activeSection === "decision" ||
    validationUnlocked;
  const {
    enabled: validationEnabled,
    status: validationStatus,
    validation,
    error: validationError,
    reload: reloadValidation,
  } = useResearchValidation(
    researchId,
    validationEvidenceActive,
    research?.runConfiguration
  );
  const validationRunId = validation?.validation_run_id ?? null;
  useEffect(() => {
    if (!validationRunId) return;
    if (validationStatus !== "ready") return;
    setValidationUnlocked(true);
  }, [validationRunId, validationStatus]);

  const evaluationRequestActive =
    activeSection === "validation" ||
    activeSection === "evaluation" ||
    activeSection === "robustness" ||
    activeSection === "paper" ||
    activeSection === "decision" ||
    activeSection === "copilot" ||
    evaluationUnlocked;
  const {
    enabled: evaluationEnabled,
    status: evaluationStatus,
    evaluation,
    error: evaluationError,
    reload: reloadEvaluation,
  } = useResearchEvaluation(
    researchId,
    evaluationRequestActive,
    validationRunId
  );

  useEffect(() => {
    if (!evaluation) return;
    if (evaluationStatus !== "ready") return;
    setEvaluationUnlocked(true);
  }, [evaluation, evaluationStatus]);
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
    navigateToSection("validation");
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

  const workflowInput = useMemo(
    () => ({
      executionStatus,
      execution,
      validationStatus,
      validation,
      evaluationStatus,
      evaluation,
      researchStatus: displayResearch?.status,
    }),
    [
      displayResearch?.status,
      evaluation,
      evaluationStatus,
      execution,
      executionStatus,
      validation,
      validationStatus,
    ]
  );

  const workflowStepStates = useMemo(
    () => deriveWorkflowStepStates(workflowInput),
    [workflowInput]
  );

  const summaryNextMilestone = useMemo(() => {
    if (evaluationStatus === "ready" && evaluation) {
      if (evaluation.blockers[0]) return evaluation.blockers[0];
      if (evaluation.outstanding_evidence[0]) return evaluation.outstanding_evidence[0];
    }
    const step = derivePrimaryWorkflowStep(workflowInput);
    if (step === "research") return tr("researchWsNextStepRunResearchTitle");
    if (step === "validation") return tr("researchWsNextStepValidateTitle");
    if (step === "robustness") return tr("researchWsNextStepOpenRobustnessTitle");
    if (step === "paper") return tr("researchWsNextStepOpenPaperTitle");
    if (step === "decision") return tr("researchWsNextStepOpenDecisionTitle");
    if (step === "archive") return tr("researchWsNextStepOpenArchiveTitle");
    return tr("researchWsNextStepOpenExperimentTitle");
  }, [evaluation, evaluationStatus, tr, workflowInput]);

  const executedExperiments = useMemo(() => {
    if (!executionEnabled || executionStatus !== "ready" || !execution) {
      return null;
    }
    return applyExecutionToExperiments(getMockExperiments(researchId), execution);
  }, [execution, executionEnabled, executionStatus, researchId]);

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
      dataNotes: tr("researchValDataNotes"),
    }),
    [tr]
  );

  function formatMetric(value: number | null, kind: "pct" | "num" | "raw"): string {
    if (value === null || Number.isNaN(value)) {
      return METRIC_NOT_CALCULATED;
    }
    if (kind === "pct") {
      return formatMetricPercent(value);
    }
    if (kind === "num") {
      return formatMetricSharpe(value);
    }
    return formatMetricTrades(value);
  }

  const loadDetail = useCallback(async () => {
    setLoadStatus("loading");
    setLoadError(null);
    try {
      const data = await getResearchRepository().getById(researchId);
      if (!data) {
        setResearch(null);
        setLoadStatus("not_found");
        return;
      }
      setResearch(data);
      setLoadStatus("ready");
    } catch {
      setResearch(null);
      setLoadError("The research workspace could not be loaded. Please retry.");
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
    ],
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

  async function handleDeleteResearch() {
    if (researchId === CANONICAL_RESEARCH_ID) return;
    setDeletingResearch(true);
    try {
      await getResearchRepository().deletePermanently(researchId);
      setDeleteModalOpen(false);
      router.replace("/");
    } finally {
      setDeletingResearch(false);
    }
  }

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <SectionCard className="research-workspace-shell-card">
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
              execution={executionStatus === "ready" ? execution : null}
              labels={{
                back: tr("researchWsBackToList"),
                moreActions: tr("researchWsMoreActions"),
                moreActionsHint: tr("researchWsMoreActionsHint"),
                deleteResearch: tr("researchListDelete"),
                owner: tr("researchListOwner"),
                created: tr("researchWsCreated"),
                updated: tr("researchListUpdated"),
                recommendation: tr("researchListRecommendation"),
                confidence: tr("researchListEvaluationArea"),
                tags: tr("researchWsTags"),
                benchmark: tr("researchListBenchmark"),
                experiment: tr("researchWsHeroExperiment"),
                experimentNotConfigured: tr("researchWsExperimentNotConfigured"),
              }}
              onDeleteResearch={
                displayResearch.id === CANONICAL_RESEARCH_ID
                  ? undefined
                  : () => setDeleteModalOpen(true)
              }
            />

            <div className="research-workspace__layout">
              <div className="research-workspace__main">
                <div
                  className="research-workspace__section-switcher"
                  role="navigation"
                  aria-label="Research workspace sections"
                >
                  <ResearchPrimaryTabs
                    researchId={displayResearch.id}
                    activeSection={activeSection}
                    stepStates={workflowStepStates}
                    labels={{
                      overview: tr("researchWsNavOverview"),
                      experiments: tr("researchWsNavExperiments"),
                      validation: tr("researchWsNavValidation"),
                      robustness: tr("researchWsNavRobustness"),
                      paper: tr("researchWsNavPaper"),
                      decision: tr("researchWsNavDecision"),
                      archive: tr("researchWsNavArchive"),
                      progressCompleted: tr("researchWsTabCompleted"),
                      progressCurrent: tr("researchWsTabCurrent"),
                      progressLocked: tr("researchWsTabLocked"),
                    }}
                  />

                  <details className="research-workspace__more-menu">
                    <summary>{tr("researchListMore")}</summary>
                    <ul className="research-workspace__more-menu-list">
                      <li>
                        <Link
                          href={`/research/${encodeURIComponent(
                            displayResearch.id
                          )}?tab=notebook`}
                        >
                          {tr("researchWsNavNotebook")}
                        </Link>
                      </li>
                      <li>
                        <Link
                          href={`/research/${encodeURIComponent(
                            displayResearch.id
                          )}?tab=timeline`}
                        >
                          {tr("researchWsNavTimeline")}
                        </Link>
                      </li>
                      <li>
                        <Link
                          href={`/research/${encodeURIComponent(
                            displayResearch.id
                          )}?tab=files`}
                        >
                          {tr("researchWsNavFiles")}
                        </Link>
                      </li>
                      <li>
                        <Link
                          href={`/research/${encodeURIComponent(
                            displayResearch.id
                          )}?tab=settings`}
                        >
                          {tr("researchWsNavSettings")}
                        </Link>
                      </li>
                    </ul>
                  </details>
                </div>

                <ResearchWorkspaceMainSection
                  researchId={researchId}
                  activeSection={activeSection}
                  displayResearch={displayResearch}
                  research={research}
                  language={language}
                  tr={tr}
                  provenanceLabels={provenanceLabels}
                  executionEnabled={executionEnabled}
                  executionStatus={executionStatus}
                  execution={execution}
                  executionError={executionError}
                  reloadExecution={reloadExecution}
                  formatMetric={formatMetric}
                  navigateToSection={navigateToSection}
                  handleRunValidation={handleRunValidation}
                  validationEnabled={validationEnabled}
                  validationStatus={validationStatus}
                  validation={validation}
                  validationError={validationError}
                  reloadValidation={reloadValidation}
                  evaluationEnabled={evaluationEnabled}
                  evaluationStatus={evaluationStatus}
                  evaluation={evaluation}
                  evaluationError={evaluationError}
                  reloadEvaluation={reloadEvaluation}
                  sessionNotebookEntries={sessionNotebookEntries}
                  handleSessionEntrySaved={handleSessionEntrySaved}
                  sessionExperiments={sessionExperiments}
                  selectedExperimentId={selectedExperimentId}
                  setSelectedExperimentId={setSelectedExperimentId}
                  handleExperimentDesigned={handleExperimentDesigned}
                  executedExperiments={executedExperiments}
                  timelineEvents={timelineEvents}
                  validationEvidenceActive={validationEvidenceActive}
                  copilotEnabled={copilotEnabled}
                  copilotStatus={copilotStatus}
                  copilotResult={copilotResult}
                  copilotError={copilotError}
                  copilotQuestion={copilotQuestion}
                  setCopilotQuestion={setCopilotQuestion}
                  askCopilot={askCopilot}
                  copilotSampleQuestions={copilotSampleQuestions}
                />
              </div>

              <ResearchSummaryRail
                research={displayResearch}
                language={language}
                execution={executionStatus === "ready" ? execution : null}
                nextMilestone={summaryNextMilestone}
                labels={{
                  title: tr("researchSummaryTitle"),
                  status: tr("researchSummaryStatus"),
                  nextMilestone: tr("researchSummaryNextMilestone"),
                  experiment: tr("researchWsHeroExperiment"),
                  benchmark: tr("researchListBenchmark"),
                  updated: tr("researchListUpdated"),
                  noMilestone: tr("researchSummaryNoMilestone"),
                  experimentNotConfigured: tr("researchWsExperimentNotConfigured"),
                }}
              />
            </div>
          </div>
        ) : null}
      </SectionCard>
      <DeleteResearchModal
        open={deleteModalOpen}
        researchName={displayResearch?.name ?? ""}
        busy={deletingResearch}
        onClose={() => {
          if (!deletingResearch) setDeleteModalOpen(false);
        }}
        onConfirm={handleDeleteResearch}
        labels={{
          title: tr("researchListDeleteTitle"),
          description: tr("researchListDeleteDescription"),
          irreversible: tr("researchListDeleteIrreversible"),
          confirm: tr("researchListDeleteConfirm"),
          cancel: tr("researchListDeleteCancel"),
          deleting: tr("researchListDeleting"),
        }}
      />
    </AppShell>
  );
}
