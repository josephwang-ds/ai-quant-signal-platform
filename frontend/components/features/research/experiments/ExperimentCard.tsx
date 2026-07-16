import type { Language } from "@/lib/i18n";
import { formatMetricValue } from "@/lib/researchExperiments";
import type { ResearchExperiment } from "@/types/experiment";
import ExperimentStatusBadge from "./ExperimentStatusBadge";
import ExperimentTypeBadge from "./ExperimentTypeBadge";
import { benchmarkLabel, ownerLabel, validationReadinessLabel } from "@/lib/researchDisplay";

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

export type ExperimentCardLabels = {
  hypothesis: string;
  dataset: string;
  window: string;
  benchmark: string;
  owner: string;
  updated: string;
  result: string;
  readiness: string;
  parameters: string;
  linkedNotes: string;
  openDetail: string;
  sharpe: string;
  maxDrawdown: string;
};

type ExperimentCardProps = {
  experiment: ResearchExperiment;
  language: Language;
  labels: ExperimentCardLabels;
  selected?: boolean;
  onSelect: (id: string) => void;
};

export default function ExperimentCard({
  experiment,
  language,
  labels,
  selected = false,
  onSelect,
}: ExperimentCardProps) {
  return (
    <article
      className={`experiment-card${selected ? " is-selected" : ""}`}
      role="article"
    >
      <header className="experiment-card__header">
        <div className="experiment-card__title-block">
          <h3 className="experiment-card__name">{experiment.name}</h3>
          <div className="experiment-card__badges">
            <ExperimentStatusBadge status={experiment.status} language={language} />
            <ExperimentTypeBadge experimentType={experiment.experimentType} language={language} />
          </div>
        </div>
        <button
          type="button"
          className="btn btn--ghost"
          onClick={() => onSelect(experiment.id)}
        >
          {labels.openDetail}
        </button>
      </header>

      <p className="experiment-card__hypothesis">
        <span className="experiment-card__label">{labels.hypothesis}</span>
        {experiment.hypothesis}
      </p>

      <dl className="experiment-card__meta">
        <div>
          <dt>{labels.dataset}</dt>
          <dd>{experiment.datasetOrSymbol}</dd>
        </div>
        <div>
          <dt>{labels.window}</dt>
          <dd className="font-mono">
            {experiment.startDate} → {experiment.endDate}
          </dd>
        </div>
        <div>
          <dt>{labels.benchmark}</dt>
          <dd>{benchmarkLabel(experiment.benchmark, language)}</dd>
        </div>
        <div>
          <dt>{labels.owner}</dt>
          <dd>{ownerLabel(experiment.owner, language)}</dd>
        </div>
        <div>
          <dt>{labels.updated}</dt>
          <dd>{formatDate(experiment.updatedAt, language)}</dd>
        </div>
        <div>
          <dt>{labels.readiness}</dt>
          <dd>{validationReadinessLabel(experiment.validationReadiness, language)}</dd>
        </div>
      </dl>

      <p className="experiment-card__params">
        <span className="experiment-card__label">{labels.parameters}</span>
        {experiment.parameters.length > 0
          ? experiment.parameters
              .slice(0, 4)
              .map((parameter) => `${parameter.key}=${parameter.value}`)
              .join(" · ")
          : "—"}
      </p>

      <p className="experiment-card__result">
        <span className="experiment-card__label">{labels.result}</span>
        {experiment.resultSummary}
      </p>

      <p className="experiment-card__metrics section-meta">
        {labels.sharpe}: {formatMetricValue(experiment.metrics.sharpe, "sharpe")}
        {" · "}
        {labels.maxDrawdown}:{" "}
        {formatMetricValue(experiment.metrics.maxDrawdown, "maxDrawdown")}
      </p>
    </article>
  );
}
