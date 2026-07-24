"use client";

import type { Dispatch, SetStateAction } from "react";
import Button from "@/components/ui/Button";
import ErrorAlert from "@/components/ui/ErrorAlert";
import LoadingState from "@/components/ui/LoadingState";
import type { Language, TranslationKey } from "@/lib/i18n";
import type { ResearchExperiment } from "@/types/experiment";
import type { NotebookEntry, ResearchTimelineEvent } from "@/types/notebook";
import type { ResearchDetail, ResearchWorkspaceSection } from "@/types/research";
import ProvenanceBanner, {
  type ProvenanceBannerLabels,
} from "@/components/features/research/execution/ProvenanceBanner";
import type {
  ResearchExecutionResult,
  ResearchExecutionStatus,
} from "@/types/researchExecution";
import type {
  ResearchValidationResult,
  ResearchValidationStatus,
} from "@/types/researchValidation";
import type {
  ResearchEvaluationResult,
  ResearchEvaluationRequestStatus,
} from "@/types/researchEvaluation";
import type {
  ResearchCopilotRequestStatus,
  ResearchCopilotResult,
} from "@/types/researchCopilot";
import OverviewTab from "./OverviewTab";
import EvidenceTab from "./EvidenceTab";
import DecisionTab from "./DecisionTab";
import NotebookTab from "./NotebookTab";

export type ResearchWorkspaceMainSectionProps = {
  researchId: string;
  activeSection: ResearchWorkspaceSection;
  displayResearch: ResearchDetail;
  research: ResearchDetail | null;
  language: Language;
  tr: (key: TranslationKey) => string;
  provenanceLabels: ProvenanceBannerLabels;
  executionEnabled: boolean;
  executionStatus: ResearchExecutionStatus;
  execution: ResearchExecutionResult | null;
  executionError: string | null;
  reloadExecution: () => void;
  formatMetric: (value: number | null, kind: "pct" | "num" | "raw") => string;
  navigateToSection: (section: ResearchWorkspaceSection) => void;
  handleRunValidation: () => void;
  validationEnabled: boolean;
  validationStatus: ResearchValidationStatus;
  validation: ResearchValidationResult | null;
  validationError: string | null;
  reloadValidation: () => void;
  evaluationEnabled: boolean;
  evaluationStatus: ResearchEvaluationRequestStatus;
  evaluation: ResearchEvaluationResult | null;
  evaluationError: string | null;
  reloadEvaluation: () => void;
  sessionNotebookEntries: NotebookEntry[];
  handleSessionEntrySaved: (
    entry: NotebookEntry,
    timelineEvent: ResearchTimelineEvent
  ) => void;
  sessionExperiments: ResearchExperiment[];
  selectedExperimentId: string | null;
  setSelectedExperimentId: Dispatch<SetStateAction<string | null>>;
  handleExperimentDesigned: (payload: {
    experiment: ResearchExperiment;
    notebookEntry: NotebookEntry;
    timelineEvent: ResearchTimelineEvent;
  }) => void;
  executedExperiments: ResearchExperiment[] | null;
  timelineEvents: ResearchTimelineEvent[];
  validationEvidenceActive: boolean;
  copilotEnabled: boolean;
  copilotStatus: ResearchCopilotRequestStatus;
  copilotResult: ResearchCopilotResult | null;
  copilotError: string | null;
  copilotQuestion: string;
  setCopilotQuestion: (value: string) => void;
  askCopilot: (question: string) => void | Promise<void>;
  copilotSampleQuestions: string[];
};

/**
 * Tab content router — pure extract from ResearchWorkspacePage.
 * Parent owns data loading and workspace chrome.
 */
export default function ResearchWorkspaceMainSection(
  props: ResearchWorkspaceMainSectionProps
) {
  const {
    researchId,
    activeSection,
    displayResearch,
    research,
    language,
    tr,
    provenanceLabels,
    executionEnabled,
    executionStatus,
    execution,
    executionError,
    reloadExecution,
    navigateToSection,
    handleRunValidation,
    validationEnabled,
    validationStatus,
    validation,
    validationError,
    reloadValidation,
    evaluationEnabled,
    evaluationStatus,
    evaluation,
    evaluationError,
    reloadEvaluation,
    sessionNotebookEntries,
    handleSessionEntrySaved,
    sessionExperiments,
    selectedExperimentId,
    setSelectedExperimentId,
    handleExperimentDesigned,
    executedExperiments,
    timelineEvents,
    validationEvidenceActive,
    copilotEnabled,
    copilotStatus,
    copilotResult,
    copilotError,
    copilotQuestion,
    setCopilotQuestion,
    askCopilot,
    copilotSampleQuestions,
  } = props;

  if (!displayResearch) {
    return null;
  }

  const provenanceSlot =
    executionEnabled && executionStatus === "ready" && execution ? (
      <ProvenanceBanner
        provenance={execution.provenance}
        labels={provenanceLabels}
        warnings={execution.warnings}
        language={language}
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

  if (activeSection === "overview") {
    return (
      <OverviewTab
        language={language}
        tr={tr}
        displayResearch={displayResearch}
        provenanceSlot={provenanceSlot}
        executionStatus={executionStatus}
        execution={execution}
        validationStatus={validationStatus}
        validation={validation}
        evaluationStatus={evaluationStatus}
        evaluation={evaluation}
        reloadExecution={reloadExecution}
        handleRunValidation={handleRunValidation}
        navigateToSection={navigateToSection}
      />
    );
  }

  if (
    activeSection === "experiments" ||
    activeSection === "validation" ||
    activeSection === "evaluation" ||
    activeSection === "robustness"
  ) {
    return (
      <EvidenceTab
        section={activeSection}
        researchId={researchId}
        language={language}
        tr={tr}
        displayResearch={displayResearch}
        provenanceSlot={provenanceSlot}
        navigateToSection={navigateToSection}
        sessionExperiments={sessionExperiments}
        selectedExperimentId={selectedExperimentId}
        setSelectedExperimentId={setSelectedExperimentId}
        handleExperimentDesigned={handleExperimentDesigned}
        executedExperiments={executedExperiments}
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
      />
    );
  }

  if (
    activeSection === "paper" ||
    activeSection === "decision"
  ) {
    return (
      <DecisionTab
        section={activeSection}
        language={language}
        tr={tr}
        research={research}
        validationStatus={validationStatus}
        validation={validation}
        evaluationStatus={evaluationStatus}
        evaluation={evaluation}
        navigateToSection={navigateToSection}
      />
    );
  }

  if (
    activeSection === "notebook" ||
    activeSection === "timeline" ||
    activeSection === "copilot"
  ) {
    return (
      <NotebookTab
        section={activeSection}
        researchId={researchId}
        language={language}
        tr={tr}
        displayResearch={displayResearch}
        sessionNotebookEntries={sessionNotebookEntries}
        handleSessionEntrySaved={handleSessionEntrySaved}
        timelineEvents={timelineEvents}
        copilotEnabled={copilotEnabled}
        copilotStatus={copilotStatus}
        copilotResult={copilotResult}
        copilotError={copilotError}
        copilotQuestion={copilotQuestion}
        setCopilotQuestion={setCopilotQuestion}
        askCopilot={askCopilot}
        copilotSampleQuestions={copilotSampleQuestions}
        validationEvidenceActive={validationEvidenceActive}
        validationStatus={validationStatus}
        validationError={validationError}
        evaluationEnabled={evaluationEnabled}
        evaluationStatus={evaluationStatus}
        evaluation={evaluation}
        evaluationError={evaluationError}
        reloadEvaluation={reloadEvaluation}
      />
    );
  }

  return null;
}
