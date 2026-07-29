"use client";

import Link from "next/link";
import FindingList from "@/components/features/intelligence-workspace/FindingList";
import LimitationList from "@/components/features/intelligence-workspace/LimitationList";
import {
  ViewEmptyState,
  ViewLocalError,
} from "@/components/features/intelligence-workspace/WorkspaceStates";
import StatusBadge from "@/components/ui/StatusBadge";
import type { Language } from "@/lib/i18n";
import type { IntelligenceUiError } from "@/lib/intelligence/errorMap";
import type {
  ResearchRunDetailDto,
  ResearchSummarySnapshot,
  SnapshotReferenceDto,
} from "@/lib/intelligence/types";
import type { SnapshotContentStatus } from "@/lib/intelligence/useSnapshotContent";
import {
  formatNullableText,
  formatPublishedTimestamp,
  formatRunType,
  formatValidationStatus,
  hasSummaryValidationDiscrepancy,
  mapRunValidationOk,
  workspaceViewHref,
} from "@/lib/intelligence/workspaceDisplay";

export type OverviewViewProps = {
  run: ResearchRunDetailDto;
  language: Language;
  reference: SnapshotReferenceDto | null;
  status: SnapshotContentStatus;
  content: ResearchSummarySnapshot | null;
  error: IntelligenceUiError | null;
  onRetry: () => void;
};

