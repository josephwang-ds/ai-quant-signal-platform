import type { Language } from "@/lib/i18n";
import type { EvaluationRecommendationPanel } from "@/types/evaluation";
import StatusBadge from "@/components/ui/StatusBadge";

function formatDate(value: string, language: Language): string {
  if (value === "—") {
    return value;
  }
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

export type EvaluationRecommendationLabels = {
  title: string;
  current: string;
  why: string;
  blocking: string;
  nextActions: string;
  transition: string;
  owner: string;
  reassessment: string;
  none: string;
};

type EvaluationRecommendationProps = {
  panel: EvaluationRecommendationPanel;
  language: Language;
  labels: EvaluationRecommendationLabels;
};

export default function EvaluationRecommendationPanelView({
  panel,
  language,
  labels,
}: EvaluationRecommendationProps) {
  return (
    <section className="evaluation-recommendation" aria-label={labels.title}>
      <h3 className="evaluation-recommendation__title">{labels.title}</h3>
      <div className="evaluation-recommendation__current">
        <span className="section-meta">{labels.current}</span>
        <StatusBadge label={panel.recommendation} variant="info" />
      </div>
      <dl className="evaluation-recommendation__dl">
        <div>
          <dt>{labels.why}</dt>
          <dd>{panel.why}</dd>
        </div>
        <div>
          <dt>{labels.blocking}</dt>
          <dd>
            {panel.blockingConditions.length === 0
              ? labels.none
              : panel.blockingConditions.join(" · ")}
          </dd>
        </div>
        <div>
          <dt>{labels.nextActions}</dt>
          <dd>
            <ul>
              {panel.requiredNextActions.map((action) => (
                <li key={action}>{action}</li>
              ))}
            </ul>
          </dd>
        </div>
        <div>
          <dt>{labels.transition}</dt>
          <dd>{panel.eligibleNextTransition}</dd>
        </div>
        <div>
          <dt>{labels.owner}</dt>
          <dd>{panel.reviewOwner}</dd>
        </div>
        <div>
          <dt>{labels.reassessment}</dt>
          <dd>{formatDate(panel.reassessmentAt, language)}</dd>
        </div>
      </dl>
    </section>
  );
}
