import EmptyState from "@/components/ui/EmptyState";
import StatusBadge from "@/components/ui/StatusBadge";
import ResearchBand from "@/components/features/research/ux/ResearchBand";
import ResearchCenterHeader from "@/components/features/research/ux/ResearchCenterHeader";
import ResearchKeyValueList from "@/components/features/research/ux/ResearchKeyValueList";
import ResearchNextAction from "@/components/features/research/ux/ResearchNextAction";
import ResearchStatusMatrix from "@/components/features/research/ux/ResearchStatusMatrix";
import { canonicalStatusVariant } from "@/lib/researchStatusBadge";
import {
  buildDecisionCenterModel,
  type DecisionChecklistId,
  type DecisionEvidenceId,
  type DecisionEvidenceStatus,
  type DecisionNextActionKind,
  type DecisionRiskId,
  type DecisionStatus,
} from "@/lib/researchDecision";
import type { ResearchDetail } from "@/types/research";
import type { ResearchEvaluationResult } from "@/types/researchEvaluation";
import type { ResearchValidationResult } from "@/types/researchValidation";

export type ResearchDecisionCenterLabels = {
  title: string;
  summary: string;
  summaryTitle: string;
  summaryResearch: string;
  summaryExperiment: string;
  summaryStatus: string;
  statusNotReady: string;
  statusUnderReview: string;
  statusApprovedForPaper: string;
  statusRejected: string;
  statusArchived: string;
  evidenceTitle: string;
  evidenceCompleted: string;
  evidencePending: string;
  evidenceLabels: Record<DecisionEvidenceId, string>;
  risksTitle: string;
  risksEmptyTitle: string;
  risksEmpty: string;
  riskLabels: Record<DecisionRiskId, string>;
  checklistTitle: string;
  checklistCompleted: string;
  checklistPending: string;
  checklistLabels: Record<DecisionChecklistId, string>;
  notesTitle: string;
  notesEmptyTitle: string;
  notesEmpty: string;
  nextActionTitle: string;
  nextActionDescription: string;
  nextActionCta: string;
  nextCompleteValidation: string;
  nextCompleteRobustness: string;
  nextPreparePaper: string;
  nextContinuePaper: string;
  nextArchive: string;
  nextNone: string;
  noEvidenceTitle: string;
  noEvidenceNote: string;
};

type Props = {
  research: ResearchDetail;
  validation: ResearchValidationResult | null;
  evaluation: ResearchEvaluationResult | null;
  labels: ResearchDecisionCenterLabels;
  onContinue?: () => void;
};

function statusLabel(
  status: DecisionStatus,
  labels: ResearchDecisionCenterLabels
): string {
  if (status === "not_ready") return labels.statusNotReady;
  if (status === "under_review") return labels.statusUnderReview;
  if (status === "approved_for_paper") return labels.statusApprovedForPaper;
  if (status === "rejected") return labels.statusRejected;
  return labels.statusArchived;
}

function statusTone(status: DecisionStatus): string {
  if (status === "approved_for_paper") return "approved";
  if (status === "under_review") return "pending";
  if (status === "rejected") return "rejected";
  if (status === "archived") return "not_started";
  return "not_started";
}

function evidenceLabel(
  status: DecisionEvidenceStatus,
  labels: ResearchDecisionCenterLabels
): string {
  return status === "completed"
    ? labels.evidenceCompleted
    : labels.evidencePending;
}

function nextActionText(
  kind: DecisionNextActionKind,
  labels: ResearchDecisionCenterLabels
): string {
  if (kind === "complete_validation") return labels.nextCompleteValidation;
  if (kind === "complete_robustness") return labels.nextCompleteRobustness;
  if (kind === "prepare_paper_trading") return labels.nextPreparePaper;
  if (kind === "continue_paper_observation") return labels.nextContinuePaper;
  if (kind === "archive_research") return labels.nextArchive;
  return labels.nextNone;
}

/**
 * Decision Center — research approval staging.
 * Presentation-only: never invents approvals, scores, or trading results.
 */
export default function ResearchDecisionCenter({
  research,
  validation,
  evaluation,
  labels,
  onContinue,
}: Props) {
  const model = buildDecisionCenterModel({
    research,
    validation,
    evaluation,
    hasSession: false,
    decisionNotes: null,
  });

  return (
    <section className="research-center" aria-labelledby="decision-center-title">
      <ResearchCenterHeader
        titleId="decision-center-title"
        title={labels.title}
        description={labels.summary}
      />

      {!model.hasValidationEvidence && !model.hasEvaluationEvidence ? (
        <EmptyState title={labels.noEvidenceTitle} description={labels.noEvidenceNote} />
      ) : null}

      <ResearchBand caption={labels.summaryTitle} glyph="decision">
        <ResearchKeyValueList
          items={[
            {
              id: "research",
              label: labels.summaryResearch,
              value: model.researchName,
            },
            {
              id: "experiment",
              label: labels.summaryExperiment,
              value: model.experimentLabel,
            },
            {
              id: "status",
              label: labels.summaryStatus,
              value: (
                <StatusBadge
                  label={statusLabel(model.decisionStatus, labels)}
                  variant={canonicalStatusVariant(statusTone(model.decisionStatus))}
                />
              ),
            },
          ]}
        />
      </ResearchBand>

      <hr className="overview-divider" />

      <ResearchBand caption={labels.evidenceTitle} glyph="evidence">
        <ResearchStatusMatrix
          items={model.evidence.map((item) => ({
            id: item.id,
            label: labels.evidenceLabels[item.id],
            statusLabel: evidenceLabel(item.status, labels),
            statusTone: item.status,
          }))}
        />
      </ResearchBand>

      <hr className="overview-divider" />

      <ResearchBand caption={labels.risksTitle} glyph="limitation">
        {model.remainingRiskIds.length === 0 ? (
          <EmptyState title={labels.risksEmptyTitle} description={labels.risksEmpty} />
        ) : (
          <ul className="research-plain-list">
            {model.remainingRiskIds.map((id) => (
              <li key={id}>{labels.riskLabels[id]}</li>
            ))}
          </ul>
        )}
      </ResearchBand>

      <hr className="overview-divider" />

      <ResearchBand caption={labels.checklistTitle} glyph="progress">
        <ResearchStatusMatrix
          items={model.checklist.map((item) => ({
            id: item.id,
            label: labels.checklistLabels[item.id],
            statusLabel:
              item.status === "completed"
                ? labels.checklistCompleted
                : labels.checklistPending,
            statusTone: item.status,
          }))}
        />
      </ResearchBand>

      <hr className="overview-divider" />

      <ResearchBand caption={labels.notesTitle} glyph="action">
        {model.decisionNotes ? (
          <p className="research-notes-body">{model.decisionNotes}</p>
        ) : (
          <EmptyState title={labels.notesEmptyTitle} description={labels.notesEmpty} />
        )}
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
