"use client";

import Link from "next/link";
import type { Language } from "@/lib/i18n";
import {
  derivePublishedRunLabel,
  formatNullableText,
  formatPublishedTimestamp,
  formatRunType,
  shortenRunId,
  summarizeUniverse,
} from "@/lib/intelligence/display";
import type { ResearchRunSummaryDto } from "@/lib/intelligence/types";

export type PublishedRunCardProps = {
  run: ResearchRunSummaryDto;
  language: Language;
};

export default function PublishedRunCard({
  run,
  language,
}: PublishedRunCardProps) {
  const label = derivePublishedRunLabel(run, language);
  const href = `/research/${encodeURIComponent(run.run_id)}`;
  const published = formatPublishedTimestamp(run.published_at, language);
  const universe = summarizeUniverse(run.universe) ?? formatNullableText(null);
  const zh = language === "zh";

  return (
    <article
      className="published-run-card"
      data-testid="published-run-card"
      data-run-id={run.run_id}
    >
      <Link
        href={href}
        className="published-run-card__link"
        aria-label={
          zh
            ? `打开已发布研究 ${label}，运行编号 ${run.run_id}`
            : `Open published research ${label}, run ${run.run_id}`
        }
      >
        <div className="published-run-card__row">
          <span className="published-run-card__type">
            {formatRunType(run.run_type, language)}
          </span>
          <h3 className="published-run-card__title">{label}</h3>
        </div>
        <p className="published-run-card__summary">
          {published.dateTime ? (
            <time dateTime={published.dateTime}>{published.display}</time>
          ) : (
            published.display
          )}
          {" · "}
          {universe}
          {" · "}
          <code className="published-run-card__run-id" title={run.run_id}>
            {shortenRunId(run.run_id)}
          </code>
          {run.git_commit ? (
            <>
              {" · "}
              <code title={run.git_commit}>
                {run.git_commit.length > 12
                  ? run.git_commit.slice(0, 12)
                  : run.git_commit}
              </code>
            </>
          ) : null}
        </p>
      </Link>
    </article>
  );
}
