import EvaluationPendingNotice from "@/components/features/research/EvaluationPendingNotice";
import MetricSummaryCard from "@/components/ui/MetricSummaryCard";
import EvidenceSummary from "@/components/features/research/EvidenceSummary";
import LifecycleProgress from "@/components/features/research/LifecycleProgress";
import type { ReactNode } from "react";
import type { ResearchDetail } from "@/types/research";

export type OverviewSectionLabels = {
  researchQuestion: string;
  hypothesis: string;
  researchObjective: string;
  currentStage: string;
  researchConfidence: string;
  currentRecommendation: string;
  researchSummary: string;
  evidenceNarrative: string;
  validationSummary: string;
  keyStrengths: string;
  knownWeaknesses: string;
  openQuestions: string;
  nextActions: string;
  lifecycleTitle: string;
  lifecycleDescription: string;
  evidenceTitle: string;
  evidenceDescription: string;
  confidence: string;
  strategyConfig: string;
  dataRequirements: string;
  symbol: string;
  benchmark: string;
  strategy: string;
  dataStatus: string;
  metricsStatus: string;
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

export type OverviewSectionProps = {
  research: ResearchDetail;
  labels: OverviewSectionLabels;
  calculatedMetrics?: OverviewCalculatedMetrics | null;
  provenanceSlot?: ReactNode;
};

function BulletList({ items, title }: { items: string[]; title: string }) {
  return (
    <section className="overview-block">
      <h3 className="overview-block__title">{title}</h3>
      <ul className="overview-block__list">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

/** Research Workspace Overview：问题、配置、生命周期；可选展示真实计算结果。 */
export default function OverviewSection({
  research,
  labels,
  calculatedMetrics = null,
  provenanceSlot = null,
}: OverviewSectionProps) {
  return (
    <div className="research-overview">
      <p className="research-overview__publicity">{research.integrity.publicityLabel}</p>
      <p className="research-overview__explain">{research.integrity.explanatoryText}</p>
      {provenanceSlot}

      <div className="research-overview__metrics">
        <MetricSummaryCard
          label={labels.currentStage}
          value={research.currentStage}
          description={research.status}
          tone="emphasis"
        />
        <div className="research-overview__confidence">
          <p className="metric-summary-card__label">{labels.researchConfidence}</p>
          <EvaluationPendingNotice
            label={labels.confidence}
            message={research.integrity.evaluationPendingMessage}
          />
        </div>
        <MetricSummaryCard
          label={labels.currentRecommendation}
          value={research.currentRecommendation}
        />
      </div>

      {calculatedMetrics ? (
        <section
          className="overview-block"
          aria-label={labels.calculatedMetricsTitle ?? "Calculated metrics"}
        >
          <h3 className="overview-block__title">
            {labels.calculatedMetricsTitle ?? "Calculated backtest metrics"}
          </h3>
          <dl className="overview-block__config">
            <div>
              <dt>{labels.metricTotalReturn ?? "Total return"}</dt>
              <dd className="font-mono">{calculatedMetrics.totalReturn}</dd>
            </div>
            <div>
              <dt>{labels.metricBenchmarkReturn ?? "Benchmark total return"}</dt>
              <dd className="font-mono">{calculatedMetrics.benchmarkReturn}</dd>
            </div>
            <div>
              <dt>{labels.metricCagr ?? "CAGR"}</dt>
              <dd className="font-mono">{calculatedMetrics.cagr}</dd>
            </div>
            <div>
              <dt>{labels.metricSharpe ?? "Sharpe"}</dt>
              <dd className="font-mono">{calculatedMetrics.sharpe}</dd>
            </div>
            <div>
              <dt>{labels.metricMaxDd ?? "Max drawdown"}</dt>
              <dd className="font-mono">{calculatedMetrics.maxDrawdown}</dd>
            </div>
            <div>
              <dt>{labels.metricVol ?? "Ann. volatility"}</dt>
              <dd className="font-mono">{calculatedMetrics.volatility}</dd>
            </div>
            <div>
              <dt>{labels.metricTrades ?? "Trade count"}</dt>
              <dd className="font-mono">{calculatedMetrics.tradeCount}</dd>
            </div>
          </dl>
        </section>
      ) : null}

      <section className="overview-block overview-block--featured">
        <h3 className="overview-block__title">{labels.researchQuestion}</h3>
        <p className="overview-block__body overview-block__body--lead">
          {research.researchQuestion}
        </p>
      </section>

      <div className="research-overview__grid">
        <section className="overview-block">
          <h3 className="overview-block__title">{labels.hypothesis}</h3>
          <p className="overview-block__body">{research.hypothesis}</p>
        </section>
        <section className="overview-block">
          <h3 className="overview-block__title">{labels.researchObjective}</h3>
          <p className="overview-block__body">{research.researchObjective}</p>
        </section>
      </div>

      <section className="overview-block">
        <h3 className="overview-block__title">{labels.strategyConfig}</h3>
        <dl className="overview-block__config">
          <div>
            <dt>{labels.symbol}</dt>
            <dd className="font-mono">{research.configuration.symbol}</dd>
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
            <dt>{labels.dataStatus}</dt>
            <dd>{research.integrity.dataStatus}</dd>
          </div>
          <div>
            <dt>{labels.metricsStatus}</dt>
            <dd>{research.integrity.metricsStatus}</dd>
          </div>
        </dl>
        <ul className="overview-block__list">
          {research.configuration.parameterLines.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      </section>

      <BulletList
        title={labels.dataRequirements}
        items={research.configuration.dataRequirements}
      />

      <LifecycleProgress
        currentStage={research.currentStage}
        title={labels.lifecycleTitle}
        description={labels.lifecycleDescription}
      />

      <section className="overview-block">
        <h3 className="overview-block__title">{labels.researchSummary}</h3>
        <p className="overview-block__body">{research.researchSummary}</p>
      </section>

      <section className="overview-block">
        <h3 className="overview-block__title">{labels.evidenceNarrative}</h3>
        <p className="overview-block__body">{research.evidenceSummary}</p>
      </section>

      <EvidenceSummary
        items={research.evidenceItems}
        title={labels.evidenceTitle}
        description={labels.evidenceDescription}
      />

      <section className="overview-block">
        <h3 className="overview-block__title">{labels.validationSummary}</h3>
        <p className="overview-block__body">{research.validationSummary}</p>
      </section>

      <div className="research-overview__grid">
        <BulletList title={labels.keyStrengths} items={research.keyStrengths} />
        <BulletList title={labels.knownWeaknesses} items={research.knownWeaknesses} />
      </div>

      <div className="research-overview__grid">
        <BulletList title={labels.openQuestions} items={research.openQuestions} />
        <BulletList title={labels.nextActions} items={research.nextActions} />
      </div>
    </div>
  );
}
