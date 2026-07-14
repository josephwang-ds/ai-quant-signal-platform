"use client";

import Link from "next/link";
import Button from "@/components/ui/Button";
import EvaluationPendingNotice from "@/components/features/research/EvaluationPendingNotice";
import StatusBadge, { researchLifecycleVariant } from "@/components/ui/StatusBadge";
import TagList from "@/components/ui/TagList";
import type { Language } from "@/lib/i18n";
import type { ResearchListItem } from "@/types/research";

function formatUpdated(value: string, language: Language): string {
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

export type ResearchCardProps = {
  item: ResearchListItem;
  language: Language;
  labels: {
    openWorkspace: string;
    duplicate: string;
    archive: string;
    more: string;
    experiments: string;
    lastValidation: string;
    recommendation: string;
    updated: string;
    owner: string;
    confidence: string;
    symbol: string;
    benchmark: string;
    strategy: string;
    dataStatus: string;
    metricsStatus: string;
    validationStatus: string;
    evaluationStatus: string;
  };
  onDuplicate: (id: string) => void;
  onArchive: (id: string) => void;
  onMore: (id: string) => void;
};

/**
 * Research 项目卡片（列表主单元）。
 * Open Workspace → /research/[researchId]
 */
export default function ResearchCard({
  item,
  language,
  labels,
  onDuplicate,
  onArchive,
  onMore,
}: ResearchCardProps) {
  return (
    <article className="research-card">
      <header className="research-card__header">
        <div className="research-card__title-block">
          <h2 className="research-card__name">{item.name}</h2>
          <StatusBadge
            label={item.status}
            variant={researchLifecycleVariant(item.status)}
          />
        </div>
        <EvaluationPendingNotice
          label={labels.confidence}
          message={item.integrity.evaluationPendingMessage}
        />
      </header>

      <p className="research-card__publicity">{item.integrity.publicityLabel}</p>
      <p className="research-card__question">{item.researchQuestion}</p>

      <dl className="research-card__meta">
        <div className="research-card__meta-item">
          <dt>{labels.symbol}</dt>
          <dd className="font-mono">{item.configuration.symbol}</dd>
        </div>
        <div className="research-card__meta-item">
          <dt>{labels.benchmark}</dt>
          <dd>{item.configuration.benchmark}</dd>
        </div>
        <div className="research-card__meta-item">
          <dt>{labels.strategy}</dt>
          <dd>MA20 / MA60</dd>
        </div>
        <div className="research-card__meta-item">
          <dt>{labels.owner}</dt>
          <dd>{item.owner}</dd>
        </div>
        <div className="research-card__meta-item">
          <dt>{labels.experiments}</dt>
          <dd className="font-mono">{item.experimentCount}</dd>
        </div>
        <div className="research-card__meta-item">
          <dt>{labels.updated}</dt>
          <dd>{formatUpdated(item.updatedAt, language)}</dd>
        </div>
      </dl>

      <dl className="research-card__integrity">
        <div>
          <dt>{labels.dataStatus}</dt>
          <dd>{item.integrity.dataStatus}</dd>
        </div>
        <div>
          <dt>{labels.metricsStatus}</dt>
          <dd>{item.integrity.metricsStatus}</dd>
        </div>
        <div>
          <dt>{labels.validationStatus}</dt>
          <dd>{item.integrity.validationStatus}</dd>
        </div>
        <div>
          <dt>{labels.evaluationStatus}</dt>
          <dd>{item.integrity.evaluationStatus}</dd>
        </div>
      </dl>

      <TagList tags={item.tags} className="research-card__tags" />

      <div className="research-card__insights">
        <p>
          <span className="research-card__insight-label">{labels.lastValidation}</span>
          {item.lastValidation}
        </p>
        <p>
          <span className="research-card__insight-label">{labels.recommendation}</span>
          {item.currentRecommendation}
        </p>
      </div>

      <footer className="research-card__actions">
        <Link
          href={`/research/${encodeURIComponent(item.id)}`}
          className="btn btn--primary"
        >
          {labels.openWorkspace}
        </Link>
        <Button onClick={() => onDuplicate(item.id)}>{labels.duplicate}</Button>
        <Button
          onClick={() => onArchive(item.id)}
          disabled={item.status === "Archived"}
          className="btn--ghost"
        >
          {labels.archive}
        </Button>
        <Button
          onClick={() => onMore(item.id)}
          className="btn--ghost"
          aria-label={labels.more}
        >
          {labels.more}
        </Button>
      </footer>
    </article>
  );
}
