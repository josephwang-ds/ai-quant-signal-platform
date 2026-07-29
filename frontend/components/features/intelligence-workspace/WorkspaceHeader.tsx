"use client";

import Link from "next/link";
import StatusBadge from "@/components/ui/StatusBadge";
import type { Language } from "@/lib/i18n";
import {
  formatNullableText,
  formatPublishedTimestamp,
  formatRunType,
  shortenRunId,
} from "@/lib/intelligence/workspaceDisplay";
import type { ResearchRunDetailDto } from "@/lib/intelligence/types";

export type WorkspaceHeaderProps = {
  run: ResearchRunDetailDto;
  language: Language;
  /** Side effect of Overview summary load only — never replaces run identity. */
  analysisWindow?: string | null;
  /** Summary universe only when run.universe is null. */
  universeOverride?: string | null;
};

export default function WorkspaceHeader({
  run,
  language,
  analysisWindow,
  universeOverride,
}: WorkspaceHeaderProps) {
  const zh = language === "zh";
  const published = formatPublishedTimestamp(run.published_at, language);
  const truncatedId = shortenRunId(run.run_id, 16, 10);
  const universe = universeOverride ?? run.universe;

  return (
    <header className="published-workspace__header" data-testid="published-workspace-header">
      <Link href="/" className="published-workspace__back" data-testid="workspace-back-library">
        {zh ? "← 返回研究资料库" : "← Back to Research Library"}
      </Link>

      <div className="published-workspace__identity">
        <p className="published-workspace__type">{formatRunType(run.run_type, language)}</p>
        <div className="published-workspace__title-row">
          <h1 className="published-workspace__run-id">
            <code title={run.run_id} aria-label={run.run_id}>
              {truncatedId}
            </code>
          </h1>
          <StatusBadge label="PUBLISHED" variant="success" />
        </div>
      </div>

      <dl className="published-workspace__meta">
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
          <dd>{formatNullableText(universe)}</dd>
        </div>
        <div data-testid="header-analysis-window">
          <dt>{zh ? "分析窗口" : "Analysis window"}</dt>
          <dd>{formatNullableText(analysisWindow)}</dd>
        </div>
        <div>
          <dt>{zh ? "数据集" : "Dataset"}</dt>
          <dd>{formatNullableText(run.dataset_version)}</dd>
        </div>
        <div>
          <dt>{zh ? "特征" : "Features"}</dt>
          <dd>{formatNullableText(run.feature_version)}</dd>
        </div>
        <div>
          <dt>{zh ? "模型" : "Model"}</dt>
          <dd>{formatNullableText(run.model_version)}</dd>
        </div>
        <div>
          <dt>{zh ? "Git" : "Git"}</dt>
          <dd>
            {run.git_commit ? (
              <code title={run.git_commit}>{run.git_commit}</code>
            ) : (
              formatNullableText(null)
            )}
          </dd>
        </div>
      </dl>
    </header>
  );
}
