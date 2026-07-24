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
    boundaryTitle: tr("robustnessBoundaryTitle"),
    boundaryDescription: tr("robustnessBoundaryDescription"),
    nextActionTitle: tr("researchLifecycleNextActionTitle"),
    nextActionDescription: tr("researchLifecycleNextActionDescription"),
    nextActionCta: tr("researchLifecycleNextActionCta"),
    statusCompleted: tr("robustnessStatusCompleted"),
    statusPending: tr("robustnessStatusPending"),
    statusBlocked: tr("robustnessStatusBlocked"),
    overallNotStarted: tr("robustnessOverallNotStarted"),
    overallInProgress: tr("robustnessOverallInProgress"),
    overallBlocked: tr("robustnessOverallBlocked"),
    overallComplete: tr("robustnessOverallComplete"),
    overallNotStartedBody: tr("robustnessOverallNotStartedBody"),
    overallInProgressBody: tr("robustnessOverallInProgressBody"),
    overallBlockedBody: tr("robustnessOverallBlockedBody"),
    overallCompleteBody: tr("robustnessOverallCompleteBody"),
    nextResolveBlocker: tr("robustnessNextResolveBlocker"),
    nextContinue: tr("robustnessNextContinue"),
    nextObservation: tr("robustnessNextObservation"),
    nextNone: tr("robustnessNextNone"),
    noEvidenceTitle: tr("robustnessNoEvidenceTitle"),
    noEvidenceNote: tr("robustnessNoEvidenceNote"),
    itemLabels: {
      parameter_sensitivity: tr("robustnessItemParameterSensitivity"),
      benchmark_comparison: tr("robustnessItemBenchmarkComparison"),
      transaction_cost: tr("robustnessItemTransactionCost"),
      data_quality: tr("robustnessItemDataQuality"),
    },
    boundaryLabels: {
      market_regime: tr("robustnessItemMarketRegime"),
      walk_forward: tr("robustnessItemWalkForward"),
      monte_carlo: tr("robustnessItemMonteCarlo"),
      liquidity_capacity: tr("robustnessItemLiquidityCapacity"),
    },
  };
}
