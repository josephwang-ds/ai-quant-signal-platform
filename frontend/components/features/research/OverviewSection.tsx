import EvaluationPendingNotice from "@/components/features/research/EvaluationPendingNotice";
import type { ReactNode } from "react";
import type { ResearchDetail } from "@/types/research";
import {
  isCompletedStatus,
  isRunningStatus,
} from "@/lib/researchRepository";

export type OverviewSectionLabels = {
  researchQuestion: string;
  owner: string;
  benchmark: string;
  strategy: string;
  created: string;
  progressTitle: string;
  progressResearch: string;
  progressExperiments: string;
  progressEvidence: string;
  progressDecision: string;
  quickActionsTitle: string;
  runExperiment: string;
  openValidation: string;
  generateReview: string;
  recentExperimentsTitle: string;
  latestEvidenceTitle: string;
  currentDecisionTitle: string;
  confidence: string;
  noExperiments: string;
  noEvidence: string;
  decisionPending: string;
  // Kept for backward-compatible test props / callers
  hypothesis?: string;
  researchObjective?: string;
  currentStage?: string;
  researchConfidence?: string;
  currentRecommendation?: string;
  researchSummary?: string;
  evidenceNarrative?: string;
  validationSummary?: string;
  keyStrengths?: string;
  knownWeaknesses?: string;
  openQuestions?: string;
  nextActions?: string;
  lifecycleTitle?: string;
  lifecycleDescription?: string;
  evidenceTitle?: string;
  evidenceDescription?: string;
  strategyConfig?: string;
  dataRequirements?: string;
  symbol?: string;
  dataStatus?: string;
  metricsStatus?: string;
  calculatedMetricsTitle?: string;
  metricTotalReturn?: string;
  metricBenchmarkReturn?: string;
  metricCagr?: string;
  metricSharpe?: string;
  metricMaxDd?: string;
  metricVol?: string;
  metricTrades?: string;
};

export type OverviewCalculatedMetrics = {
  totalReturn: string;
  benchmarkReturn: string;
  cagr: string;
  sharpe: string;
  maxDrawdown: string;
  volatility: string;
  tradeCount: string;
};

export type OverviewQuickActionHandlers = {
  onRunExperiment?: () => void;
  onOpenValidation?: () => void;
  onGenerateReview?: () => void;
};

export type OverviewSectionProps = {
  research: ResearchDetail;
  labels: OverviewSectionLabels;
  calculatedMetrics?: OverviewCalculatedMetrics | null;
  provenanceSlot?: ReactNode;
  quickActions?: OverviewQuickActionHandlers;
  recentExperimentLabels?: string[];
};

type ProgressLevel = 0 | 1 | 2 | 3 | 4 | 5;

function progressBar(level: ProgressLevel): string {
  const filled = "█".repeat(level);
  const empty = "░".repeat(5 - level);
  return `${filled}${empty}`;
}

function researchProgress(research: ResearchDetail): ProgressLevel {
  if (research.status === "Archived") return 5;
  if (isCompletedStatus(research.status)) return 4;
  if (isRunningStatus(research.status) || research.status === "Review") return 3;
  if (research.status === "Draft") return 1;
  return 2;
}

function experimentsProgress(research: ResearchDetail): ProgressLevel {
  if (research.experimentCount <= 0) return 1;
  if (research.experimentCount === 1) return 2;
  if (research.experimentCount <= 3) return 3;
  return 4;
}

function evidenceProgress(research: ResearchDetail): ProgressLevel {
  const status = research.integrity.validationStatus.toLowerCase();
  if (status.includes("complete") || status.includes("pass")) return 4;
  if (status.includes("running") || status.includes("progress")) return 3;
  if (status.includes("await") || status.includes("pending") || status.includes("not"))
    return 2;
  return 2;
}

function decisionProgress(research: ResearchDetail): ProgressLevel {
  if (
    research.status === "Paper Trading" ||
    research.status === "Monitoring" ||
    research.status === "Validated"
  ) {
    return 3;
  }
  if (research.status === "Review") return 2;
  return 1;
}

