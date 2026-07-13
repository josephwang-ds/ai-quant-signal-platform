import type { Language } from "@/lib/i18n";
import type { EvaluationHistorySnapshot } from "@/types/evaluation";
import StatusBadge from "@/components/ui/StatusBadge";

function formatDate(value: string, language: Language): string {
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

export type EvaluationHistoryLabels = {
  title: string;
  date: string;
  score: string;
  recommendation: string;
  change: string;
  trigger: string;
  superseded: string;
  active: string;
  empty: string;
};

type EvaluationHistoryProps = {
  history: EvaluationHistorySnapshot[];
  language: Language;
  labels: EvaluationHistoryLabels;
};

export default function EvaluationHistory({
  history,
  language,
  labels,
}: EvaluationHistoryProps) {
  return (
    <section className="evaluation-history" aria-label={labels.title}>
      <h3 className="evaluation-history__title">{labels.title}</h3>
      {history.length === 0 ? (
        <p className="section-meta">{labels.empty}</p>
      ) : (
        <ul className="evaluation-history__list">
          {history.map((item) => (
            <li key={item.id} className="evaluation-history__item">
              <div className="evaluation-history__head">
                <span className="font-mono">{formatDate(item.evaluatedAt, language)}</span>
                <StatusBadge
                  label={item.superseded ? labels.superseded : labels.active}
                  variant={item.superseded ? "neutral" : "info"}
                />
              </div>
              <dl className="evaluation-history__dl">
                <div>
                  <dt>{labels.score}</dt>
                  <dd className="font-mono">{item.confidenceScore}</dd>
                </div>
                <div>
                  <dt>{labels.recommendation}</dt>
                  <dd>{item.recommendation}</dd>
                </div>
                <div>
                  <dt>{labels.change}</dt>
                  <dd>{item.mainChange}</dd>
                </div>
                <div>
                  <dt>{labels.trigger}</dt>
                  <dd className="font-mono">{item.trigger}</dd>
                </div>
              </dl>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
