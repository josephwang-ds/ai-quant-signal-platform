import type { ExperimentMetrics } from "@/types/experiment";
import { formatMetricValue } from "@/lib/researchExperiments";

export type ExperimentMetricsLabels = {
  title: string;
  disclaimer: string;
  sharpe: string;
  cagr: string;
  maxDrawdown: string;
  volatility: string;
  tradeCount: string;
  winRate: string;
  totalTransactionCost: string;
};

type ExperimentMetricsPanelProps = {
  metrics: ExperimentMetrics;
  labels: ExperimentMetricsLabels;
};

const METRIC_KEYS: (keyof ExperimentMetrics)[] = [
  "sharpe",
  "cagr",
  "maxDrawdown",
  "volatility",
  "tradeCount",
  "winRate",
  "totalTransactionCost",
];

export default function ExperimentMetricsPanel({
  metrics,
  labels,
}: ExperimentMetricsPanelProps) {
  const labelMap: Record<keyof ExperimentMetrics, string> = {
    sharpe: labels.sharpe,
    cagr: labels.cagr,
    maxDrawdown: labels.maxDrawdown,
    volatility: labels.volatility,
    tradeCount: labels.tradeCount,
    winRate: labels.winRate,
    totalTransactionCost: labels.totalTransactionCost,
  };

  return (
    <section className="experiment-metrics" aria-label={labels.title}>
      <h4 className="experiment-metrics__title">{labels.title}</h4>
      <p className="section-meta">{labels.disclaimer}</p>
      <dl className="experiment-metrics__grid">
        {METRIC_KEYS.map((key) => (
          <div key={key} className="experiment-metrics__item">
            <dt>{labelMap[key]}</dt>
            <dd className="font-mono">{formatMetricValue(metrics[key], key)}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
