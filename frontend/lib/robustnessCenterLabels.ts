import type { ResearchRobustnessCenterLabels } from "@/components/features/research/robustness/ResearchRobustnessCenter";
import type { TranslationKey } from "@/lib/i18n";

export function buildRobustnessCenterLabels(
  tr: (key: TranslationKey) => string
): ResearchRobustnessCenterLabels {
  return {
    title: tr("robustnessCenterTitle"),
    summary: tr("robustnessCenterSummary"),
    statusTitle: tr("robustnessStatusTitle"),
    matrixTitle: tr("robustnessMatrixTitle"),
    plannedTitle: tr("robustnessPlannedTitle"),
    failureTitle: tr("robustnessFailureTitle"),
    nextActionTitle: tr("researchLifecycleNextActionTitle"),
    nextActionDescription: tr("researchLifecycleNextActionDescription"),
    nextActionCta: tr("researchLifecycleNextActionCta"),
    statusCompleted: tr("robustnessStatusCompleted"),
    statusPending: tr("robustnessStatusPending"),
    statusPlanned: tr("robustnessStatusPlanned"),
    statusBlocked: tr("robustnessStatusBlocked"),
    overallNotStarted: tr("robustnessOverallNotStarted"),
    overallInProgress: tr("robustnessOverallInProgress"),
    overallBlocked: tr("robustnessOverallBlocked"),
    overallPlannedRemaining: tr("robustnessOverallPlannedRemaining"),
    overallComplete: tr("robustnessOverallComplete"),
    overallNotStartedBody: tr("robustnessOverallNotStartedBody"),
    overallInProgressBody: tr("robustnessOverallInProgressBody"),
    overallBlockedBody: tr("robustnessOverallBlockedBody"),
    overallPlannedRemainingBody: tr("robustnessOverallPlannedRemainingBody"),
    overallCompleteBody: tr("robustnessOverallCompleteBody"),
    nextResolveBlocker: tr("robustnessNextResolveBlocker"),
    nextContinue: tr("robustnessNextContinue"),
    nextNone: tr("robustnessNextNone"),
    noEvidenceTitle: tr("robustnessNoEvidenceTitle"),
    noEvidenceNote: tr("robustnessNoEvidenceNote"),
    plannedEmptyTitle: tr("robustnessPlannedEmptyTitle"),
    plannedEmpty: tr("robustnessPlannedEmpty"),
    failureEmptyTitle: tr("robustnessFailureEmptyTitle"),
    failureEmpty: tr("robustnessFailureEmpty"),
    itemLabels: {
      parameter_sensitivity: tr("robustnessItemParameterSensitivity"),
      benchmark_comparison: tr("robustnessItemBenchmarkComparison"),
      transaction_cost: tr("robustnessItemTransactionCost"),
      data_quality: tr("robustnessItemDataQuality"),
      stress_test: tr("robustnessItemStressTest"),
      market_regime: tr("robustnessItemMarketRegime"),
      walk_forward: tr("robustnessItemWalkForward"),
      monte_carlo: tr("robustnessItemMonteCarlo"),
      liquidity_capacity: tr("robustnessItemLiquidityCapacity"),
    },
    failureTitles: {
      extreme_volatility: tr("robustnessFailureExtremeVolatilityTitle"),
      regime_shift: tr("robustnessFailureRegimeShiftTitle"),
      forward_validation: tr("robustnessFailureForwardValidationTitle"),
      capacity: tr("robustnessFailureCapacityTitle"),
    },
    failureBodies: {
      extreme_volatility: tr("robustnessFailureExtremeVolatilityBody"),
      regime_shift: tr("robustnessFailureRegimeShiftBody"),
      forward_validation: tr("robustnessFailureForwardValidationBody"),
      capacity: tr("robustnessFailureCapacityBody"),
    },
  };
}
