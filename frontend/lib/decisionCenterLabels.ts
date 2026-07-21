import type { ResearchDecisionCenterLabels } from "@/components/features/research/decision/ResearchDecisionCenter";
import type { TranslationKey } from "@/lib/i18n";

export function buildDecisionCenterLabels(
  tr: (key: TranslationKey) => string
): ResearchDecisionCenterLabels {
  return {
    title: tr("decisionCenterTitle"),
    summary: tr("decisionCenterSummary"),
    summaryTitle: tr("decisionCenterSummaryTitle"),
    summaryResearch: tr("decisionCenterResearch"),
    summaryExperiment: tr("decisionCenterExperiment"),
    summaryStatus: tr("decisionCenterStatus"),
    statusNotReady: tr("decisionCenterStatusNotReady"),
    statusUnderReview: tr("decisionCenterStatusUnderReview"),
    statusApprovedForPaper: tr("decisionCenterStatusApprovedForPaper"),
    statusRejected: tr("decisionCenterStatusRejected"),
    statusArchived: tr("decisionCenterStatusArchived"),
    evidenceTitle: tr("decisionCenterEvidenceTitle"),
    evidenceCompleted: tr("decisionCenterEvidenceCompleted"),
    evidencePending: tr("decisionCenterEvidencePending"),
    evidenceLabels: {
      validation: tr("decisionCenterEvidenceValidation"),
      robustness: tr("decisionCenterEvidenceRobustness"),
      paper_trading: tr("decisionCenterEvidencePaper"),
    },
    risksTitle: tr("decisionCenterRisksTitle"),
    risksEmptyTitle: tr("decisionCenterRisksEmptyTitle"),
    risksEmpty: tr("decisionCenterRisksEmpty"),
    riskLabels: {
      extreme_volatility: tr("decisionCenterRiskStress"),
      regime_shift: tr("decisionCenterRiskRegime"),
      forward_validation: tr("decisionCenterRiskWalkForward"),
      capacity: tr("decisionCenterRiskCapacity"),
      implemented_robustness_pending: tr("decisionCenterRiskImplementedPending"),
    },
    checklistTitle: tr("decisionCenterChecklistTitle"),
    checklistCompleted: tr("decisionCenterChecklistCompleted"),
    checklistPending: tr("decisionCenterChecklistPending"),
    checklistLabels: {
      validation_completed: tr("decisionCenterCheckValidation"),
      robustness_reviewed: tr("decisionCenterCheckRobustness"),
      observation_plan_prepared: tr("decisionCenterCheckObservation"),
      limitations_documented: tr("decisionCenterCheckLimitations"),
    },
    notesTitle: tr("decisionCenterNotesTitle"),
    notesEmptyTitle: tr("decisionCenterNotesEmptyTitle"),
    notesEmpty: tr("decisionCenterNotesEmpty"),
    nextActionTitle: tr("researchLifecycleNextActionTitle"),
    nextActionDescription: tr("researchLifecycleNextActionDescription"),
    nextActionCta: tr("researchLifecycleNextActionCta"),
    nextCompleteValidation: tr("decisionCenterNextCompleteValidation"),
    nextCompleteRobustness: tr("decisionCenterNextCompleteRobustness"),
    nextPreparePaper: tr("decisionCenterNextPreparePaper"),
    nextContinuePaper: tr("decisionCenterNextContinuePaper"),
    nextArchive: tr("decisionCenterNextArchive"),
    nextNone: tr("decisionCenterNextNone"),
    noEvidenceTitle: tr("decisionCenterNoEvidenceTitle"),
    noEvidenceNote: tr("decisionCenterNoEvidenceNote"),
  };
}
