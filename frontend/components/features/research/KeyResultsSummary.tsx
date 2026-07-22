import EmptyState from "@/components/ui/EmptyState";
import MetricSummaryCard from "@/components/ui/MetricSummaryCard";
import type { ResearchExecutionResult } from "@/types/researchExecution";
import type { ResearchValidationResult } from "@/types/researchValidation";
import {
  formatMetricPercent,
  formatMetricSharpe,
  getDrawdownTone,
  getReturnTone,
  getSharpeTone,
} from "@/lib/formatters";

export type KeyResultsSummaryLabels = {
  strategyTotalReturn: string;
  benchmarkTotalReturn: string;
  maxDrawdown: string;
  oosSharpe: string;
  unavailable: string;
  unavailableTitle: string;
  oosSharpeUnavailable: string;
};

export type KeyResultsSummaryProps = {
  execution: ResearchExecutionResult | null;
  validation: ResearchValidationResult | null;
  labels: KeyResultsSummaryLabels;
};

export default function KeyResultsSummary({
  execution,
  validation,
  labels,
}: KeyResultsSummaryProps) {
  if (!execution) {
    return (
      <EmptyState
        title={labels.unavailableTitle}
        description={labels.unavailable}
      />
    );
  }

  const strategyReturn = execution.metrics?.total_return ?? null;
  const benchmarkReturn = execution.benchmark_metrics?.total_return ?? null;
  const maxDrawdown = execution.metrics?.maximum_drawdown ?? null;
  const oosSharpe = validation?.oos?.out_of_sample_metrics?.sharpe_ratio ?? null;

  return (
    <div className="key-results-summary" role="list">
      <MetricSummaryCard
        label={labels.strategyTotalReturn}
        value={formatMetricPercent(strategyReturn)}
        tone={getReturnTone(strategyReturn)}
      />
      <MetricSummaryCard
        label={labels.benchmarkTotalReturn}
        value={formatMetricPercent(benchmarkReturn)}
        tone={getReturnTone(benchmarkReturn)}
      />
      <MetricSummaryCard
        label={labels.maxDrawdown}
        value={formatMetricPercent(maxDrawdown)}
        tone={getDrawdownTone(maxDrawdown)}
      />
      <MetricSummaryCard
        label={labels.oosSharpe}
        value={
          oosSharpe == null
            ? labels.oosSharpeUnavailable
            : formatMetricSharpe(oosSharpe)
        }
        tone={getSharpeTone(oosSharpe)}
      />
    </div>
  );
}
