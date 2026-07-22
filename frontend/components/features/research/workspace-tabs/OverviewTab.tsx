"use client";

import OverviewSection from "@/components/features/research/OverviewSection";
import type { Language, TranslationKey } from "@/lib/i18n";
import type { ResearchDetail } from "@/types/research";
import type { ResearchExecutionResult, ResearchExecutionStatus } from "@/types/researchExecution";
import type { ResearchValidationResult, ResearchValidationStatus } from "@/types/researchValidation";
import type { ResearchEvaluationResult, ResearchEvaluationRequestStatus } from "@/types/researchEvaluation";
import type { ResearchWorkspaceSection } from "@/types/research";
import type { ReactNode } from "react";

export type OverviewTabProps = {
  language: Language;
  tr: (key: TranslationKey) => string;
  displayResearch: ResearchDetail;
  provenanceSlot: ReactNode;
  executionStatus: ResearchExecutionStatus;
  execution: ResearchExecutionResult | null;
  validationStatus: ResearchValidationStatus;
  validation: ResearchValidationResult | null;
  evaluationStatus: ResearchEvaluationRequestStatus;
  evaluation: ResearchEvaluationResult | null;
  reloadExecution: () => void;
  handleRunValidation: () => void;
  navigateToSection: (section: ResearchWorkspaceSection) => void;
};

export default function OverviewTab({
  language,
  tr,
  displayResearch,
  provenanceSlot,
  executionStatus,
  execution,
  validationStatus,
  validation,
  evaluationStatus,
  evaluation,
  reloadExecution,
  handleRunValidation,
  navigateToSection,
}: OverviewTabProps) {
    return (
      <OverviewSection
        language={language}
        research={displayResearch}
        provenanceSlot={provenanceSlot}
        executionStatus={executionStatus}
        execution={execution}
        validationStatus={validationStatus}
        validation={validation}
        evaluationStatus={evaluationStatus}
        evaluation={evaluation}
        onRunResearch={reloadExecution}
        onRunValidation={handleRunValidation}
        onOpenSection={navigateToSection}
        labels={{
          keyResultsTitle: tr("researchWsCalculatedMetrics"),
          guidedWorkflowTitle: tr("researchWsGuidedWorkflowTitle"),
          conclusionTitle: tr("researchWsCurrentDecision"),
          evidencePreviewTitle: tr("researchWsEvidencePreview"),
          primaryActionCaption: tr("researchWsBandAction"),
          progressCaption: tr("researchWsBandProgress"),
          validationCaption: tr("researchWsBandValidation"),
          decisionCaption: tr("researchWsBandDecision"),
          supportCaption: tr("researchWsBandSupport"),
          validationStatus: tr("researchWsNavValidation"),
          decisionStatus: tr("researchWsNavDecision"),
          validationComplete: tr("researchValEvidenceComplete"),
          validationIncomplete: tr("researchValIncomplete"),
          validationPending: tr("researchWsValidationNotStarted"),
          decisionPending: tr("researchWsDecisionPending"),
          evaluationCompleted: tr("researchEvalCompleted"),
          evaluationIncomplete: tr("researchEvalIncomplete"),
          evaluationBlocked: tr("researchEvalBlocked"),
          keyResults: {
            strategyTotalReturn: `${tr("researchListStrategy")} ${tr("researchWsMetricTotalReturn")}`,
            benchmarkTotalReturn: tr("researchWsMetricBenchReturn"),
            maxDrawdown: tr("researchValMaxDrawdown"),
            oosSharpe: `${tr("researchValOutOfSample")} ${tr("researchValSharpe")}`,
            unavailable: tr("researchWsKeyResultsUnavailable"),
            unavailableTitle: tr("researchWsKeyResultsUnavailableTitle"),
            oosSharpeUnavailable: tr("researchWsOosSharpeUnavailable"),
          },
          guidedFlow: {
            title: tr("researchWsGuidedWorkflowTitle"),
            stepResearch: tr("researchWsNavOverview"),
            stepExperiment: tr("researchWsNavExperiments"),
            stepValidation: tr("researchWsNavValidation"),
            stepRobustness: tr("researchWsNavRobustness"),
            stepPaper: tr("researchWsNavPaper"),
            stepDecision: tr("researchWsNavDecision"),
            stepArchive: tr("researchWsNavArchive"),
            unavailableUntilPrior: tr("researchWsGuidedUnavailableUntilPrior"),
            loading: tr("researchWsGuidedLoading"),
            failed: tr("researchWsGuidedFailed"),
          },
          nextStep: {
            title: tr("researchWsNextStepTitle"),
            runResearchTitle: tr("researchWsNextStepRunResearchTitle"),
            runResearchDescription: tr("researchWsNextStepRunResearchDescription"),
            runResearchCta: tr("researchWsNextStepRunResearchCta"),
            runResearchLoadingCta: tr("researchWsNextStepRunResearchLoadingCta"),
            runResearchRetryCta: tr("researchWsNextStepRunResearchRetryCta"),
            validateTitle: tr("researchWsNextStepValidateTitle"),
            validateDescription: tr("researchWsNextStepValidateDescription"),
            validateCta: tr("researchWsNextStepValidateCta"),
            openExperimentTitle: tr("researchWsNextStepOpenExperimentTitle"),
            openExperimentDescription: tr(
              "researchWsNextStepOpenExperimentDescription"
            ),
            openExperimentCta: tr("researchWsNextStepOpenExperimentCta"),
            openRobustnessTitle: tr("researchWsNextStepOpenRobustnessTitle"),
            openRobustnessDescription: tr(
              "researchWsNextStepOpenRobustnessDescription"
            ),
            openRobustnessCta: tr("researchWsNextStepOpenRobustnessCta"),
            openPaperTitle: tr("researchWsNextStepOpenPaperTitle"),
            openPaperDescription: tr("researchWsNextStepOpenPaperDescription"),
            openPaperCta: tr("researchWsNextStepOpenPaperCta"),
            openDecisionTitle: tr("researchWsNextStepOpenDecisionTitle"),
            openDecisionDescription: tr(
              "researchWsNextStepOpenDecisionDescription"
            ),
            openDecisionCta: tr("researchWsNextStepOpenDecisionCta"),
            openArchiveTitle: tr("researchWsNextStepOpenArchiveTitle"),
            openArchiveDescription: tr("researchWsNextStepOpenArchiveDescription"),
            openArchiveCta: tr("researchWsNextStepOpenArchiveCta"),
          },
          conclusion: {
            title: tr("researchWsCurrentDecision"),
            notRequested: tr("researchWsConclusionNotRequested"),
            incomplete: tr("researchWsConclusionIncomplete"),
            blocked: tr("researchWsConclusionBlocked"),
            completed: tr("researchEvalCompleted"),
            coverageLabel: tr("researchEvalCoveragePercentage"),
            keyStrengthsLabel: tr("researchWsKeyStrengths"),
            limitationLabel: tr("researchWsKnownWeaknesses"),
            nextActionLabel: tr("researchWsNextActions"),
          },
        }}
      />
    );
}
