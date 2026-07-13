import StatusBadge from "@/components/ui/StatusBadge";
import type { EvaluationIssue } from "@/types/evaluation";

export type EvaluationBlockersLabels = {
  blockersTitle: string;
  warningsTitle: string;
  missingTitle: string;
  severity: string;
  source: string;
  reason: string;
  evidence: string;
  nextAction: string;
  owner: string;
  due: string;
  emptyBlockers: string;
  emptyWarnings: string;
  emptyMissing: string;
};

type EvaluationBlockersProps = {
  issues: EvaluationIssue[];
  labels: EvaluationBlockersLabels;
};

function IssueList({
  title,
  items,
  empty,
  labels,
}: {
  title: string;
  items: EvaluationIssue[];
  empty: string;
  labels: EvaluationBlockersLabels;
}) {
  return (
    <section className="evaluation-issues" aria-label={title}>
      <h3 className="evaluation-issues__title">{title}</h3>
      {items.length === 0 ? (
        <p className="section-meta">{empty}</p>
      ) : (
        <ul className="evaluation-issues__list">
          {items.map((issue) => (
            <li key={issue.id} className="evaluation-issues__item">
              <div className="evaluation-issues__head">
                <StatusBadge
                  label={issue.severity}
                  variant={
                    issue.severity === "critical"
                      ? "danger"
                      : issue.severity === "warning"
                        ? "warning"
                        : "info"
                  }
                />
                <strong>{issue.sourceDimensionName}</strong>
              </div>
              <dl className="evaluation-issues__dl">
                <div>
                  <dt>{labels.reason}</dt>
                  <dd>{issue.reason}</dd>
                </div>
                <div>
                  <dt>{labels.evidence}</dt>
                  <dd className="font-mono">{issue.evidenceRef}</dd>
                </div>
                <div>
                  <dt>{labels.nextAction}</dt>
                  <dd>{issue.requiredNextAction}</dd>
                </div>
                <div>
                  <dt>{labels.owner}</dt>
                  <dd>{issue.owner}</dd>
                </div>
                <div>
                  <dt>{labels.due}</dt>
                  <dd>{issue.dueAt ?? "—"}</dd>
                </div>
              </dl>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default function EvaluationBlockers({
  issues,
  labels,
}: EvaluationBlockersProps) {
  const blockers = issues.filter((issue) => issue.kind === "blocker");
  const warnings = issues.filter((issue) => issue.kind === "warning");
  const missing = issues.filter((issue) => issue.kind === "missing_evidence");

  return (
    <div className="evaluation-blockers-group">
      <IssueList
        title={labels.blockersTitle}
        items={blockers}
        empty={labels.emptyBlockers}
        labels={labels}
      />
      <IssueList
        title={labels.warningsTitle}
        items={warnings}
        empty={labels.emptyWarnings}
        labels={labels}
      />
      <IssueList
        title={labels.missingTitle}
        items={missing}
        empty={labels.emptyMissing}
        labels={labels}
      />
    </div>
  );
}
