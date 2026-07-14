import type {
  EvaluationStatus,
  ResearchEvaluationResult,
} from "@/types/researchEvaluation";

/**
 * Enterprise governance dashboard for PR-010 evaluation evidence.
 *
 * This panel renders only backend-derived summarization of PR-009
 * validation evidence. It never renders a score, confidence, star rating,
 * or buy/sell recommendation — evaluation answers "do we have enough
 * trustworthy evidence to continue research?", not "should we buy?".
 */

export type ResearchEvaluationLabels = {
  title: string;
  summary: string;
  status: string;
  completed: string;
  incomplete: string;
  blocked: string;
  source: string;
  generated: string;
  coverageTitle: string;
  implementedStages: string;
  completedStagesCount: string;
  coveragePercentage: string;
  coverageDisclaimer: string;
  evidenceSummaryTitle: string;
  stageColumn: string;
  statusColumn: string;
  summaryColumn: string;
  completedEvidenceTitle: string;
  incompleteEvidenceTitle: string;
  outstandingEvidenceTitle: string;
  limitationsTitle: string;
  blockersTitle: string;
  none: string;
  notAvailable: string;
};

type Props = {
  evaluation: ResearchEvaluationResult;
  labels: ResearchEvaluationLabels;
};

function statusTone(status: string): string {
  if (status === "completed") return "success";
  if (status === "blocked" || status === "failed") return "danger";
  if (status === "incomplete") return "warning";
  return "neutral";
}

function statusLabel(
  status: EvaluationStatus | string,
  labels: ResearchEvaluationLabels
): string {
  if (status === "completed") return labels.completed;
  if (status === "incomplete") return labels.incomplete;
  if (status === "blocked") return labels.blocked;
  return status;
}

function EvidenceList({
  title,
  items,
  emptyLabel,
  tone,
}: {
  title: string;
  items: string[];
  emptyLabel: string;
  tone?: "warning" | "danger";
}) {
  return (
    <section className="evaluation-list-card" aria-label={title}>
      <h3>{title}</h3>
      {items.length === 0 ? (
        <p className="section-meta">{emptyLabel}</p>
      ) : (
        <ul
          className={
            tone
              ? `validation-evidence__list evaluation-list--${tone}`
              : "validation-evidence__list"
          }
        >
          {items.map((item, index) => (
            <li key={`${item}-${index}`}>{item}</li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default function ResearchEvaluationPanel({
  evaluation,
  labels,
}: Props) {
  const coverage = evaluation.evidence_coverage;
  const provenance = evaluation.provenance;

  return (
    <section
      className="research-evaluation"
      aria-labelledby="research-evaluation-title"
    >
      <header className="research-evaluation__header">
        <div>
          <h2 id="research-evaluation-title">{labels.title}</h2>
          <p>{labels.summary}</p>
        </div>
        <span
          className={`badge badge--${statusTone(evaluation.evaluation_status)}`}
        >
          {statusLabel(evaluation.evaluation_status, labels)}
        </span>
      </header>

      <dl className="validation-evidence__facts validation-evidence__facts--summary">
        <div>
          <dt>{labels.status}</dt>
          <dd>{statusLabel(evaluation.evaluation_status, labels)}</dd>
        </div>
        <div>
          <dt>{labels.source}</dt>
          <dd>
            {(provenance.market_data_provenance?.["source"] as string) ??
              (provenance.market_data_provenance?.["provider"] as string) ??
              labels.notAvailable}
          </dd>
        </div>
        <div>
          <dt>{labels.generated}</dt>
          <dd>{evaluation.generated_at}</dd>
        </div>
      </dl>

      <section
        className="evaluation-coverage-card"
        aria-labelledby="research-evaluation-coverage-title"
      >
        <h3 id="research-evaluation-coverage-title">{labels.coverageTitle}</h3>
        <dl className="validation-evidence__facts">
          <div>
            <dt>{labels.implementedStages}</dt>
            <dd>{coverage.implemented_stage_count}</dd>
          </div>
          <div>
            <dt>{labels.completedStagesCount}</dt>
            <dd>{coverage.completed_stage_count}</dd>
          </div>
          <div>
            <dt>{labels.coveragePercentage}</dt>
            <dd>{coverage.coverage_percentage}%</dd>
          </div>
        </dl>
        <div
          className="evaluation-coverage-bar"
          role="img"
          aria-label={`${coverage.coverage_percentage}%`}
        >
          <div
            className="evaluation-coverage-bar__fill"
            style={{ width: `${Math.min(100, Math.max(0, coverage.coverage_percentage))}%` }}
          />
        </div>
        <p className="validation-detail__note">{labels.coverageDisclaimer}</p>
      </section>

      <section
        className="evaluation-evidence-summary"
        aria-labelledby="research-evaluation-summary-title"
      >
        <h3 id="research-evaluation-summary-title">
          {labels.evidenceSummaryTitle}
        </h3>
        <div className="validation-table-wrap">
          <table className="data-table validation-table">
            <caption>{labels.evidenceSummaryTitle}</caption>
            <thead>
              <tr>
                <th>{labels.stageColumn}</th>
                <th>{labels.statusColumn}</th>
                <th>{labels.summaryColumn}</th>
              </tr>
            </thead>
            <tbody>
              {evaluation.evidence_summary.map((item) => (
                <tr key={item.stage}>
                  <th scope="row">{item.label}</th>
                  <td>
                    <span className={`badge badge--${statusTone(item.status)}`}>
                      {statusLabel(item.status, labels)}
                    </span>
                  </td>
                  <td>{item.summary}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="evaluation-list-grid">
        <EvidenceList
          title={labels.completedEvidenceTitle}
          items={evaluation.completed_stages}
          emptyLabel={labels.none}
        />
        <EvidenceList
          title={labels.incompleteEvidenceTitle}
          items={evaluation.incomplete_stages}
          emptyLabel={labels.none}
          tone="warning"
        />
        <EvidenceList
          title={labels.outstandingEvidenceTitle}
          items={evaluation.outstanding_evidence}
          emptyLabel={labels.none}
        />
        <EvidenceList
          title={labels.limitationsTitle}
          items={evaluation.limitations}
          emptyLabel={labels.none}
        />
      </div>

      <EvidenceList
        title={labels.blockersTitle}
        items={evaluation.blockers}
        emptyLabel={labels.none}
        tone="danger"
      />
    </section>
  );
}
