import ConfidenceBadge from "@/components/ui/ConfidenceBadge";
import MetricSummaryCard from "@/components/ui/MetricSummaryCard";
import EvidenceSummary from "@/components/features/research/EvidenceSummary";
import LifecycleProgress from "@/components/features/research/LifecycleProgress";
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
};

export type OverviewSectionProps = {
  research: ResearchDetail;
  labels: OverviewSectionLabels;
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

/** Research Workspace Overview：问题、证据、生命周期与下一步。 */
export default function OverviewSection({ research, labels }: OverviewSectionProps) {
  return (
    <div className="research-overview">
      <div className="research-overview__metrics">
        <MetricSummaryCard
          label={labels.currentStage}
          value={research.currentStage}
          description={research.status}
          tone="emphasis"
        />
        <div className="research-overview__confidence">
          <p className="metric-summary-card__label">{labels.researchConfidence}</p>
          <ConfidenceBadge
            score={research.confidenceScore}
            label={labels.confidence}
          />
        </div>
        <MetricSummaryCard
          label={labels.currentRecommendation}
          value={research.currentRecommendation}
        />
      </div>

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
