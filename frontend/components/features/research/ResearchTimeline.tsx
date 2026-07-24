import type { ResearchTimelineEvent } from "@/types/notebook";
import type { Language } from "@/lib/i18n";
import {
  timelineEventKindLabel,
  timelineEventSummaryLabel,
  timelineEventTitleLabel,
} from "@/lib/researchDisplay";

function formatDateTime(value: string, language: Language): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString(language === "zh" ? "zh-CN" : "en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export type ResearchTimelineLabels = {
  title: string;
  description: string;
  sessionNote: string;
  empty: string;
};

type ResearchTimelineProps = {
  events: ResearchTimelineEvent[];
  language: Language;
  labels: ResearchTimelineLabels;
};

/**
 * 轻量本地时间线（mock + session 事件）。
 * TODO(api): 订阅 Research 领域事件流。
 */
export default function ResearchTimeline({
  events,
  language,
  labels,
}: ResearchTimelineProps) {
  return (
    <section className="research-timeline" aria-label={labels.title}>
      <header className="research-timeline__header">
        <h2 className="research-timeline__title">{labels.title}</h2>
        <p className="research-timeline__description">{labels.description}</p>
        <p className="section-meta">{labels.sessionNote}</p>
      </header>

      {events.length === 0 ? (
        <p className="section-meta">{labels.empty}</p>
      ) : (
        <ol className="research-timeline__list">
          {events.map((event) => (
            <li key={event.id} className="research-timeline__item">
              <time className="research-timeline__time font-mono">
                {formatDateTime(event.occurredAt, language)}
              </time>
              <div className="research-timeline__content">
                <p className="research-timeline__event-title">
                  {timelineEventTitleLabel(event.title, language)}
                </p>
                <p className="research-timeline__summary">
                  {timelineEventSummaryLabel(event.summary, language)}
                </p>
                <span className="research-timeline__kind">
                  {timelineEventKindLabel(event.kind, language)}
                </span>
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
