"use client";

import Link from "next/link";
import Button from "@/components/ui/Button";
import StatusBadge, { researchLifecycleVariant } from "@/components/ui/StatusBadge";
import type { Language } from "@/lib/i18n";
import {
  researchNameLabel,
  researchQuestionLabel,
  researchStatusLabel,
} from "@/lib/researchDisplay";
import type { ResearchListItem } from "@/types/research";

function formatRelativeUpdated(value: string, language: Language): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  const now = Date.now();
  const diffMs = now - date.getTime();
  const minute = 60_000;
  const hour = 60 * minute;
  const day = 24 * hour;
  const zh = language === "zh";

  if (diffMs < minute) {
    return zh ? "刚刚更新" : "Updated just now";
  }
  if (diffMs < hour) {
    const minutes = Math.max(1, Math.floor(diffMs / minute));
    return zh ? `${minutes} 分钟前更新` : `Updated ${minutes}m ago`;
  }
  if (diffMs < day) {
    const hours = Math.max(1, Math.floor(diffMs / hour));
    return zh ? `${hours} 小时前更新` : `Updated ${hours}h ago`;
  }
  if (diffMs < 2 * day) {
    return zh ? "1 天前更新" : "Updated 1 day ago";
  }
  if (diffMs < 30 * day) {
    const days = Math.floor(diffMs / day);
    return zh ? `${days} 天前更新` : `Updated ${days} days ago`;
  }

  return date.toLocaleDateString(zh ? "zh-CN" : "en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export type ResearchCardProps = {
  item: ResearchListItem;
  language: Language;
  labels: {
    question: string;
    experiments: string;
    latestEvidence: string;
    archive: string;
    more: string;
  };
  onArchive: (id: string) => void;
};

/**
 * Research Hub card — question-led identity + lifecycle signals only.
 * Whole card opens the workspace; no primary CTA button.
 */
export default function ResearchCard({
  item,
  language,
  labels,
  onArchive,
}: ResearchCardProps) {
  const href = `/research/${encodeURIComponent(item.id)}`;

  return (
    <article className="research-card research-card--project">
      <Link href={href} className="research-card__link">
        <header className="research-card__header">
          <div className="research-card__title-block">
            <h2 className="research-card__name">
              {researchNameLabel(item.id, item.name, language)}
            </h2>
            <StatusBadge
              label={researchStatusLabel(item.status, language)}
              variant={researchLifecycleVariant(item.status)}
            />
          </div>
        </header>

        <div className="research-card__question-block">
          <p className="research-card__field-label">{labels.question}</p>
          <p className="research-card__question">
            {researchQuestionLabel(item.id, item.researchQuestion, language)}
          </p>
        </div>

        <p className="research-card__experiments">
          <span className="font-mono">{item.experimentCount}</span> {labels.experiments}
        </p>

        <div className="research-card__evidence">
          <p className="research-card__field-label">{labels.latestEvidence}</p>
          <p className="research-card__evidence-text">{item.evidenceSummary}</p>
        </div>

        <p className="research-card__updated">
          {formatRelativeUpdated(item.updatedAt, language)}
        </p>
      </Link>

      <div className="research-card__overflow-wrap">
        <details className="research-card__overflow">
          <summary aria-label={labels.more} title={labels.more}>
            •••
          </summary>
          <div className="research-card__overflow-menu">
            <Button
              onClick={(event) => {
                event.preventDefault();
                event.stopPropagation();
                onArchive(item.id);
              }}
              disabled={item.status === "Archived"}
              className="btn--ghost"
            >
              {labels.archive}
            </Button>
          </div>
        </details>
      </div>
    </article>
  );
}
