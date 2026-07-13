"use client";

import Link from "next/link";
import Button from "@/components/ui/Button";
import ConfidenceBadge from "@/components/ui/ConfidenceBadge";
import StatusBadge, { researchLifecycleVariant } from "@/components/ui/StatusBadge";
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
  };
  onDuplicate: (id: string) => void;
  onArchive: (id: string) => void;
  onMore: (id: string) => void;
};

/**
 * Research 项目卡片（列表主单元）。
 *
 * TODO(backend): Open Workspace 进入 /research/[id]。
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
        <ConfidenceBadge score={item.confidenceScore} label={labels.confidence} />
      </header>

      <p className="research-card__question">{item.researchQuestion}</p>

      <dl className="research-card__meta">
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

      <ul className="research-card__tags" aria-label="Tags">
        {item.tags.map((tag) => (
          <li key={tag} className="research-card__tag">
            {tag}
          </li>
        ))}
      </ul>

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
        {/* TODO(backend): 替换为 Research Workspace 详情路由 */}
        <Link
          href={`/research-notes?researchId=${encodeURIComponent(item.id)}`}
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