export default function OverviewView({
  run,
  language,
  reference,
  status,
  content,
  error,
  onRetry,
}: OverviewViewProps) {
  const zh = language === "zh";

  if (status === "loading" || status === "idle") {
    return (
      <section
        className="published-workspace__view"
        aria-labelledby="workspace-view-heading"
        data-testid="overview-view"
      >
        <h2 id="workspace-view-heading" tabIndex={-1}>
          {zh ? "概览" : "Overview"}
        </h2>
        <div className="published-workspace__view-loading" aria-hidden="true">
          <div className="research-skeleton research-skeleton--title" />
          <div className="research-skeleton research-skeleton--line" />
          <div className="research-skeleton research-skeleton--block" />
        </div>
        <span className="research-library__sr-only">
          {zh ? "正在加载研究摘要…" : "Loading research summary…"}
        </span>
      </section>
    );
  }

  if (status === "error") {
    return (
      <section
        className="published-workspace__view"
        aria-labelledby="workspace-view-heading"
        data-testid="overview-view"
      >
        <h2 id="workspace-view-heading" tabIndex={-1}>
          {zh ? "概览" : "Overview"}
        </h2>
        <ViewLocalError
          language={language}
          error={
            error ?? {
              category: "invalid_snapshot",
              reason: "snapshot_invalid",
              message: zh
                ? "研究摘要快照内容无效。"
                : "Research summary snapshot content is invalid.",
            }
          }
          onRetry={onRetry}
        />
      </section>
    );
  }

  if (!reference || status === "missing_reference") {
    return (
      <section
        className="published-workspace__view"
        aria-labelledby="workspace-view-heading"
        data-testid="overview-view"
      >
        <h2 id="workspace-view-heading" tabIndex={-1}>
          {zh ? "概览" : "Overview"}
        </h2>
        <ViewEmptyState
          title={
            zh
              ? "此运行未发布研究摘要快照。"
              : "No research summary snapshot was published for this run."
          }
          description={
            zh
              ? "可在证据视图中查看已登记的快照与产物引用。"
              : "Review registered snapshot and artifact references in Evidence."
          }
          action={
            <Link
              href={workspaceViewHref(run.run_id, "evidence")}
              scroll={false}
              className="btn"
              data-testid="overview-open-evidence"
            >
              {zh ? "打开证据" : "Open Evidence"}
            </Link>
          }
        />
      </section>
    );
  }

  if (!content) {
    return (
      <section
        className="published-workspace__view"
        aria-labelledby="workspace-view-heading"
        data-testid="overview-view"
      >
        <h2 id="workspace-view-heading" tabIndex={-1}>
          {zh ? "概览" : "Overview"}
        </h2>
        <ViewLocalError
          language={language}
          error={
            error ?? {
              category: "invalid_snapshot",
              reason: "snapshot_invalid",
              message: zh
                ? "研究摘要快照内容无效。"
                : "Research summary snapshot content is invalid.",
            }
          }
          onRetry={onRetry}
        />
      </section>
    );
  }

  const asOf = formatPublishedTimestamp(content.as_of, language);
  const generated = formatPublishedTimestamp(content.generated_at, language);
  const runConsumerStatus = mapRunValidationOk(run.validation.ok);
  const discrepancy = hasSummaryValidationDiscrepancy(
    run.validation.ok,
    content.validation_status
  );

  return (
    <section
      className="published-workspace__view"
      aria-labelledby="workspace-view-heading"
      data-testid="overview-view"
    >
      <h2 id="workspace-view-heading" tabIndex={-1}>
        {zh ? "概览" : "Overview"}
      </h2>

      <div className="published-workspace__overview-lead">
        <p className="published-workspace__eyebrow">
          {content.run_type
            ? formatRunType(content.run_type, language)
            : formatRunType(run.run_type, language)}
        </p>
        <h3 className="published-workspace__summary-title">
          {formatNullableText(content.research_title)}
        </h3>
        <p className="published-workspace__objective">
          {formatNullableText(content.research_objective)}
        </p>
      </div>

      <dl className="published-workspace__meta-grid" data-testid="overview-meta">
        <div>
          <dt>{zh ? "股票池" : "Universe"}</dt>
          <dd>{formatNullableText(content.universe)}</dd>
        </div>
        <div>
          <dt>{zh ? "分析窗口" : "Analysis window"}</dt>
          <dd>{formatNullableText(content.analysis_window)}</dd>
        </div>
        <div>
          <dt>{zh ? "截至" : "As of"}</dt>
          <dd>
            {asOf.dateTime ? (
              <time dateTime={asOf.dateTime}>{asOf.display}</time>
            ) : (
              asOf.display
            )}
          </dd>
        </div>
        <div>
          <dt>{zh ? "生成时间" : "Generated"}</dt>
          <dd>
            {generated.dateTime ? (
              <time dateTime={generated.dateTime}>{generated.display}</time>
            ) : (
              generated.display
            )}
          </dd>
        </div>
        <div>
          <dt>{zh ? "摘要验证状态" : "Summary validation"}</dt>
          <dd>
            <StatusBadge
              label={formatValidationStatus(content.validation_status, language)}
              variant={
                content.validation_status === "passed"
                  ? "success"
                  : content.validation_status === "failed"
                    ? "danger"
                    : "neutral"
              }
            />
          </dd>
        </div>
      </dl>

      {discrepancy ? (
        <p
          className="published-workspace__discrepancy"
          role="status"
          data-testid="overview-validation-discrepancy"
        >
          {zh
            ? `已发布摘要报告的消费端验证状态与权威运行验证不一致（摘要：${formatValidationStatus(content.validation_status, language)}；运行：${formatValidationStatus(runConsumerStatus, language)}）。验证视图以运行详情为准。`
            : `The published summary reports a different consumer-facing validation status from the canonical run validation (summary: ${formatValidationStatus(content.validation_status, language)}; run: ${formatValidationStatus(runConsumerStatus, language)}). Validation view uses run detail as canonical.`}
        </p>
      ) : null}

      <div className="published-workspace__subsection">
        <h3>{zh ? "关键发现" : "Key findings"}</h3>
        <FindingList findings={content.key_findings} language={language} />
      </div>

      <div className="published-workspace__subsection">
        <h3>{zh ? "限制" : "Limitations"}</h3>
        <LimitationList limitations={content.limitations} language={language} />
      </div>

      <div className="published-workspace__subsection">
        <h3>{zh ? "已发布证据摘要" : "Published evidence summary"}</h3>
        {content.artifact_summary.length === 0 ? (
          <p className="published-workspace__muted" role="status">
            {zh
              ? "此快照未包含产物摘要项。"
              : "No artifact summary items were included in this snapshot."}
          </p>
        ) : (
          <ul
            className="published-workspace__artifact-summary"
            data-testid="artifact-summary"
          >
            {content.artifact_summary.map((item) => (
              <li key={item.artifact_id}>
                <span>{item.name}</span>
                <span className="published-workspace__muted">
                  {item.artifact_type}
                </span>
                <code title={item.artifact_id}>{item.artifact_id}</code>
              </li>
            ))}
          </ul>
        )}
      </div>

      <details className="published-workspace__tech-details">
        <summary>{zh ? "技术出处" : "Technical provenance"}</summary>
        <dl className="published-workspace__meta-grid">
          <div>
            <dt>{zh ? "构建器" : "Builder"}</dt>
            <dd>
              <code>{content.provenance.builder}</code>
            </dd>
          </div>
          <div>
            <dt>{zh ? "来源产物 ID" : "Source artifact IDs"}</dt>
            <dd>
              {content.provenance.source_artifact_ids.length > 0
                ? content.provenance.source_artifact_ids.join(", ")
                : formatNullableText(null)}
            </dd>
          </div>
          {content.provenance.notes ? (
            <div>
              <dt>{zh ? "备注" : "Notes"}</dt>
              <dd>{content.provenance.notes}</dd>
            </div>
          ) : null}
          <div>
            <dt>{zh ? "内容 schema" : "Content schema"}</dt>
            <dd>
              <code>{content.schema_version}</code>
            </dd>
          </div>
          <div>
            <dt>{zh ? "生成时间" : "Generated"}</dt>
            <dd>
              {generated.dateTime ? (
                <time dateTime={generated.dateTime}>{generated.display}</time>
              ) : (
                generated.display
              )}
            </dd>
          </div>
        </dl>
      </details>
    </section>
  );
}
