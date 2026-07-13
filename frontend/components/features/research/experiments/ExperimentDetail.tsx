import Button from "@/components/ui/Button";
import type { Language } from "@/lib/i18n";
import type { ResearchExperiment } from "@/types/experiment";
import ExperimentLifecycle, {
  type ExperimentLifecycleLabels,
} from "./ExperimentLifecycle";
import ExperimentMetricsPanel, {
  type ExperimentMetricsLabels,
} from "./ExperimentMetrics";
import ExperimentStatusBadge from "./ExperimentStatusBadge";
import ExperimentTypeBadge from "./ExperimentTypeBadge";

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

export type ExperimentDetailLabels = {
  title: string;
  close: string;
  overview: string;
  hypothesis: string;
  configuration: string;
  parameters: string;
  results: string;
  notes: string;
  relatedEvidence: string;
  linkedNotebook: string;
  validationReadiness: string;
  dataset: string;
  window: string;
  benchmark: string;
  owner: string;
  created: string;
  updated: string;
  success: string;
  falsification: string;
  none: string;
  lifecycle: ExperimentLifecycleLabels;
  metrics: ExperimentMetricsLabels;
};

type ExperimentDetailProps = {
  experiment: ResearchExperiment;
  language: Language;
  labels: ExperimentDetailLabels;
  onClose: () => void;
};

export default function ExperimentDetail({
  experiment,
  language,
  labels,
  onClose,
}: ExperimentDetailProps) {
  return (
    <section className="experiment-detail" aria-label={labels.title}>
      <header className="experiment-detail__header">
        <div>
          <div className="experiment-detail__badges">
            <ExperimentStatusBadge status={experiment.status} />
            <ExperimentTypeBadge experimentType={experiment.experimentType} />
          </div>
          <h3 className="experiment-detail__name">{experiment.name}</h3>
        </div>
        <Button className="btn--ghost" onClick={onClose}>
          {labels.close}
        </Button>
      </header>

      <ExperimentLifecycle status={experiment.status} labels={labels.lifecycle} />

      <div className="experiment-detail__grid">
        <section className="experiment-detail__block">
          <h4>{labels.overview}</h4>
          <dl className="experiment-detail__dl">
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
              <dd>{experiment.benchmark}</dd>
            </div>
            <div>
              <dt>{labels.owner}</dt>
              <dd>{experiment.owner}</dd>
            </div>
            <div>
              <dt>{labels.created}</dt>
              <dd>{formatDate(experiment.createdAt, language)}</dd>
            </div>
            <div>
              <dt>{labels.updated}</dt>
              <dd>{formatDate(experiment.updatedAt, language)}</dd>
            </div>
            <div>
              <dt>{labels.validationReadiness}</dt>
              <dd>{experiment.validationReadiness}</dd>
            </div>
          </dl>
        </section>

        <section className="experiment-detail__block">
          <h4>{labels.hypothesis}</h4>
          <p>{experiment.hypothesis}</p>
          <h4>{labels.success}</h4>
          <p>{experiment.successCriteria}</p>
          <h4>{labels.falsification}</h4>
          <p>{experiment.falsificationCondition}</p>
        </section>
      </div>

      <section className="experiment-detail__block">
        <h4>{labels.configuration} / {labels.parameters}</h4>
        {experiment.parameters.length > 0 ? (
          <ul className="experiment-detail__params">
            {experiment.parameters.map((parameter) => (
              <li key={`${parameter.key}-${parameter.value}`}>
                <span className="font-mono">{parameter.key}</span>
                {" = "}
                <span className="font-mono">{parameter.value}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="section-meta">{labels.none}</p>
        )}
      </section>

      <section className="experiment-detail__block">
        <h4>{labels.results}</h4>
        <p>{experiment.resultSummary}</p>
      </section>

      <ExperimentMetricsPanel metrics={experiment.metrics} labels={labels.metrics} />

      <div className="experiment-detail__grid">
        <section className="experiment-detail__block">
          <h4>{labels.notes}</h4>
          <p>{experiment.notes || labels.none}</p>
        </section>
        <section className="experiment-detail__block">
          <h4>{labels.relatedEvidence}</h4>
          {experiment.relatedEvidenceIds.length > 0 ? (
            <ul>
              {experiment.relatedEvidenceIds.map((id) => (
                <li key={id} className="font-mono">
                  {id}
                </li>
              ))}
            </ul>
          ) : (
            <p className="section-meta">{labels.none}</p>
          )}
          <h4>{labels.linkedNotebook}</h4>
          {experiment.linkedNotebookEntryIds.length > 0 ? (
            <ul>
              {experiment.linkedNotebookEntryIds.map((id) => (
                <li key={id} className="font-mono">
                  {id}
                </li>
              ))}
            </ul>
          ) : (
            <p className="section-meta">{labels.none}</p>
          )}
        </section>
      </div>
    </section>
  );
}
