import EmptyState from "@/components/ui/EmptyState";
import StatusBadge from "@/components/ui/StatusBadge";
import ResearchBand from "@/components/features/research/ux/ResearchBand";
import ResearchCenterHeader from "@/components/features/research/ux/ResearchCenterHeader";
import ResearchKeyValueList from "@/components/features/research/ux/ResearchKeyValueList";
import ResearchNextAction from "@/components/features/research/ux/ResearchNextAction";
import ResearchStatusMatrix from "@/components/features/research/ux/ResearchStatusMatrix";
import { canonicalStatusVariant } from "@/lib/researchStatusBadge";
import {
  buildPaperTradingCenterModel,
  type ObservationItemId,
  type ObservationItemStatus,
  type PaperEligibilityStatus,
  type PaperNextActionKind,
  type ReviewCriterionId,
} from "@/lib/researchPaperTrading";
import type { ResearchDetail } from "@/types/research";
import type { ResearchEvaluationResult } from "@/types/researchEvaluation";
import type { ResearchValidationResult } from "@/types/researchValidation";

export type ResearchPaperTradingCenterLabels = {
  title: string;
  summary: string;
  deploymentTitle: string;
  deploymentResearch: string;
  deploymentExperiment: string;
  deploymentBenchmark: string;
  deploymentStrategy: string;
  deploymentStatus: string;
  eligibilityTitle: string;
  eligibilityNotEligible: string;
  eligibilityNeedsReview: string;
  eligibilityEligible: string;
  eligibilityActive: string;
  eligibilityCompleted: string;
  eligibilityStopped: string;
  eligibilityReasonNoValidation: string;
  eligibilityReasonBlocked: string;
  eligibilityReasonIncomplete: string;
  eligibilityReasonEligible: string;
  eligibilityReasonActive: string;
  eligibilityReasonCompleted: string;
  eligibilityReasonStopped: string;
  observationTitle: string;
  observationConfigured: string;
  observationPending: string;
  observationPlanned: string;
  observationLabels: Record<ObservationItemId, string>;
  sessionTitle: string;
  sessionEmptyTitle: string;
  sessionEmptyBody: string;
  reviewTitle: string;
  reviewAwaiting: string;
  reviewLabels: Record<ReviewCriterionId, string>;
  nextActionTitle: string;
  nextActionDescription: string;
  nextActionCta: string;
  nextContinueValidation: string;
  nextContinueRobustness: string;
  nextBeginObservation: string;
  nextContinueObservation: string;
  nextProceedDecision: string;
  nextArchive: string;
  nextNone: string;
  noEvidenceTitle: string;
  noEvidenceNote: string;
};

type Props = {
  research: ResearchDetail;
  validation: ResearchValidationResult | null;
  evaluation: ResearchEvaluationResult | null;
  labels: ResearchPaperTradingCenterLabels;
  onContinue?: () => void;
  showHeader?: boolean;
};

function eligibilityLabel(
  status: PaperEligibilityStatus,
  labels: ResearchPaperTradingCenterLabels
): string {
  if (status === "not_eligible") return labels.eligibilityNotEligible;
  if (status === "needs_review") return labels.eligibilityNeedsReview;
  if (status === "eligible") return labels.eligibilityEligible;
  if (status === "active") return labels.eligibilityActive;
  if (status === "completed") return labels.eligibilityCompleted;
  return labels.eligibilityStopped;
}

function eligibilityReason(
  reasonKey: ReturnType<typeof buildPaperTradingCenterModel>["eligibilityReasonKey"],
  labels: ResearchPaperTradingCenterLabels
): string {
  if (reasonKey === "no_validation") return labels.eligibilityReasonNoValidation;
  if (reasonKey === "blocked") return labels.eligibilityReasonBlocked;
  if (reasonKey === "incomplete") return labels.eligibilityReasonIncomplete;
  if (reasonKey === "eligible") return labels.eligibilityReasonEligible;
  if (reasonKey === "active") return labels.eligibilityReasonActive;
  if (reasonKey === "completed") return labels.eligibilityReasonCompleted;
  return labels.eligibilityReasonStopped;
}

function observationLabel(
  status: ObservationItemStatus,
  labels: ResearchPaperTradingCenterLabels
): string {
  if (status === "configured") return labels.observationConfigured;
  if (status === "pending") return labels.observationPending;
  return labels.observationPlanned;
}

