"use client";

import StatusBadge from "@/components/ui/StatusBadge";
import type { Language } from "@/lib/i18n";
import type {
  ResearchRunDetailDto,
  ValidationStatus,
} from "@/lib/intelligence/types";
import {
  formatNullableText,
  formatPublishedTimestamp,
  formatValidationStatus,
  hasSummaryValidationDiscrepancy,
  mapRunValidationOk,
  NULLABLE_PLACEHOLDER,
} from "@/lib/intelligence/workspaceDisplay";

export type ValidationViewProps = {
  run: ResearchRunDetailDto;
  language: Language;
  /** From previously loaded Overview summary only — never triggers a fetch. */
  summaryValidationStatus?: ValidationStatus | null;
};

function recorded(value: string | number | null | undefined): string {
  if (value == null || (typeof value === "string" && value.trim() === "")) {
    return NULLABLE_PLACEHOLDER;
  }
  return String(value);
}

export default function ValidationView({
  run,
  language,
  summaryValidationStatus = null,
}: ValidationViewProps) {
  const zh = language === "zh";
  const consumerStatus = mapRunValidationOk(run.validation.ok);
  const published = formatPublishedTimestamp(run.published_at, language);
  const notes = run.notes?.trim() ? run.notes.trim() : null;
  const discrepancy =
    summaryValidationStatus != null &&
    hasSummaryValidationDiscrepancy(run.validation.ok, summaryValidationStatus);

  return (
    <section
      className="published-workspace__view"
      aria-labelledby="workspace-view-heading"
      data-testid="validation-view"
    >
      <h2 id="workspace-view-heading" tabIndex={-1}>
        {zh ? "验证" : "Validation"}
      </h2>

      <div className="published-workspace__validation-overall" data-testid="validation-overall">
        <h3>{zh ? "发布验证总览" : "Overall publication validation"}</h3>
        <p>
          <StatusBadge
            label={formatValidationStatus(consumerStatus, language)}
            variant={run.validation.ok ? "success" : "danger"}
          />
          <span className="published-workspace__muted">
            {" "}
            {zh
              ? "（以运行详情为权威来源）"
              : "(canonical source: research run detail)"}
          </span>
        </p>
        {discrepancy && summaryValidationStatus ? (
          <p
            className="published-workspace__discrepancy"
            role="status"
            data-testid="validation-discrepancy"
          >
            {zh
              ? `已发布摘要报告了不同的消费端验证状态（摘要：${formatValidationStatus(summaryValidationStatus, language)}）。本页仍以运行详情为准。`
              : `The published summary reports a different consumer-facing validation status from the canonical run validation (summary: ${formatValidationStatus(summaryValidationStatus, language)}). This page remains authoritative from run detail.`}
          </p>
        ) : null}
      </div>

      <div className="published-workspace__subsection" data-testid="validation-checks">
        <h3>{zh ? "验证检查" : "Validation checks"}</h3>
        {run.validation.checks.length === 0 ? (
          <p className="published-workspace__muted" role="status">
            {zh ? "未记录验证检查。" : "No validation checks recorded."}
          </p>
        ) : (
          <ul className="published-workspace__check-list">
            {run.validation.checks.map((check) => (
              <li key={check}>
                <code>{check}</code>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="published-workspace__subsection" data-testid="validation-errors">
        <h3>{zh ? "错误" : "Errors"}</h3>
        {run.errors.length === 0 ? (
          <p className="published-workspace__muted" role="status">
            {zh ? "未记录验证错误。" : "No validation errors recorded."}
          </p>
        ) : (
          <ul className="published-workspace__error-list">
            {run.errors.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        )}
      </div>

      <div className="published-workspace__subsection" data-testid="validation-repro">
        <h3>{zh ? "可复现性" : "Reproducibility"}</h3>
        <dl className="published-workspace__meta-grid">
          <div>
            <dt>{zh ? "数据集" : "Dataset"}</dt>
            <dd>{recorded(run.dataset_version)}</dd>
          </div>
          <div>
            <dt>{zh ? "特征" : "Features"}</dt>
            <dd>{recorded(run.feature_version)}</dd>
          </div>
          <div>
            <dt>{zh ? "模型" : "Model"}</dt>
            <dd>{recorded(run.model_version)}</dd>
          </div>
          <div>
            <dt>{zh ? "Git 提交" : "Git commit"}</dt>
            <dd>
              {run.git_commit ? <code>{run.git_commit}</code> : recorded(null)}
            </dd>
          </div>
          <div>
            <dt>{zh ? "随机种子" : "Seed"}</dt>
            <dd>{recorded(run.random_seed)}</dd>
          </div>
          <div>
            <dt>{zh ? "训练窗口" : "Training window"}</dt>
            <dd>{recorded(run.training_window)}</dd>
          </div>
          <div>
            <dt>{zh ? "预测窗口" : "Prediction window"}</dt>
            <dd>{recorded(run.prediction_window)}</dd>
          </div>
          <div>
            <dt>{zh ? "环境" : "Environment"}</dt>
            <dd>{recorded(run.environment)}</dd>
          </div>
          <div>
            <dt>{zh ? "生成器" : "Generator"}</dt>
            <dd>{recorded(run.generator)}</dd>
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
          {notes ? (
            <div>
              <dt>{zh ? "备注" : "Notes"}</dt>
              <dd>{formatNullableText(notes)}</dd>
            </div>
          ) : null}
        </dl>
      </div>
    </section>
  );
}
