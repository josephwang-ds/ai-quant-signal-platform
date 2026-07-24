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
    statusReady: tr("decisionCenterStatusReady"),
    evidenceTitle: tr("decisionCenterEvidenceTitle"),
    evidenceCompleted: tr("decisionCenterEvidenceCompleted"),
    evidencePending: tr("decisionCenterEvidencePending"),
    evidenceLabels: {
      validation: tr("decisionCenterEvidenceValidation"),
      robustness: tr("decisionCenterEvidenceRobustness"),
    },
    risksTitle: tr("decisionCenterRisksTitle"),
    risksEmptyTitle: tr("decisionCenterRisksEmptyTitle"),
    risksEmpty: tr("decisionCenterRisksEmpty"),
    riskLabels: {
      parameter_sensitivity: tr("decisionCenterRiskParameter"),
      benchmark_comparison: tr("decisionCenterRiskBenchmark"),
      transaction_cost: tr("decisionCenterRiskCost"),
      data_quality: tr("decisionCenterRiskDataQuality"),
    },
    checklistTitle: tr("decisionCenterChecklistTitle"),
    checklistCompleted: tr("decisionCenterChecklistCompleted"),
    checklistPending: tr("decisionCenterChecklistPending"),
    checklistLabels: {
      validation_completed: tr("decisionCenterCheckValidation"),
      robustness_reviewed: tr("decisionCenterCheckRobustness"),
      limitations_documented: tr("decisionCenterCheckLimitations"),
    },
    recordTitle: tr("decisionRecordTitle"),
    recordDescription: tr("decisionRecordDescription"),
    outcomeLabel: tr("decisionRecordOutcome"),
    outcomeAdvance: tr("decisionRecordAdvance"),
    outcomeHold: tr("decisionRecordHold"),
    outcomeReject: tr("decisionRecordReject"),
    rationaleLabel: tr("decisionRecordRationale"),
    rationalePlaceholder: tr("decisionRecordRationalePlaceholder"),
    saveDecision: tr("decisionRecordSave"),
    savedDecision: tr("decisionRecordSaved"),
    localNote: tr("decisionRecordLocalNote"),
    noEvidenceTitle: tr("decisionCenterNoEvidenceTitle"),
    noEvidenceNote: tr("decisionCenterNoEvidenceNote"),
  };
}
