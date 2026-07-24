"use client";

import { useEffect, useState, type FormEvent } from "react";
import EmptyState from "@/components/ui/EmptyState";
import StatusBadge from "@/components/ui/StatusBadge";
import ResearchBand from "@/components/features/research/ux/ResearchBand";
import ResearchCenterHeader from "@/components/features/research/ux/ResearchCenterHeader";
import ResearchKeyValueList from "@/components/features/research/ux/ResearchKeyValueList";
import ResearchStatusMatrix from "@/components/features/research/ux/ResearchStatusMatrix";
import { canonicalStatusVariant } from "@/lib/researchStatusBadge";
import {
  buildDecisionCenterModel,
  type DecisionChecklistId,
  type DecisionEvidenceId,
  type DecisionEvidenceStatus,
  type DecisionRiskId,
  type DecisionStatus,
} from "@/lib/researchDecision";
import {
  getResearchDecisionRecord,
  saveResearchDecisionRecord,
  type ResearchDecisionOutcome,
  type ResearchDecisionRecord,
} from "@/lib/researchDecisionRecord";
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
  statusReady: string;
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
  recordTitle: string;
  recordDescription: string;
  outcomeLabel: string;
  outcomePromote: string;
  outcomeHold: string;
  outcomeReject: string;
  outcomeArchive: string;
  rationaleLabel: string;
  rationalePlaceholder: string;
  evidenceSummaryLabel: string;
  evidenceSummaryPlaceholder: string;
  reviewerNoteLabel: string;
  reviewerNotePlaceholder: string;
  saveDecision: string;
  savedDecision: string;
  localNote: string;
  humanDecisionNote: string;
  noEvidenceTitle: string;
  noEvidenceNote: string;
};

type Props = {
  research: ResearchDetail;
  validation: ResearchValidationResult | null;
  evaluation: ResearchEvaluationResult | null;
  factorValidationCompleted?: boolean;
  evidenceTimestamp?: string | null;
  labels: ResearchDecisionCenterLabels;
};

function statusLabel(
  status: DecisionStatus,
  labels: ResearchDecisionCenterLabels
): string {
  if (status === "not_ready") return labels.statusNotReady;
  if (status === "under_review") return labels.statusUnderReview;
  return labels.statusReady;
}

