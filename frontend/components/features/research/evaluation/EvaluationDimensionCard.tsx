import type { Language } from "@/lib/i18n";
import {
  computeWeightedContribution,
} from "@/lib/researchEvaluation";
import type { EvaluationDimension } from "@/types/evaluation";
import EvidenceReferenceList from "@/components/features/research/validation/EvidenceReferenceList";
import EvaluationDimensionStatusBadge from "./EvaluationDimensionStatusBadge";

function formatDate(value: string, language: Language): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleDateString(language === "zh" ? "zh-CN" : "en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export type EvaluationDimensionCardLabels = {
  score: string;
  weight: string;
  contribution: string;
  evidence: string;
  evidenceEmpty: string;
  limitations: string;
  blocking: string;
  blockingYes: string;
  blockingNo: string;
  lastUpdated: string;
  expand: string;
  collapse: string;
  none: string;
};

type EvaluationDimensionCardProps = {
  dimension: EvaluationDimension;
  language: Language;
  labels: EvaluationDimensionCardLabels;
  expanded: boolean;
  onToggle: (key: string) => void;
};

export default function EvaluationDimensionCard({
  dimension,
  language,
  labels,
  expanded,
  onToggle,
}: EvaluationDimensionCardProps) {
  const contribution = computeWeightedContribution(
    dimension.score,
    dimension.weight
  );

  return (
    <article
      className={`evaluation-dimension-card${dimension.blocking ? " is-blocking" : ""}`}
    >
      <header className="evaluation-dimension-card__header">
        <div>
          <div className="evaluation-dimension-card__badges">
            <EvaluationDimensionStatusBadge status={dimension.status} />
            {dimension.blocking ? (
              <span className="badge badge--danger">{labels.blockingYes}</span>
            ) : null}
          </div>
          <h4 className="evaluation-dimension-card__name">{dimension.name}</h4>
          <p className="evaluation-dimension-card__summary">{dimension.summary}</p>
        </div>
        <button
          type="button"
          className="btn btn--ghost"
          onClick={() => onToggle(dimension.key)}
          aria-expanded={expanded}
        >
          {expanded ? labels.collapse : labels.expand}
        </button>
      </header>

      <dl className="evaluation-dimension-card__meta">
        <div>
          <dt>{labels.score}</dt>
          <dd className="font-mono">{dimension.score}</dd>
        </div>
        <div>
          <dt>{labels.weight}</dt>
          <dd className="font-mono">{dimension.weight}</dd>
        </div>
        <div>
          <dt>{labels.contribution}</dt>
          <dd className="font-mono">{contribution.toFixed(2)}</dd>
        </div>
        <div>
          <dt>{labels.lastUpdated}</dt>
          <dd>{formatDate(dimension.lastUpdatedAt, language)}</dd>
        </div>
        <div>
          <dt>{labels.blocking}</dt>
          <dd>
            {dimension.blocking ? labels.blockingYes : labels.blockingNo}
          </dd>
        </div>
      </dl>

      {expanded ? (
        <div className="evaluation-dimension-card__detail">
          <EvidenceReferenceList
            refs={dimension.evidenceRefs}
            title={labels.evidence}
            empty={labels.evidenceEmpty}
          />
          {dimension.evidenceLinks.length > 0 ? (
            <ul className="evaluation-dimension-card__links">
              {dimension.evidenceLinks.map((link) => (
                <li key={link.id}>
                  <strong>{link.claim}</strong>
                  <span className="font-mono"> → {link.evidenceRef}</span>
                  <p>{link.detail}</p>
                </li>
              ))}
            </ul>
          ) : null}
          <h5>{labels.limitations}</h5>
          {dimension.limitations.length === 0 ? (
            <p>{labels.none}</p>
          ) : (
            <ul>
              {dimension.limitations.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          )}
        </div>
      ) : null}
    </article>
  );
}
