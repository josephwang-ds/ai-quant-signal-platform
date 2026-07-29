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
import type { ResearchRunDetailDto } from "@/lib/intelligence/types";

export type LatestPublishedRunCardProps = {
  run: ResearchRunDetailDto;
  language: Language;
};

export default function LatestPublishedRunCard({
  run,
  language,
}: LatestPublishedRunCardProps) {
  const zh = language === "zh";
  const label = derivePublishedRunLabel(run, language);
  const href = `/research/${encodeURIComponent(run.run_id)}`;
  const published = formatPublishedTimestamp(run.published_at, language);
  const universe = summarizeUniverse(run.universe) ?? formatNullableText(null);

  return (
    <section
      className="research-library__latest"
      aria-labelledby="latest-published-title"
      data-testid="latest-published-section"
    >
      <header className="research-library__section-header">
        <h2 id="latest-published-title">
          {zh ? "最新已发布研究" : "Latest Published Research"}
        </h2>
      </header>

      <article className="published-run-card published-run-card--latest">
        <div className="published-run-card__body">
          <p className="published-run-card__type">
            {formatRunType(run.run_type, language)}
          </p>
          <h3 className="published-run-card__title">{label}</h3>
          <dl className="published-run-card__meta published-run-card__meta--latest">
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
          </dl>
          <div className="published-run-card__actions">
            <Link
              href={href}
              className="btn btn--primary"
              data-testid="open-latest-research"
            >
              {zh ? "打开最新研究" : "Open latest research"}
            </Link>
          </div>
        </div>
      </article>
    </section>
  );
}
