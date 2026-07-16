import MetricSummaryCard from "@/components/ui/MetricSummaryCard";

export type ResearchWorkspaceSummaryProps = {
  total: number;
  defined: number;
  evidenceAvailable: number;
  reviewOrArchived: number;
  labels: {
    ariaLabel: string;
    research: string;
    defined: string;
    evidenceAvailable: string;
    reviewOrArchived: string;
  };
};

/** Workspace-level KPI strip above the Research List. */
export default function ResearchWorkspaceSummary({
  total,
  defined,
  evidenceAvailable,
  reviewOrArchived,
  labels,
}: ResearchWorkspaceSummaryProps) {
  return (
    <div className="research-workspace-summary" aria-label={labels.ariaLabel}>
      <MetricSummaryCard label={labels.research} value={String(total)} tone="emphasis" />
      <MetricSummaryCard label={labels.defined} value={String(defined)} />
      <MetricSummaryCard
        label={labels.evidenceAvailable}
        value={String(evidenceAvailable)}
      />
      <MetricSummaryCard
        label={labels.reviewOrArchived}
        value={String(reviewOrArchived)}
      />
    </div>
  );
}
