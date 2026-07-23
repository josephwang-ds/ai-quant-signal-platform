"use client";

import Link from "next/link";
import AppShell from "@/components/layout/AppShell";
import ResearchPaperTradingCenter, {
  type ResearchPaperTradingCenterLabels,
} from "@/components/features/research/paper/ResearchPaperTradingCenter";
import ErrorAlert from "@/components/ui/ErrorAlert";
import LoadingState from "@/components/ui/LoadingState";
import SectionCard from "@/components/ui/SectionCard";
import SectionHeader from "@/components/ui/SectionHeader";
import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";
import { useResearchEvaluation } from "@/components/features/research/evaluation/useResearchEvaluation";
import { useResearchValidation } from "@/components/features/research/validation/useResearchValidation";
import { getResearchRepository } from "@/lib/localResearchRepository";
import type { TranslationKey } from "@/lib/i18n";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";
import { useEffect, useState } from "react";
import type { ResearchDetail } from "@/types/research";

export function buildPaperTradingLabels(
  tr: (key: TranslationKey) => string
): ResearchPaperTradingCenterLabels {
  return {
    title: tr("paperDeployTitle"),
    summary: tr("paperDeploySummary"),
    deploymentTitle: tr("paperDeployDeploymentTitle"),
    deploymentResearch: tr("paperDeployResearch"),
    deploymentExperiment: tr("paperDeployExperiment"),
    deploymentBenchmark: tr("paperDeployBenchmark"),
    deploymentStrategy: tr("paperDeployStrategy"),
    deploymentStatus: tr("paperDeployStatus"),
    eligibilityTitle: tr("paperDeployEligibilityTitle"),
    eligibilityNotEligible: tr("paperDeployEligibilityNotEligible"),
    eligibilityNeedsReview: tr("paperDeployEligibilityNeedsReview"),
    eligibilityEligible: tr("paperDeployEligibilityEligible"),
    eligibilityActive: tr("paperDeployEligibilityActive"),
    eligibilityCompleted: tr("paperDeployEligibilityCompleted"),
    eligibilityStopped: tr("paperDeployEligibilityStopped"),
    eligibilityReasonNoValidation: tr("paperDeployEligibilityReasonNoValidation"),
    eligibilityReasonBlocked: tr("paperDeployEligibilityReasonBlocked"),
    eligibilityReasonIncomplete: tr("paperDeployEligibilityReasonIncomplete"),
    eligibilityReasonEligible: tr("paperDeployEligibilityReasonEligible"),
    eligibilityReasonActive: tr("paperDeployEligibilityReasonActive"),
    eligibilityReasonCompleted: tr("paperDeployEligibilityReasonCompleted"),
    eligibilityReasonStopped: tr("paperDeployEligibilityReasonStopped"),
    observationTitle: tr("paperDeployObservationTitle"),
    observationConfigured: tr("paperDeployObservationConfigured"),
    observationPending: tr("paperDeployObservationPending"),
    observationPlanned: tr("paperDeployObservationPlanned"),
    observationLabels: {
      signal_consistency: tr("paperDeployObsSignalConsistency"),
      benchmark_behaviour: tr("paperDeployObsBenchmark"),
      transaction_cost_drift: tr("paperDeployObsCostDrift"),
      drawdown_behaviour: tr("paperDeployObsDrawdown"),
      data_quality: tr("paperDeployObsDataQuality"),
      position_changes: tr("paperDeployObsPositionChanges"),
    },
    sessionTitle: tr("paperDeploySessionTitle"),
    sessionEmptyTitle: tr("paperDeploySessionEmptyTitle"),
    sessionEmptyBody: tr("paperDeploySessionEmptyBody"),
    reviewTitle: tr("paperDeployReviewTitle"),
    reviewAwaiting: tr("paperDeployReviewAwaiting"),
    reviewLabels: {
      signal_consistent: tr("paperDeployReviewSignal"),
      costs_acceptable: tr("paperDeployReviewCosts"),
      drawdown_within_assumptions: tr("paperDeployReviewDrawdown"),
      no_validation_issues: tr("paperDeployReviewValidation"),
      benchmark_explainable: tr("paperDeployReviewBenchmark"),
    },
    nextActionTitle: tr("researchLifecycleNextActionTitle"),
    nextActionDescription: tr("researchLifecycleNextActionDescription"),
    nextActionCta: tr("researchLifecycleNextActionCta"),
    nextContinueValidation: tr("paperDeployNextContinueValidation"),
    nextContinueRobustness: tr("paperDeployNextContinueRobustness"),
    nextBeginObservation: tr("paperDeployNextBeginObservation"),
    nextContinueObservation: tr("paperDeployNextContinueObservation"),
    nextProceedDecision: tr("paperDeployNextProceedDecision"),
    nextArchive: tr("paperDeployNextArchive"),
    nextNone: tr("paperDeployNextNone"),
    noEvidenceTitle: tr("paperDeployNoEvidenceTitle"),
    noEvidenceNote: tr("paperDeployNoEvidenceNote"),
  };
}

