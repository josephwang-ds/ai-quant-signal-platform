"use client";

import MetricSummaryCard from "@/components/ui/MetricSummaryCard";
import type { ResearchExecutionResult } from "@/types/researchExecution";
import type { ResearchValidationResult } from "@/types/researchValidation";

export type KeyResultsSummaryLabels = {
  strategyTotalReturn: string;
  benchmarkTotalReturn: string;
  maxDrawdown: string;
  oosSharpe: string;
  unavailable: string;
  oosSharpeUnavailable: string;
};

export type KeyResultsSummaryProps = {
  execution: ResearchExecutionResult | null;
  validation: ResearchValidationResult | null;
  labels: KeyResultsSummaryLabels;
};

function formatPct(value: number | null | undefined): string | null {
  if (value === null || value === undefined || Number.isNaN(value)) return null;
  return `${(value * 100).toFixed(1)}%`;
}

function formatNum2(value: number | null | undefined): string | null {
  if (value === null || value === undefined || Number.isNaN(value)) return null;
  return value.toFixed(2);
}

export default function KeyResultsSummary({
  execution,
  validation,
  labels,
}: KeyResultsSummaryProps) {
  if (!execution) {
    return <p className="section-meta">{labels.unavailable}</p>;
  }

  const oosSharpe = validation?.oos?.out_of_sample_metrics?.sharpe_ratio ?? null;
  const oosSharpeFormatted = formatNum2(oosSharpe);

  return (
    <div className="key-results-summary" role="list">
      <MetricSummaryCard
        label={labels.strategyTotalReturn}
        value={formatPct(execution.metrics?.total_return) ?? "—"}
      />
      <MetricSummaryCard
        label={labels.benchmarkTotalReturn}
        value={formatPct(execution.benchmark_metrics?.total_return) ?? "—"}
      />
      <MetricSummaryCard
        label={labels.maxDrawdown}
        value={formatPct(execution.metrics?.maximum_drawdown) ?? "—"}
      />
      <MetricSummaryCard
        label={labels.oosSharpe}
        value={oosSharpeFormatted ?? labels.oosSharpeUnavailable}
      />
    </div>
  );
}