function statusTone(status: DecisionStatus): string {
  if (status === "ready") return "completed";
  if (status === "under_review") return "pending";
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

function outcomeLabel(
  outcome: ResearchDecisionOutcome,
  labels: ResearchDecisionCenterLabels
): string {
  if (outcome === "promote") return labels.outcomePromote;
  if (outcome === "reject") return labels.outcomeReject;
  if (outcome === "archive") return labels.outcomeArchive;
  return labels.outcomeHold;
}

export default function ResearchDecisionCenter({
  research,
  validation,
  evaluation,
  factorValidationCompleted = false,
  evidenceTimestamp = null,
  labels,
}: Props) {
  const model = buildDecisionCenterModel({
    research,
    validation,
    evaluation,
    factorValidationCompleted,
  });
  const [outcome, setOutcome] = useState<ResearchDecisionOutcome>("hold");
  const [rationale, setRationale] = useState("");
  const [evidenceSummary, setEvidenceSummary] = useState("");
  const [reviewerNote, setReviewerNote] = useState("");
  const [record, setRecord] = useState<ResearchDecisionRecord | null>(null);

  useEffect(() => {
    const existing = getResearchDecisionRecord(research.id);
    setRecord(existing);
    if (existing) {
      setOutcome(existing.outcome);
      setRationale(existing.rationale);
      setEvidenceSummary(existing.evidenceSummary ?? "");
      setReviewerNote(existing.reviewerNote ?? "");
    }
  }, [research.id]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (
      !rationale.trim() ||
      (outcome === "promote" && model.decisionStatus !== "ready")
    ) {
      return;
    }
    setRecord(
      saveResearchDecisionRecord({
        researchId: research.id,
        outcome,
        rationale,
        evidenceTimestamp:
          evidenceTimestamp ??
          validation?.generated_at ??
          evaluation?.generated_at ??
          null,
        evidenceSummary,
        reviewerNote,
      })
    );
  }

  return (
    <section className="research-center" aria-labelledby="decision-center-title">
      <ResearchCenterHeader
        titleId="decision-center-title"
        title={labels.title}
        description={labels.summary}
      />

      {!model.hasValidationEvidence && !model.hasEvaluationEvidence ? (
        <EmptyState
          title={labels.noEvidenceTitle}
          description={labels.noEvidenceNote}
        />
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
                  variant={canonicalStatusVariant(
                    statusTone(model.decisionStatus)
                  )}
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
          <EmptyState
            title={labels.risksEmptyTitle}
            description={labels.risksEmpty}
          />
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

      <ResearchBand caption={labels.recordTitle} glyph="action">
        <div className="decision-record">
          <div>
            <p className="research-status-block__body">
              {labels.recordDescription}
            </p>
            {record ? (
              <div className="decision-record__saved" role="status">
                <StatusBadge
                  label={outcomeLabel(record.outcome, labels)}
                  variant={
                    record.outcome === "promote"
                      ? "success"
                      : record.outcome === "reject" ||
                          record.outcome === "archive"
                        ? "danger"
                        : "warning"
                  }
                />
                <p>{record.rationale}</p>
                {record.evidenceSummary ? (
                  <p className="section-meta">{record.evidenceSummary}</p>
                ) : null}
                {record.reviewerNote ? (
                  <p className="section-meta">{record.reviewerNote}</p>
                ) : null}
                <span>
                  {labels.savedDecision} ·{" "}
                  {new Date(record.decidedAt).toLocaleString()}
                  {record.evidenceTimestamp
                    ? ` · evidence ${new Date(record.evidenceTimestamp).toLocaleString()}`
                    : ""}
                </span>
              </div>
            ) : null}
          </div>

          <form className="decision-record__form" onSubmit={handleSubmit}>
            <p className="section-meta">{labels.humanDecisionNote}</p>
            <label>
              <span>{labels.outcomeLabel}</span>
              <select
                value={outcome}
                onChange={(event) =>
                  setOutcome(event.target.value as ResearchDecisionOutcome)
                }
              >
                <option
                  value="promote"
                  disabled={model.decisionStatus !== "ready"}
                >
                  {labels.outcomePromote}
                </option>
                <option value="hold">{labels.outcomeHold}</option>
                <option value="reject">{labels.outcomeReject}</option>
                <option value="archive">{labels.outcomeArchive}</option>
              </select>
            </label>
            <label>
              <span>{labels.rationaleLabel}</span>
              <textarea
                value={rationale}
                onChange={(event) => setRationale(event.target.value)}
                placeholder={labels.rationalePlaceholder}
                rows={4}
                required
              />
            </label>
            <label>
              <span>{labels.evidenceSummaryLabel}</span>
              <textarea
                value={evidenceSummary}
                onChange={(event) => setEvidenceSummary(event.target.value)}
                placeholder={labels.evidenceSummaryPlaceholder}
                rows={2}
              />
            </label>
            <label>
              <span>{labels.reviewerNoteLabel}</span>
              <textarea
                value={reviewerNote}
                onChange={(event) => setReviewerNote(event.target.value)}
                placeholder={labels.reviewerNotePlaceholder}
                rows={2}
              />
            </label>
            <div className="decision-record__actions">
              <span>{labels.localNote}</span>
              <button
                type="submit"
                className="btn btn--primary"
                disabled={
                  !rationale.trim() ||
                  (outcome === "promote" && model.decisionStatus !== "ready")
                }
              >
                {labels.saveDecision}
              </button>
            </div>
          </form>
        </div>
      </ResearchBand>
    </section>
  );
}
