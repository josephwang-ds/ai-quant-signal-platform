import type { ReactNode } from "react";
import GuidedResearchFlow, {
  type GuidedResearchFlowLabels,
} from "@/components/features/research/GuidedResearchFlow";
import KeyResultsSummary, {
  type KeyResultsSummaryLabels,
} from "@/components/features/research/KeyResultsSummary";
import NextStepPanel, {
  type NextStepPanelLabels,
} from "@/components/features/research/NextStepPanel";
import ResearchBrief, {
  type ResearchBriefLabels,
} from "@/components/features/research/ResearchBrief";
import ResearchConclusion, {
  type ResearchConclusionLabels,
} from "@/components/features/research/ResearchConclusion";
import type { Language } from "@/lib/i18n";
import {
  derivePrimaryWorkflowStep,
  deriveWorkflowPrimaryAction,
  deriveWorkflowStepStates,
  evaluationReady,
  executionReady,
  validationReady,
} from "@/lib/researchWorkflow";
import type { ResearchDetail } from "@/types/research";
import type { ResearchExecutionResult, ResearchExecutionStatus } from "@/types/researchExecution";
import type {
  ResearchEvaluationResult,
  ResearchEvaluationRequestStatus,
} from "@/types/researchEvaluation";
import type { ResearchValidationResult, ResearchValidationStatus } from "@/types/researchValidation";

export type OverviewSectionLabels = {
  briefTitle: string;
  keyResultsTitle: string;
  guidedWorkflowTitle: string;
  conclusionTitle: string;
  evidencePreviewTitle: string;
  brief: ResearchBriefLabels;
  keyResults: KeyResultsSummaryLabels;
  guidedFlow: GuidedResearchFlowLabels;
  nextStep: NextStepPanelLabels;
  conclusion: ResearchConclusionLabels;
};

export type OverviewSectionProps = {
  language: Language;
  research: ResearchDetail;
  executionStatus: ResearchExecutionStatus;
  execution: ResearchExecutionResult | null;
  validationStatus: ResearchValidationStatus;
  validation: ResearchValidationResult | null;
  evaluationStatus: ResearchEvaluationRequestStatus;
  evaluation: ResearchEvaluationResult | null;
  onRunResearch: () => void;
  onRunValidation: () => void;
  onRequestEvaluation: () => void;
  onAskCopilot: () => void;
  labels: OverviewSectionLabels;
  provenanceSlot?: ReactNode;
};

export default function OverviewSection({
  language,
  research,
  executionStatus,
  execution,
  validationStatus,
  validation,
  evaluationStatus,
  evaluation,
  onRunResearch,
  onRunValidation,
  onRequestEvaluation,
  onAskCopilot,
  labels,
  provenanceSlot = null,
}: OverviewSectionProps) {
  const workflowInput = {
    executionStatus,
    execution,
    validationStatus,
    validation,
    evaluationStatus,
    evaluation,
  };

  const primaryStep = derivePrimaryWorkflowStep(workflowInput);
  const stepStates = deriveWorkflowStepStates(workflowInput);
  const primaryAction = deriveWorkflowPrimaryAction(workflowInput);

  const evidenceComplete = Boolean(validation?.evidence_complete);
  const evidenceStatusValue = validationReady(validationStatus, validation)
    ? evidenceComplete
      ? labels.brief.evidenceComplete
      : labels.brief.evidenceIncomplete
    : labels.brief.evidencePending;

  const decisionStatusValue = (() => {
    if (!evaluationReady(evaluationStatus, evaluation) || !evaluation) {
      return labels.brief.decisionPending;
    }
    if (evaluation.evaluation_status === "completed") {
      return labels.brief.evaluationCompleted;
    }
    if (evaluation.evaluation_status === "blocked") {
      return labels.brief.evaluationBlocked;
    }
    return labels.brief.evaluationIncomplete;
  })();

  return (
    <div className="overview-narrative">
      <section className="overview-block" aria-label={labels.briefTitle}>
        <h3 className="overview-block__title">{labels.briefTitle}</h3>
        <ResearchBrief
          research={research}
          language={language}
          execution={executionReady(executionStatus, execution) ? execution : null}
          evidenceStatusValue={evidenceStatusValue}
          decisionStatusValue={decisionStatusValue}
          labels={labels.brief}
          showIdentity={false}
        />
      </section>

      <section className="overview-block" aria-label={labels.keyResultsTitle}>
        <h3 className="overview-block__title">{labels.keyResultsTitle}</h3>
        <KeyResultsSummary
          execution={executionReady(executionStatus, execution) ? execution : null}
          validation={validationReady(validationStatus, validation) ? validation : null}
          labels={labels.keyResults}
        />
      </section>

      <ResearchConclusion
        language={language}
        evaluation={evaluation}
        evaluationReady={evaluationReady(evaluationStatus, evaluation)}
        labels={labels.conclusion}
      />

      <GuidedResearchFlow
        stepStates={stepStates}
        primaryStep={primaryStep}
        labels={{
          ...labels.guidedFlow,
          title: labels.guidedWorkflowTitle,
        }}
      />

      <NextStepPanel
        step={primaryAction.step}
        disabled={primaryAction.disabled}
        executionFailed={executionStatus === "error"}
        labels={labels.nextStep}
        onRunResearch={onRunResearch}
        onRunValidation={onRunValidation}
        onRequestEvaluation={onRequestEvaluation}
        onAskCopilot={onAskCopilot}
      />

      {provenanceSlot ? (
        <details className="overview-evidence-preview">
          <summary>{labels.evidencePreviewTitle}</summary>
          <div className="overview-provenance">{provenanceSlot}</div>
        </details>
      ) : null}
    </div>
  );
}
