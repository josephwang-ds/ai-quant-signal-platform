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
        <header className="published-run-card__header">
          <p className="published-run-card__type">{formatRunType(run.run_type, language)}</p>
          <h3 className="published-run-card__title">{label}</h3>
        </header>

        <dl className="published-run-card__meta">
          <div>
            <dt>{zh ? "运行编号" : "Run ID"}</dt>
            <dd>
              <code className="published-run-card__run-id" title={run.run_id}>
                {shortenRunId(run.run_id)}
              </code>
            </dd>
          </div>
          <div>
            <dt>{zh ? "发布时间" : "Published"}</dt>
            <dd>
              {published.dateTime ? (
                <time dateTime={published.dateTime}>{published.display}</time>
              ) : (
                published.display
              )}
            </dd>
          </div>
          <div>
            <dt>{zh ? "股票池" : "Universe"}</dt>
            <dd>{universe}</dd>
          </div>
          <div>
            <dt>{zh ? "产物" : "Artifacts"}</dt>
            <dd>{run.artifact_count}</dd>
          </div>
          <div>
            <dt>{zh ? "快照" : "Snapshots"}</dt>
            <dd>{run.snapshot_count}</dd>
          </div>
          <div>
            <dt>{zh ? "数据集版本" : "Dataset"}</dt>
            <dd>{formatNullableText(run.dataset_version)}</dd>
          </div>
          <div>
            <dt>{zh ? "特征版本" : "Features"}</dt>
            <dd>{formatNullableText(run.feature_version)}</dd>
          </div>
          <div>
            <dt>{zh ? "模型版本" : "Model"}</dt>
            <dd>{formatNullableText(run.model_version)}</dd>
          </div>
          {run.git_commit ? (
            <div>
              <dt>Git</dt>
              <dd>
                <code title={run.git_commit}>
                  {run.git_commit.length > 12
                    ? run.git_commit.slice(0, 12)
                    : run.git_commit}
                </code>
              </dd>
            </div>
          ) : null}
        </dl>
      </Link>
    </article>
  );
}
