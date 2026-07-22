import MetricSummaryCard from "@/components/ui/MetricSummaryCard";
import type { ExperimentMetrics } from "@/types/experiment";
import { formatMetricValue } from "@/lib/researchExperiments";
import {
  getDrawdownTone,
  getReturnTone,
  getSharpeTone,
  type MetricTone,
} from "@/lib/formatters";

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

function toneForMetric(
  key: keyof ExperimentMetrics,
  value: number | null
): MetricTone | "emphasis" | undefined {
  if (key === "sharpe") return getSharpeTone(value);
  if (key === "cagr" || key === "winRate") return getReturnTone(value);
  if (key === "maxDrawdown") return getDrawdownTone(value);
  return undefined;
}

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
      <div className="experiment-metrics__grid" role="list">
        {METRIC_KEYS.map((key) => (
          <MetricSummaryCard
            key={key}
            label={labelMap[key]}
            value={formatMetricValue(metrics[key], key)}
            tone={toneForMetric(key, metrics[key])}
          />
        ))}
      </div>
    </section>
  );
}
