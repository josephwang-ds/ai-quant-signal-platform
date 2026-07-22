"use client";

import Link from "next/link";
import Button from "@/components/ui/Button";
import ErrorAlert from "@/components/ui/ErrorAlert";
import LoadingState from "@/components/ui/LoadingState";
import ResearchEvaluationPanel from "@/components/features/research/evaluation/ResearchEvaluationPanel";
import type { Language, TranslationKey } from "@/lib/i18n";
import type { ResearchEvaluationResult, ResearchEvaluationRequestStatus } from "@/types/researchEvaluation";

export type EvaluationBlockProps = {
  researchId: string;
  language: Language;
  tr: (key: TranslationKey) => string;
  evaluationEnabled: boolean;
  evaluationStatus: ResearchEvaluationRequestStatus;
  evaluation: ResearchEvaluationResult | null;
  evaluationError: string | null;
  reloadEvaluation: () => void;
};

export default function EvaluationBlock({
  researchId,
  language,
  tr,
  evaluationEnabled,
  evaluationStatus,
  evaluation,
  evaluationError,
  reloadEvaluation,
}: EvaluationBlockProps) {
    if (!evaluationEnabled) {
      return (
        <ErrorAlert
          title={tr("researchEvalUnavailableTitle")}
          message={tr("researchEvalUnavailableDescription")}
        />
      );
    }
    if (evaluationStatus === "awaiting_validation") {
      return (
        <div className="research-execution-error">
          <ErrorAlert
            title={tr("researchEvalAwaitingValidationTitle")}
            message={tr("researchEvalAwaitingValidationDescription")}
          />
          <Link
            href={`/research/${encodeURIComponent(researchId)}?tab=validation`}
            className="btn btn--primary"
          >
            {tr("researchEvalGoToValidation")}
          </Link>
        </div>
      );
    }
    if (evaluationStatus === "loading") {
      return <LoadingState message={tr("researchEvalLoading")} />;
    }
    if (evaluationStatus === "error") {
      return (
        <div className="research-execution-error">
          <ErrorAlert
            title={tr("researchEvalUnavailableTitle")}
            message={evaluationError ?? tr("researchEvalUnavailableDescription")}
          />
          <Button primary onClick={reloadEvaluation}>
            {tr("researchEvalRetry")}
          </Button>
        </div>
      );
    }
    if (evaluationStatus !== "ready" || !evaluation) {
      return null;
    }
    return (
      <ResearchEvaluationPanel
        evaluation={evaluation}
        language={language}
        labels={{
          title: tr("researchWsEvaluationTitle"),
          summary: tr("researchEvalSummary"),
          status: tr("researchEvalStatus"),
          completed: tr("researchEvalCompleted"),
          incomplete: tr("researchEvalIncomplete"),
          blocked: tr("researchEvalBlocked"),
          source: tr("researchEvalSource"),
          generated: tr("researchEvalGenerated"),
          coverageTitle: tr("researchEvalCoverageTitle"),
          implementedStages: tr("researchEvalImplementedStages"),
          completedStagesCount: tr("researchEvalCompletedStagesCount"),
          coveragePercentage: tr("researchEvalCoveragePercentage"),
          coverageDisclaimer: tr("researchEvalCoverageDisclaimer"),
          evidenceSummaryTitle: tr("researchEvalEvidenceSummaryTitle"),
          stageColumn: tr("researchEvalStageColumn"),
          statusColumn: tr("researchEvalStatusColumn"),
          summaryColumn: tr("researchEvalSummaryColumn"),
          completedEvidenceTitle: tr("researchEvalCompletedEvidenceTitle"),
          incompleteEvidenceTitle: tr("researchEvalIncompleteEvidenceTitle"),
          nextMilestonesTitle: tr("researchEvalNextMilestonesTitle"),
          limitationsTitle: tr("researchEvalLimitationsTitle"),
          blockersTitle: tr("researchEvalBlockersTitle"),
          noBlockersTitle: tr("researchEvalNoBlockersTitle"),
          noBlockersDescription: tr("researchEvalNoBlockersDescription"),
          limitationGroupEvidence: tr("researchEvalLimitationGroupEvidence"),
          limitationGroupValidation: tr("researchEvalLimitationGroupValidation"),
          limitationGroupRobustness: tr("researchEvalLimitationGroupRobustness"),
          limitationGroupDeployment: tr("researchEvalLimitationGroupDeployment"),
          decisionReadinessTitle: tr("researchEvalDecisionReadiness"),
          keyFindingsTitle: tr("researchEvalKeyFindings"),
          nextGovernanceActionTitle: tr("researchEvalNextGovernanceAction"),
          detailsTitle: tr("researchEvalDetailsTitle"),
          none: tr("researchEvalNone"),
          notAvailable: tr("researchEvalNotAvailable"),
        }}
      />
    );
}
