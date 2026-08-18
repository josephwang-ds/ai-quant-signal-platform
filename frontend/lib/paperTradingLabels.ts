/**
 * Label mapping for `ResearchPaperTradingCenter`.
 *
 * Previously exported from the standalone `/paper-trading` page. That route was
 * an orphan from the pre-text-signals information architecture — nothing linked
 * to it — so it was removed, but the Decision tab of the Research Workspace
 * still needs these labels. Relocated here rather than deleted with the page.
 */

import type { ResearchPaperTradingCenterLabels } from "@/components/features/research/paper/ResearchPaperTradingCenter";
import type { TranslationKey } from "@/lib/i18n";

export function buildPaperTradingLabels(
  tr: (key: TranslationKey) => string
): ResearchPaperTradingCenterLabels {
  return {
    title: tr("paperDeployTitle"),
    summary: tr("paperDeploySummary"),
    contextTitle: tr("paperDeployDeploymentTitle"),
    research: tr("paperDeployResearch"),
    experiment: tr("paperDeployExperiment"),
    benchmark: tr("paperDeployBenchmark"),
    eligibilityTitle: tr("paperDeployEligibilityTitle"),
    eligibilityNotEligible: tr("paperDeployEligibilityNotEligible"),
    eligibilityNeedsReview: tr("paperDeployEligibilityNeedsReview"),
    eligibilityEligible: tr("paperDeployEligibilityEligible"),
    eligibilityActive: tr("paperDeployEligibilityActive"),
    eligibilityCompleted: tr("paperDeployEligibilityCompleted"),
    eligibilityReasonNoValidation: tr("paperDeployEligibilityReasonNoValidation"),
    eligibilityReasonBlocked: tr("paperDeployEligibilityReasonBlocked"),
    eligibilityReasonIncomplete: tr("paperDeployEligibilityReasonIncomplete"),
    eligibilityReasonEligible: tr("paperDeployEligibilityReasonEligible"),
    eligibilityReasonActive: tr("paperDeployEligibilityReasonActive"),
    eligibilityReasonCompleted: tr("paperDeployEligibilityReasonCompleted"),
    planTitle: tr("paperObservationPlanTitle"),
    cadence: tr("paperObservationCadence"),
    cadenceDaily: tr("paperObservationCadenceDaily"),
    cadenceWeekly: tr("paperObservationCadenceWeekly"),
    cadenceMonthly: tr("paperObservationCadenceMonthly"),
    minimumDays: tr("paperObservationMinimumDays"),
    exitCriteria: tr("paperObservationExitCriteria"),
    exitCriteriaPlaceholder: tr("paperObservationExitCriteriaPlaceholder"),
    startSession: tr("paperObservationStart"),
    activeSession: tr("paperObservationActive"),
    completedSession: tr("paperObservationCompleted"),
    startedAt: tr("paperObservationStartedAt"),
    completedAt: tr("paperObservationCompletedAt"),
    completeSession: tr("paperObservationComplete"),
    logTitle: tr("paperObservationLogTitle"),
    logEmptyTitle: tr("paperObservationLogEmptyTitle"),
    logEmptyBody: tr("paperObservationLogEmptyBody"),
    observationNote: tr("paperObservationNote"),
    observationPlaceholder: tr("paperObservationNotePlaceholder"),
    addObservation: tr("paperObservationAdd"),
    localNote: tr("paperObservationLocalNote"),
    continueDecision: tr("paperObservationContinueDecision"),
    noEvidenceTitle: tr("paperDeployNoEvidenceTitle"),
    noEvidenceNote: tr("paperDeployNoEvidenceNote"),
  };
}
