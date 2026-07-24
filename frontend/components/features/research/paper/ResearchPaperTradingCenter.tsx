"use client";

import { useEffect, useState, type FormEvent } from "react";
import EmptyState from "@/components/ui/EmptyState";
import StatusBadge from "@/components/ui/StatusBadge";
import ResearchBand from "@/components/features/research/ux/ResearchBand";
import ResearchCenterHeader from "@/components/features/research/ux/ResearchCenterHeader";
import ResearchKeyValueList from "@/components/features/research/ux/ResearchKeyValueList";
import { canonicalStatusVariant } from "@/lib/researchStatusBadge";
import {
  buildPaperTradingCenterModel,
  type PaperEligibilityReason,
  type PaperEligibilityStatus,
} from "@/lib/researchPaperTrading";
import {
  addPaperObservationEntry,
  completePaperObservationSession,
  getPaperObservationSession,
  startPaperObservationSession,
  type PaperObservationCadence,
  type PaperObservationSession,
} from "@/lib/researchPaperObservation";
import type { ResearchDetail } from "@/types/research";
import type { ResearchEvaluationResult } from "@/types/researchEvaluation";
import type { ResearchValidationResult } from "@/types/researchValidation";

export type ResearchPaperTradingCenterLabels = {
  title: string;
  summary: string;
  contextTitle: string;
  research: string;
  experiment: string;
  benchmark: string;
  eligibilityTitle: string;
  eligibilityNotEligible: string;
  eligibilityNeedsReview: string;
  eligibilityEligible: string;
  eligibilityActive: string;
  eligibilityCompleted: string;
  eligibilityReasonNoValidation: string;
  eligibilityReasonBlocked: string;
  eligibilityReasonIncomplete: string;
  eligibilityReasonEligible: string;
  eligibilityReasonActive: string;
  eligibilityReasonCompleted: string;
  planTitle: string;
  cadence: string;
  cadenceDaily: string;
  cadenceWeekly: string;
  cadenceMonthly: string;
  minimumDays: string;
  exitCriteria: string;
  exitCriteriaPlaceholder: string;
  startSession: string;
  activeSession: string;
  completedSession: string;
  startedAt: string;
  completedAt: string;
  completeSession: string;
  logTitle: string;
  logEmptyTitle: string;
  logEmptyBody: string;
  observationNote: string;
  observationPlaceholder: string;
  addObservation: string;
  localNote: string;
  continueDecision: string;
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
  return labels.eligibilityCompleted;
}

function eligibilityReason(
  reason: PaperEligibilityReason,
  labels: ResearchPaperTradingCenterLabels
): string {
  if (reason === "no_validation") return labels.eligibilityReasonNoValidation;
  if (reason === "blocked") return labels.eligibilityReasonBlocked;
  if (reason === "incomplete") return labels.eligibilityReasonIncomplete;
  if (reason === "eligible") return labels.eligibilityReasonEligible;
  if (reason === "active") return labels.eligibilityReasonActive;
  return labels.eligibilityReasonCompleted;
}

function cadenceLabel(
  cadence: PaperObservationCadence,
  labels: ResearchPaperTradingCenterLabels
): string {
  if (cadence === "daily") return labels.cadenceDaily;
  if (cadence === "monthly") return labels.cadenceMonthly;
  return labels.cadenceWeekly;
}

/**
 * Real paper-observation workflow: a user creates a bounded observation plan,
 * records dated notes, and closes the session. No trades or PnL are invented.
 */