/** Research Workspace Overview — hero signals, progress, actions (Sprint 1 IA). */
export default function OverviewSection({
  research,
  labels,
  calculatedMetrics = null,
  provenanceSlot = null,
  quickActions,
  recentExperimentLabels = [],
}: OverviewSectionProps) {
  const experiments =
    recentExperimentLabels.length > 0
      ? recentExperimentLabels
      : research.experimentCount > 0
        ? [
            `Experiment #001 · ${research.configuration.strategyName}`,
            research.experimentCount > 1
              ? "Experiment #002 · Validation track"
              : null,
            research.experimentCount > 2
              ? "Experiment #003 · Robustness track"
              : null,
          ].filter(Boolean) as string[]
        : [];

  const latestEvidence =
    research.evidenceItems.slice(0, 3).map((item) => item.label) ?? [];

  return (
    <div className="research-overview research-overview--workspace">
      <section className="overview-block overview-block--featured" aria-label={labels.researchQuestion}>
        <h3 className="overview-block__title">{labels.researchQuestion}</h3>
        <p className="overview-block__body overview-block__body--lead">
          {research.researchQuestion}
        </p>
        <div className="research-overview-hero__status">
          <p className="research-overview__publicity">
            {research.integrity.publicityLabel}
          </p>
          <EvaluationPendingNotice
            label={labels.confidence}
            message={research.integrity.evaluationPendingMessage}
          />
        </div>
        <dl className="research-overview-hero__meta">
          <div>
            <dt>{labels.owner}</dt>
            <dd>{research.owner}</dd>
          </div>
          <div>
            <dt>{labels.benchmark}</dt>
            <dd>{research.configuration.benchmark}</dd>
          </div>
          <div>
            <dt>{labels.strategy}</dt>
            <dd>{research.configuration.strategyName}</dd>
          </div>
          <div>
            <dt>{labels.created}</dt>
            <dd>{research.createdAt.slice(0, 10)}</dd>
          </div>
        </dl>
      </section>

      {provenanceSlot}

      <section className="overview-block" aria-label={labels.progressTitle}>
        <h3 className="overview-block__title">{labels.progressTitle}</h3>
        <dl className="research-progress-bars">
          <div>
            <dt>{labels.progressResearch}</dt>
            <dd className="font-mono" aria-label={`${labels.progressResearch} ${researchProgress(research)} of 5`}>
              {progressBar(researchProgress(research))}
            </dd>
          </div>
          <div>
            <dt>{labels.progressExperiments}</dt>
            <dd className="font-mono">
              {progressBar(experimentsProgress(research))}
            </dd>
          </div>
          <div>
            <dt>{labels.progressEvidence}</dt>
            <dd className="font-mono">
              {progressBar(evidenceProgress(research))}
            </dd>
          </div>
          <div>
            <dt>{labels.progressDecision}</dt>
            <dd className="font-mono">
              {progressBar(decisionProgress(research))}
            </dd>
          </div>
        </dl>
      </section>

      <section className="overview-block" aria-label={labels.quickActionsTitle}>
        <h3 className="overview-block__title">{labels.quickActionsTitle}</h3>
        <div className="research-overview-actions">
          <button
            type="button"
            className="btn btn--primary"
            onClick={quickActions?.onRunExperiment}
          >
            {labels.runExperiment}
          </button>
          <button
            type="button"
            className="btn"
            onClick={quickActions?.onOpenValidation}
          >
            {labels.openValidation}
          </button>
          <button
            type="button"
            className="btn"
            onClick={quickActions?.onGenerateReview}
          >
            {labels.generateReview}
          </button>
        </div>
      </section>

      <div className="research-overview__grid">
        <section className="overview-block">
          <h3 className="overview-block__title">
            {labels.recentExperimentsTitle}
          </h3>
          {experiments.length > 0 ? (
            <ul className="overview-block__list">
              {experiments.map((label) => (
                <li key={label}>{label}</li>
              ))}
            </ul>
          ) : (
            <p className="overview-block__body">{labels.noExperiments}</p>
          )}
        </section>

        <section className="overview-block">
          <h3 className="overview-block__title">{labels.latestEvidenceTitle}</h3>
          {latestEvidence.length > 0 ? (
            <ul className="overview-block__list">
              {latestEvidence.map((label) => (
                <li key={label}>{label}</li>
              ))}
            </ul>
          ) : (
            <p className="overview-block__body">{labels.noEvidence}</p>
          )}
          <p className="overview-block__body section-meta">
            {research.evidenceSummary}
          </p>
        </section>
      </div>

      <section className="overview-block">
        <h3 className="overview-block__title">{labels.currentDecisionTitle}</h3>
        <p className="overview-block__body overview-block__body--lead">
          {research.currentRecommendation || labels.decisionPending}
        </p>
        {/* Keep symbol visible for authenticity / regression tests */}
        <p className="section-meta font-mono">{research.configuration.symbol}</p>
      </section>

      {calculatedMetrics ? (
        <p className="section-meta">
          {labels.calculatedMetricsTitle ?? "Calculated metrics"} available in
          Experiments after execution — not shown on the overview surface.
        </p>
      ) : null}
    </div>
  );
}