function nextActionText(
  kind: PaperNextActionKind,
  labels: ResearchPaperTradingCenterLabels
): string {
  if (kind === "continue_validation") return labels.nextContinueValidation;
  if (kind === "continue_robustness") return labels.nextContinueRobustness;
  if (kind === "begin_observation") return labels.nextBeginObservation;
  if (kind === "continue_observation") return labels.nextContinueObservation;
  if (kind === "proceed_decision") return labels.nextProceedDecision;
  if (kind === "archive") return labels.nextArchive;
  return labels.nextNone;
}

/**
 * Research Deployment Center — paper trading as observation staging.
 * Presentation-only: never invents sessions, fills, or performance.
 */
export default function ResearchPaperTradingCenter({
  research,
  validation,
  evaluation,
  labels,
  onContinue,
  showHeader = true,
}: Props) {
  const model = buildPaperTradingCenterModel({
    research,
    validation,
    evaluation,
    hasSession: false,
  });

  return (
    <section
      className="research-center"
      aria-labelledby={showHeader ? "paper-deployment-title" : undefined}
      aria-label={showHeader ? undefined : labels.title}
    >
      {showHeader ? (
        <ResearchCenterHeader
          titleId="paper-deployment-title"
          title={labels.title}
          description={labels.summary}
        />
      ) : null}

      {!model.hasValidationEvidence && !model.hasEvaluationEvidence ? (
        <EmptyState title={labels.noEvidenceTitle} description={labels.noEvidenceNote} />
      ) : null}

      <ResearchBand caption={labels.deploymentTitle} glyph="progress">
        <ResearchKeyValueList
          items={[
            {
              id: "research",
              label: labels.deploymentResearch,
              value: model.deployment.researchName,
            },
            {
              id: "experiment",
              label: labels.deploymentExperiment,
              value: model.deployment.experimentLabel,
            },
            {
              id: "benchmark",
              label: labels.deploymentBenchmark,
              value: model.deployment.benchmark,
            },
            {
              id: "strategy",
              label: labels.deploymentStrategy,
              value: model.deployment.strategy,
            },
            {
              id: "status",
              label: labels.deploymentStatus,
              value: (
                <StatusBadge
                  label={model.deployment.currentStatus}
                  variant={canonicalStatusVariant(model.deployment.currentStatus)}
                />
              ),
            },
          ]}
        />
      </ResearchBand>

      <hr className="overview-divider" />

      <ResearchBand caption={labels.eligibilityTitle} glyph="decision">
        <div className="research-status-block">
          <StatusBadge
            label={eligibilityLabel(model.eligibility, labels)}
            variant={canonicalStatusVariant(model.eligibility)}
          />
          <p className="research-status-block__body">
            {eligibilityReason(model.eligibilityReasonKey, labels)}
          </p>
        </div>
      </ResearchBand>

      <hr className="overview-divider" />

      <ResearchBand caption={labels.observationTitle} glyph="evidence">
        <ResearchStatusMatrix
          items={model.observationItems.map((item) => ({
            id: item.id,
            label: labels.observationLabels[item.id],
            statusLabel: observationLabel(item.status, labels),
            statusTone:
              item.status === "configured"
                ? "completed"
                : item.status === "pending"
                  ? "pending"
                  : "planned",
          }))}
        />
      </ResearchBand>

      <hr className="overview-divider" />

      <ResearchBand caption={labels.sessionTitle} glyph="action">
        {!model.hasSession ? (
          <EmptyState
            title={labels.sessionEmptyTitle}
            description={labels.sessionEmptyBody}
          />
        ) : null}
      </ResearchBand>

      <hr className="overview-divider" />

      <ResearchBand caption={labels.reviewTitle} glyph="limitation">
        <ResearchStatusMatrix
          items={model.reviewCriteria.map((item) => ({
            id: item.id,
            label: labels.reviewLabels[item.id],
            statusLabel: labels.reviewAwaiting,
            statusTone: "pending",
          }))}
        />
      </ResearchBand>

      <hr className="overview-divider" />

      <ResearchBand caption={labels.nextActionTitle} glyph="action" action>
        <ResearchNextAction
          eyebrow={labels.nextActionTitle}
          title={nextActionText(model.nextActionKind, labels)}
          description={labels.nextActionDescription}
          cta={labels.nextActionCta}
          onClick={onContinue}
          disabled={!onContinue || model.nextActionKind === "none"}
        />
      </ResearchBand>
    </section>
  );
}