export default function ResearchPaperTradingCenter({
  research,
  validation,
  evaluation,
  labels,
  onContinue,
  showHeader = true,
}: Props) {
  const [session, setSession] = useState<PaperObservationSession | null>(null);
  const [cadence, setCadence] = useState<PaperObservationCadence>("weekly");
  const [minimumDays, setMinimumDays] = useState(30);
  const [exitCriteria, setExitCriteria] = useState("");
  const [observation, setObservation] = useState("");

  useEffect(() => {
    setSession(getPaperObservationSession(research.id));
  }, [research.id]);

  const model = buildPaperTradingCenterModel({
    research,
    validation,
    evaluation,
    sessionStatus: session?.status ?? null,
  });

  function handleStart(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (model.eligibility !== "eligible" || !exitCriteria.trim()) return;
    setSession(
      startPaperObservationSession({
        researchId: research.id,
        cadence,
        minimumDays,
        exitCriteria,
      })
    );
  }

  function handleAddObservation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!observation.trim()) return;
    setSession(
      addPaperObservationEntry({
        researchId: research.id,
        note: observation,
      })
    );
    setObservation("");
  }

  return (
    <section
      className="research-center"
      aria-labelledby={showHeader ? "paper-observation-title" : undefined}
      aria-label={showHeader ? undefined : labels.title}
    >
      {showHeader ? (
        <ResearchCenterHeader
          titleId="paper-observation-title"
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

      <ResearchBand caption={labels.contextTitle} glyph="evidence">
        <ResearchKeyValueList
          items={[
            {
              id: "research",
              label: labels.research,
              value: model.researchName,
            },
            {
              id: "experiment",
              label: labels.experiment,
              value: model.experimentLabel,
            },
            {
              id: "benchmark",
              label: labels.benchmark,
              value: model.benchmark,
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

      <ResearchBand caption={labels.planTitle} glyph="progress">
        {!session ? (
          <form className="paper-observation-form" onSubmit={handleStart}>
            <label>
              <span>{labels.cadence}</span>
              <select
                value={cadence}
                onChange={(event) =>
                  setCadence(event.target.value as PaperObservationCadence)
                }
              >
                <option value="daily">{labels.cadenceDaily}</option>
                <option value="weekly">{labels.cadenceWeekly}</option>
                <option value="monthly">{labels.cadenceMonthly}</option>
              </select>
            </label>
            <label>
              <span>{labels.minimumDays}</span>
              <input
                type="number"
                min={1}
                value={minimumDays}
                onChange={(event) =>
                  setMinimumDays(Number(event.target.value) || 1)
                }
              />
            </label>
            <label className="paper-observation-form__wide">
              <span>{labels.exitCriteria}</span>
              <textarea
                value={exitCriteria}
                onChange={(event) => setExitCriteria(event.target.value)}
                placeholder={labels.exitCriteriaPlaceholder}
                rows={3}
                required
              />
            </label>
            <div className="paper-observation-form__actions">
              <span>{labels.localNote}</span>
              <button
                type="submit"
                className="btn btn--primary"
                disabled={
                  model.eligibility !== "eligible" || !exitCriteria.trim()
                }
              >
                {labels.startSession}
              </button>
            </div>
          </form>
        ) : (
          <div className="paper-observation-session">
            <div className="paper-observation-session__header">
              <StatusBadge
                label={
                  session.status === "active"
                    ? labels.activeSession
                    : labels.completedSession
                }
                variant={session.status === "active" ? "warning" : "success"}
              />
              {session.status === "active" ? (
                <button
                  type="button"
                  className="btn"
                  onClick={() =>
                    setSession(
                      completePaperObservationSession(research.id)
                    )
                  }
                >
                  {labels.completeSession}
                </button>
              ) : null}
            </div>
            <ResearchKeyValueList
              items={[
                {
                  id: "cadence",
                  label: labels.cadence,
                  value: cadenceLabel(session.cadence, labels),
                },
                {
                  id: "minimum-days",
                  label: labels.minimumDays,
                  value: String(session.minimumDays),
                },
                {
                  id: "started",
                  label: labels.startedAt,
                  value: new Date(session.startedAt).toLocaleString(),
                },
                ...(session.completedAt
                  ? [
                      {
                        id: "completed",
                        label: labels.completedAt,
                        value: new Date(session.completedAt).toLocaleString(),
                      },
                    ]
                  : []),
              ]}
            />
            <p className="paper-observation-session__criteria">
              <strong>{labels.exitCriteria}</strong>
              <span>{session.exitCriteria}</span>
            </p>
          </div>
        )}
      </ResearchBand>

      {session ? (
        <>
          <hr className="overview-divider" />
          <ResearchBand caption={labels.logTitle} glyph="action">
            {session.entries.length === 0 ? (
              <EmptyState
                title={labels.logEmptyTitle}
                description={labels.logEmptyBody}
              />
            ) : (
              <ol className="paper-observation-log">
                {session.entries.map((entry) => (
                  <li key={entry.id}>
                    <time>{new Date(entry.observedAt).toLocaleString()}</time>
                    <p>{entry.note}</p>
                  </li>
                ))}
              </ol>
            )}
            {session.status === "active" ? (
              <form
                className="paper-observation-entry"
                onSubmit={handleAddObservation}
              >
                <label>
                  <span>{labels.observationNote}</span>
                  <textarea
                    value={observation}
                    onChange={(event) => setObservation(event.target.value)}
                    placeholder={labels.observationPlaceholder}
                    rows={3}
                    required
                  />
                </label>
                <button
                  type="submit"
                  className="btn btn--primary"
                  disabled={!observation.trim()}
                >
                  {labels.addObservation}
                </button>
              </form>
            ) : onContinue ? (
              <button
                type="button"
                className="btn btn--primary"
                onClick={onContinue}
              >
                {labels.continueDecision}
              </button>
            ) : null}
          </ResearchBand>
        </>
      ) : null}
    </section>
  );
}
