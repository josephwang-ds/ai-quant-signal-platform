import EmptyState from "@/components/ui/EmptyState";
import StatusBadge from "@/components/ui/StatusBadge";
import ResearchBand from "@/components/features/research/ux/ResearchBand";
import ResearchCenterHeader from "@/components/features/research/ux/ResearchCenterHeader";
import ResearchNextAction from "@/components/features/research/ux/ResearchNextAction";
import ResearchStatusMatrix from "@/components/features/research/ux/ResearchStatusMatrix";
import { canonicalStatusVariant } from "@/lib/researchStatusBadge";
import {
  buildRobustnessCenterModel,
  type RobustnessItemId,
  type RobustnessItemStatus,
  type RobustnessOverallStatus,
  type RobustnessScopeBoundaryId,
} from "@/lib/researchRobustness";
import type { ResearchEvaluationResult } from "@/types/researchEvaluation";
import type { ResearchValidationResult } from "@/types/researchValidation";

export type ResearchRobustnessCenterLabels = {
  title: string;
  summary: string;
  statusTitle: string;
  matrixTitle: string;
  boundaryTitle: string;
  boundaryDescription: string;
  nextActionTitle: string;
  nextActionDescription: string;
  nextActionCta: string;
  statusCompleted: string;
  statusPending: string;
  statusBlocked: string;
  overallNotStarted: string;
  overallInProgress: string;
  overallBlocked: string;
  overallComplete: string;
  overallNotStartedBody: string;
  overallInProgressBody: string;
  overallBlockedBody: string;
  overallCompleteBody: string;
  nextResolveBlocker: string;
  nextContinue: string;
  nextObservation: string;
  nextNone: string;
  noEvidenceTitle: string;
  noEvidenceNote: string;
  itemLabels: Record<RobustnessItemId, string>;
  boundaryLabels: Record<RobustnessScopeBoundaryId, string>;
};

type Props = {
  validation: ResearchValidationResult | null;
  evaluation: ResearchEvaluationResult | null;
  labels: ResearchRobustnessCenterLabels;
  onContinue?: (target: "validation" | "paper") => void;
  showHeader?: boolean;
};

function statusLabel(
  status: RobustnessItemStatus,
  labels: ResearchRobustnessCenterLabels
): string {
  if (status === "completed") return labels.statusCompleted;
  if (status === "pending") return labels.statusPending;
  return labels.statusBlocked;
}

function overallCopy(
  status: RobustnessOverallStatus,
  labels: ResearchRobustnessCenterLabels
): { title: string; body: string; tone: string } {
  if (status === "blocked") {
    return {
      title: labels.overallBlocked,
      body: labels.overallBlockedBody,
      tone: "blocked",
    };
  }
  if (status === "in_progress") {
    return {
      title: labels.overallInProgress,
      body: labels.overallInProgressBody,
      tone: "pending",
    };
  }
  if (status === "complete") {
    return {
      title: labels.overallComplete,
      body: labels.overallCompleteBody,
      tone: "completed",
    };
  }
  return {
    title: labels.overallNotStarted,
    body: labels.overallNotStartedBody,
    tone: "not_started",
  };
}

/**
 * Evidence-backed robustness review.
 * Only implemented deterministic checks appear in the matrix. Unsupported
 * methods are disclosed once as a scope boundary, not rendered as fake tasks.
 */
export default function ResearchRobustnessCenter({
  validation,
  evaluation,
  labels,
  onContinue,
  showHeader = true,
}: Props) {
  const model = buildRobustnessCenterModel({ validation, evaluation });
  const overall = overallCopy(model.overallStatus, labels);
  const nextItem = model.nextItemId
    ? model.items.find((item) => item.id === model.nextItemId) ?? null
    : null;

  const nextActionText = (() => {
    if (model.nextActionKind === "start_observation") {
      return labels.nextObservation;
    }
    if (model.nextActionKind === "none" || !nextItem) return labels.nextNone;
    const name = labels.itemLabels[nextItem.id];
    return model.nextActionKind === "resolve_blocker"
      ? `${labels.nextResolveBlocker}: ${name}`
      : `${labels.nextContinue}: ${name}`;
  })();

  return (
    <section
      className="research-center"
      aria-labelledby={showHeader ? "robustness-center-title" : undefined}
      aria-label={showHeader ? undefined : labels.title}
    >
      {showHeader ? (
        <ResearchCenterHeader
          titleId="robustness-center-title"
          title={labels.title}
          description={labels.summary}
        />
      ) : null}

      {!model.hasValidationEvidence && !model.hasEvaluationEvidence ? (
        <EmptyState
          title={labels.noEvidenceTitle}
          description={labels.noEvidenceNote}
        />
      ) : null}

      <ResearchBand caption={labels.statusTitle} glyph="decision">
        <div className="research-status-block">
          <StatusBadge
            label={overall.title}
            variant={canonicalStatusVariant(overall.tone)}
          />
          <p className="research-status-block__body">{overall.body}</p>
        </div>
      </ResearchBand>

      <hr className="overview-divider" />

      <ResearchBand caption={labels.matrixTitle} glyph="evidence">
        <ResearchStatusMatrix
          items={model.items.map((item) => ({
            id: item.id,
            label: labels.itemLabels[item.id],
            statusLabel: statusLabel(item.status, labels),
            statusTone: item.status,
          }))}
        />
      </ResearchBand>

      <hr className="overview-divider" />

      <ResearchBand caption={labels.boundaryTitle} glyph="limitation">
        <p className="research-status-block__body">
          {labels.boundaryDescription}
        </p>
        <ul className="research-plain-list">
          {model.scopeBoundaryIds.map((id) => (
            <li key={id}>{labels.boundaryLabels[id]}</li>
          ))}
        </ul>
      </ResearchBand>

      <hr className="overview-divider" />

      <ResearchBand caption={labels.nextActionTitle} glyph="action" action>
        <ResearchNextAction
          eyebrow={labels.nextActionTitle}
          title={nextActionText}
          description={labels.nextActionDescription}
          cta={labels.nextActionCta}
          onClick={
            onContinue
              ? () =>
                  onContinue(
                    model.nextActionKind === "start_observation"
                      ? "paper"
                      : "validation"
                  )
              : undefined
          }
          disabled={!onContinue || model.nextActionKind === "none"}
        />
      </ResearchBand>
    </section>
  );
}
