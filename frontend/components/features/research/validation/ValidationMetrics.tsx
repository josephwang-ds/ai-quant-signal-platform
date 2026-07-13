import type { ValidationMetric } from "@/types/validation";

export type ValidationMetricsLabels = {
  title: string;
  disclaimer: string;
  historical: string;
  simulated: string;
};

type ValidationMetricsProps = {
  metrics: ValidationMetric[];
  labels: ValidationMetricsLabels;
};

export default function ValidationMetrics({
  metrics,
  labels,
}: ValidationMetricsProps) {
  if (metrics.length === 0) {
    return null;
  }

  return (
    <section className="validation-metrics" aria-label={labels.title}>
      <h4 className="validation-metrics__title">{labels.title}</h4>
      <p className="section-meta">{labels.disclaimer}</p>
      <dl className="validation-metrics__grid">
        {metrics.map((metric) => (
          <div key={metric.key} className="validation-metrics__item">
            <dt>
              {metric.label}
              <span className="validation-metrics__basis">
                {" "}
                (
                {metric.basis === "historical"
                  ? labels.historical
                  : labels.simulated}
                )
              </span>
            </dt>
            <dd className="font-mono">{metric.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
