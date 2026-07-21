import EmptyState from "@/components/ui/EmptyState";
import StatusBadge from "@/components/ui/StatusBadge";
import ResearchBand from "@/components/features/research/ux/ResearchBand";
import ResearchCenterHeader from "@/components/features/research/ux/ResearchCenterHeader";
import ResearchNextAction from "@/components/features/research/ux/ResearchNextAction";
import ResearchStatusMatrix from "@/components/features/research/ux/ResearchStatusMatrix";
import { canonicalStatusVariant } from "@/lib/researchStatusBadge";
import {
  buildRobustnessCenterModel,
  type RobustnessFailureConditionId,
  type RobustnessItemId,
  type RobustnessItemStatus,
  type RobustnessOverallStatus,
} from "@/lib/researchRobustness";
import type { ResearchEvaluationResult } from "@/types/researchEvaluation";
import type { ResearchValidationResult } from "@/types/researchValidation";

export type ResearchRobustnessCenterLabels = {
  title: string;
  summary: string;
  statusTitle: string;
  matrixTitle: string;
  plannedTitle: string;
  failureTitle: string;
  nextActionTitle: string;
  nextActionDescription: string;
  nextActionCta: string;
  statusCompleted: string;
  statusPending: string;
  statusPlanned: string;
  statusBlocked: string;
  overallNotStarted: string;
  overallInProgress: string;
  overallBlocked: string;
  overallPlannedRemaining: string;
  overallComplete: string;
  overallNotStartedBody: string;
  overallInProgressBody: string;
  overallBlockedBody: string;
  overallPlannedRemainingBody: string;
  overallCompleteBody: string;
  nextResolveBlocker: string;
  nextContinue: string;
  nextNone: string;
  noEvidenceTitle: string;
  noEvidenceNote: string;
  plannedEmptyTitle: string;
  plannedEmpty: string;
  failureEmptyTitle: string;
  failureEmpty: string;
  itemLabels: Record<RobustnessItemId, string>;
  failureTitles: Record<RobustnessFailureConditionId, string>;
  failureBodies: Record<RobustnessFailureConditionId, string>;
};

type Props = {
  validation: ResearchValidationResult | null;
  evaluation: ResearchEvaluationResult | null;
  labels: ResearchRobustnessCenterLabels;
  onContinue?: () => void;
};

function statusLabel(
  status: RobustnessItemStatus,
  labels: ResearchRobustnessCenterLabels
): string {
  if (status === "completed") return labels.statusCompleted;
  if (status === "pending") return labels.statusPending;
  if (status === "blocked") return labels.statusBlocked;
  return labels.statusPlanned;
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
  if (status === "planned_remaining") {
    return {
      title: labels.overallPlannedRemaining,
      body: labels.overallPlannedRemainingBody,
      tone: "planned",
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
 * Research Robustness Center — organises robustness work.
 * Presentation-only: never invents metrics or runs new tests.
 */
export default function ResearchRobustnessCenter({
  validation,
  evaluation,
  labels,
  onContinue,
}: Props) {
  const model = buildRobustnessCenterModel({ validation, evaluation });
  const overall = overallCopy(model.overallStatus, labels);

  const plannedItems = model.items.filter((item) => item.status === "planned");

  const nextItem = model.nextItemId
    ? model.items.find((item) => item.id === model.nextItemId) ?? null
    : null;

  const nextActionText = (() => {
    if (model.nextActionKind === "none" || !nextItem) return labels.nextNone;
    const name = labels.itemLabels[nextItem.id];
    if (model.nextActionKind === "resolve_blocker") {
      return `${labels.nextResolveBlocker}: ${name}`;
    }
    return `${labels.nextContinue}: ${name}`;
  })();

  return (
    <section className="research-center" aria-labelledby="robustness-center-title">
      <ResearchCenterHeader
        titleId="robustness-center-title"
        title={labels.title}
        description={labels.summary}
      />

      {!model.hasValidationEvidence && !model.hasEvaluationEvidence ? (
        <EmptyState title={labels.noEvidenceTitle} description={labels.noEvidenceNote} />
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

      <ResearchBand caption={labels.plannedTitle} glyph="progress">
        {plannedItems.length === 0 ? (
          <EmptyState
            title={labels.plannedEmptyTitle}
            description={labels.plannedEmpty}
          />
        ) : (
          <ul className="research-chip-list">
            {plannedItems.map((item) => (
              <li key={item.id}>
                <StatusBadge
                  label={labels.itemLabels[item.id]}
                  variant="neutral"
                />
              </li>
            ))}
          </ul>
        )}
      </ResearchBand>

      <hr className="overview-divider" />

      <ResearchBand caption={labels.failureTitle} glyph="limitation">
        {model.failureConditionIds.length === 0 ? (
          <EmptyState
            title={labels.failureEmptyTitle}
            description={labels.failureEmpty}
          />
        ) : (
          <div className="research-note-list">
            {model.failureConditionIds.map((id) => (
              <article key={id} className="research-note-card">
                <h3 className="research-note-card__title">
                  {labels.failureTitles[id]}
                </h3>
                <p className="research-note-card__body">{labels.failureBodies[id]}</p>
              </article>
            ))}
          </div>
        )}
      </ResearchBand>

      <hr className="overview-divider" />

      <ResearchBand caption={labels.nextActionTitle} glyph="action" action>
        <ResearchNextAction
          eyebrow={labels.nextActionTitle}
          title={nextActionText}
          description={labels.nextActionDescription}
          cta={labels.nextActionCta}
          onClick={onContinue}
          disabled={!onContinue || model.nextActionKind === "none"}
        />
      </ResearchBand>
    </section>
  );
}