/**
 * Standalone Paper Trading Research Deployment entry.
 * Observation staging only — not a broker terminal.
 */
export default function PaperTradingPage() {
  const { language, setLanguage, tr } = useWorkspaceLanguage();
  const [research, setResearch] = useState<ResearchDetail | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const detail = await getResearchRepository().getById(CANONICAL_RESEARCH_ID);
        if (!cancelled) {
          setResearch(detail);
          if (!detail) setLoadError(tr("paperDeployResearchMissing"));
        }
      } catch (err) {
        if (!cancelled) {
          setLoadError(err instanceof Error ? err.message : tr("paperDeployResearchMissing"));
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [tr]);

  const {
    enabled: validationEnabled,
    status: validationStatus,
    validation,
    error: validationError,
  } = useResearchValidation(CANONICAL_RESEARCH_ID, true);
  const validationRunId = validation?.validation_run_id ?? null;
  const { status: evaluationStatus, evaluation } = useResearchEvaluation(
    CANONICAL_RESEARCH_ID,
    true,
    validationRunId
  );

  const labels = buildPaperTradingLabels(tr);

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <SectionCard className="paper-trading-page-hero">
        <SectionHeader
          level={1}
          title={labels.title}
          description={labels.summary}
        />
        <div className="paper-trading-page-hero__footer">
          <p>{tr("paperDeployCanonicalHint")}</p>
          <Link
            href={`/research/${encodeURIComponent(CANONICAL_RESEARCH_ID)}?tab=paper`}
            className="btn btn--ghost"
          >
            {tr("paperDeployOpenWorkspace")}
          </Link>
        </div>
      </SectionCard>

      {loadError ? (
        <SectionCard className="paper-trading-state-panel">
          <ErrorAlert title={tr("paperDeployTitle")} message={loadError} />
        </SectionCard>
      ) : null}

      {!research && !loadError ? (
        <SectionCard className="paper-trading-state-panel">
          <LoadingState message={tr("researchWsLoading")} />
        </SectionCard>
      ) : null}

      {validationEnabled && validationStatus === "loading" ? (
        <SectionCard className="paper-trading-state-panel">
          <LoadingState message={tr("researchValLoading")} />
        </SectionCard>
      ) : null}

      {validationEnabled && validationStatus === "error" ? (
        <SectionCard className="paper-trading-state-panel">
          <ErrorAlert
            title={tr("researchValUnavailableTitle")}
            message={validationError ?? tr("researchValUnavailableDescription")}
          />
        </SectionCard>
      ) : null}

      {research ? (
        <SectionCard className="paper-trading-center-panel">
          <ResearchPaperTradingCenter
            research={research}
            validation={validationStatus === "ready" ? validation : null}
            evaluation={evaluationStatus === "ready" ? evaluation : null}
            labels={labels}
            showHeader={false}
          />
        </SectionCard>
      ) : null}
    </AppShell>
  );
}
