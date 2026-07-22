import ResearchKeyValueList from "@/components/features/research/ux/ResearchKeyValueList";
import type { ReactNode } from "react";
import KeyResultsSummary, {
  type KeyResultsSummaryLabels,
} from "@/components/features/research/KeyResultsSummary";
import NextStepPanel, {
  type NextStepPanelLabels,
} from "@/components/features/research/NextStepPanel";
import ResearchConclusion, {
  type ResearchConclusionLabels,
} from "@/components/features/research/ResearchConclusion";
import ResearchGlyph, {
  type ResearchGlyphName,
} from "@/components/features/research/ResearchGlyph";
import type { Language } from "@/lib/i18n";
import {
  deriveWorkflowPrimaryAction,
  evaluationReady,
  executionReady,
  validationReady,
} from "@/lib/researchWorkflow";
import type { ResearchDetail, ResearchWorkspaceSection } from "@/types/research";
import type { ResearchExecutionResult, ResearchExecutionStatus } from "@/types/researchExecution";
import type {
  ResearchEvaluationResult,
  ResearchEvaluationRequestStatus,
} from "@/types/researchEvaluation";
import type { ResearchValidationResult, ResearchValidationStatus } from "@/types/researchValidation";

export type OverviewSectionLabels = {
  keyResultsTitle: string;
  conclusionTitle: string;
  evidencePreviewTitle: string;
  primaryActionCaption: string;
  validationCaption: string;
  decisionCaption: string;
  supportCaption: string;
  keyResults: KeyResultsSummaryLabels;
  nextStep: NextStepPanelLabels;
  validationStatus: string;
  decisionStatus: string;
  validationComplete: string;
  validationIncomplete: string;
  validationPending: string;
  decisionPending: string;
  evaluationCompleted: string;
  evaluationIncomplete: string;
  evaluationBlocked: string;
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
  onOpenSection: (section: ResearchWorkspaceSection) => void;
  labels: OverviewSectionLabels;
  provenanceSlot?: ReactNode;
};

function SectionCaption({
  glyph,
  children,
}: {
  glyph: ResearchGlyphName;
  children: ReactNode;
}) {
  return (
    <p className="overview-caption">
      <ResearchGlyph name={glyph} />
      <span>{children}</span>
    </p>
  );
}

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
  onOpenSection,
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
    researchStatus: research.status,
  };

  const primaryAction = deriveWorkflowPrimaryAction(workflowInput);

  const validationComplete = Boolean(validation?.evidence_complete);
  const validationStatusValue = validationReady(validationStatus, validation)
    ? validationComplete
      ? labels.validationComplete
      : labels.validationIncomplete
    : labels.validationPending;

  const decisionStatusValue = (() => {
    if (!evaluationReady(evaluationStatus, evaluation) || !evaluation) {
      return labels.decisionPending;
    }
    if (evaluation.evaluation_status === "completed") {
      return labels.evaluationCompleted;
    }
    if (evaluation.evaluation_status === "blocked") {
      return labels.evaluationBlocked;
    }
    return labels.evaluationIncomplete;
  })();

  const showDecision = evaluationReady(evaluationStatus, evaluation);

  return (
    <div className="overview-narrative" data-research-id={research.id}>
      <section className="overview-band overview-band--action" aria-label={labels.primaryActionCaption}>
        <SectionCaption glyph="action">{labels.primaryActionCaption}</SectionCaption>
        <NextStepPanel
          step={primaryAction.step}
          disabled={primaryAction.disabled}
          executionFailed={executionStatus === "error"}
          labels={labels.nextStep}
          onRunResearch={onRunResearch}
          onRunValidation={onRunValidation}
          onOpenSection={onOpenSection}
        />
      </section>

      <hr className="overview-divider" />

      <section className="overview-band overview-band--evidence" aria-label={labels.validationCaption}>
        <SectionCaption glyph="evidence">{labels.validationCaption}</SectionCaption>
        <KeyResultsSummary
          execution={executionReady(executionStatus, execution) ? execution : null}
          validation={validationReady(validationStatus, validation) ? validation : null}
          labels={labels.keyResults}
        />
        <ResearchKeyValueList
          items={[
            {
              id: "validation",
              label: labels.validationStatus,
              value: validationStatusValue,
            },
            {
              id: "decision",
              label: labels.decisionStatus,
              value: decisionStatusValue,
            },
          ]}
        />
      </section>

      {showDecision ? (
        <>
          <hr className="overview-divider" />
          <section className="overview-band overview-band--decision" aria-label={labels.decisionCaption}>
            <SectionCaption glyph="decision">{labels.decisionCaption}</SectionCaption>
            <ResearchConclusion
              language={language}
              evaluation={evaluation}
              evaluationReady={showDecision}
              labels={labels.conclusion}
            />
          </section>
        </>
      ) : null}

      {provenanceSlot ? (
        <>
          <hr className="overview-divider" />
          <section className="overview-band overview-band--support" aria-label={labels.supportCaption}>
            <SectionCaption glyph="progress">{labels.supportCaption}</SectionCaption>
            {provenanceSlot}
          </section>
        </>
      ) : null}
    </div>
  );
}
