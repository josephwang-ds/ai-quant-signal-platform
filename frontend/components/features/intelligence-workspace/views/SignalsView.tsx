"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  ViewEmptyState,
  ViewLocalError,
} from "@/components/features/intelligence-workspace/WorkspaceStates";
import type { Language } from "@/lib/i18n";
import type { IntelligenceUiError } from "@/lib/intelligence/errorMap";
import type {
  SignalDirection,
  SignalSnapshot,
  SnapshotReferenceDto,
} from "@/lib/intelligence/types";
import { SIGNAL_DIRECTIONS } from "@/lib/intelligence/types";
import type { SnapshotContentStatus } from "@/lib/intelligence/useSnapshotContent";
import {
  countSignalsByDirection,
  formatNullableNumber,
  formatNullableText,
  formatPublishedTimestamp,
  formatSignalDirection,
  sortSignalRecords,
  workspaceViewHref,
} from "@/lib/intelligence/workspaceDisplay";

export type SignalsViewProps = {
  runId: string;
  language: Language;
  reference: SnapshotReferenceDto | null;
  status: SnapshotContentStatus;
  content: SignalSnapshot | null;
  error: IntelligenceUiError | null;
  onRetry: () => void;
};

export default function SignalsView({
  runId,
  language,
  reference,
  status,
  content,
  error,
  onRetry,
}: SignalsViewProps) {
  const zh = language === "zh";
  const [directionFilter, setDirectionFilter] = useState<SignalDirection | "all">(
    "all"
  );

  const sorted = useMemo(
    () => (content ? sortSignalRecords(content.signals) : []),
    [content]
  );

  const counts = useMemo(
    () => countSignalsByDirection(content?.signals ?? []),
    [content]
  );

  const presentDirections = useMemo(
    () => SIGNAL_DIRECTIONS.filter((direction) => counts[direction] > 0),
    [counts]
  );

  const filtered = useMemo(() => {
    if (directionFilter === "all") return sorted;
    return sorted.filter((signal) => signal.direction === directionFilter);
  }, [directionFilter, sorted]);

  if (status === "loading" || status === "idle") {
    return (
      <section
        className="published-workspace__view"
        aria-labelledby="workspace-view-heading"
        data-testid="signals-view"
      >
        <h2 id="workspace-view-heading" tabIndex={-1}>
          {zh ? "信号" : "Signals"}
        </h2>
        <div className="published-workspace__view-loading" aria-hidden="true">
          <div className="research-skeleton research-skeleton--line" />
          <div className="research-skeleton research-skeleton--block" />
        </div>
        <span className="research-library__sr-only">
          {zh ? "正在加载信号快照…" : "Loading signal snapshot…"}
        </span>
      </section>
    );
  }

  if (status === "error") {
    return (
      <section
        className="published-workspace__view"
        aria-labelledby="workspace-view-heading"
        data-testid="signals-view"
      >
        <h2 id="workspace-view-heading" tabIndex={-1}>
          {zh ? "信号" : "Signals"}
        </h2>
        <ViewLocalError
          language={language}
          error={
            error ?? {
              category: "invalid_snapshot",
              reason: "snapshot_invalid",
              message: zh
                ? "信号快照内容无效。"
                : "Signal snapshot content is invalid.",
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
        data-testid="signals-view"
      >
        <h2 id="workspace-view-heading" tabIndex={-1}>
          {zh ? "信号" : "Signals"}
        </h2>
        <ViewEmptyState
          title={
            zh
              ? "此运行未发布信号快照。"
              : "No signal snapshot was published for this run."
          }
          description={
            zh
              ? "可在证据视图中查看已登记的快照与产物引用。"
              : "Review registered snapshot and artifact references in Evidence."
          }
          action={
            <Link
              href={workspaceViewHref(runId, "evidence")}
              scroll={false}
              className="btn"
              data-testid="signals-open-evidence"
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
        data-testid="signals-view"
      >
        <h2 id="workspace-view-heading" tabIndex={-1}>
          {zh ? "信号" : "Signals"}
        </h2>
        <ViewLocalError
          language={language}
          error={
            error ?? {
              category: "invalid_snapshot",
              reason: "snapshot_invalid",
              message: zh
                ? "信号快照内容无效。"
                : "Signal snapshot content is invalid.",
            }
          }
          onRetry={onRetry}
        />
      </section>
    );
  }

  const asOf = formatPublishedTimestamp(content.as_of, language);
  const generated = formatPublishedTimestamp(content.generated_at, language);
  const totalCount = content.signals.length;

  return (
    <section
      className="published-workspace__view"
      aria-labelledby="workspace-view-heading"
      data-testid="signals-view"
    >
      <h2 id="workspace-view-heading" tabIndex={-1}>
        {zh ? "信号" : "Signals"}
      </h2>

      <div className="published-workspace__signal-toolbar">
        <p className="published-workspace__muted" data-testid="signal-page-summary">
          {zh ? "股票池" : "Universe"}: {formatNullableText(content.universe)}
          {" · "}
          {zh ? "截至" : "As of"}:{" "}
          {asOf.dateTime ? (
            <time dateTime={asOf.dateTime}>{asOf.display}</time>
          ) : (
            asOf.display
          )}
          {" · "}
          {zh ? "生成" : "Generated"}:{" "}
          {generated.dateTime ? (
            <time dateTime={generated.dateTime}>{generated.display}</time>
          ) : (
            generated.display
          )}
          {" · "}
          {zh ? "记录数" : "Records"}: {totalCount}
        </p>
        {totalCount > 0 ? (
          <div className="published-workspace__filter">
            <label htmlFor="signal-direction-filter">
              {zh ? "方向" : "Direction"}
            </label>
            <select
              id="signal-direction-filter"
              value={directionFilter}
              onChange={(event) =>
                setDirectionFilter(event.target.value as SignalDirection | "all")
              }
              data-testid="signal-direction-filter"
            >
              <option value="all">{zh ? "全部" : "All"}</option>
              {presentDirections.map((direction) => (
                <option key={direction} value={direction}>
                  {formatSignalDirection(direction, language)}
                </option>
              ))}
            </select>
          </div>
        ) : null}
      </div>

      <div
        className="published-workspace__signal-strip"
        data-testid="signal-direction-strip"
        aria-label={zh ? "按方向统计（全部记录）" : "Direction counts (all records)"}
      >
        {SIGNAL_DIRECTIONS.map((direction) => (
          <div key={direction} className="published-workspace__signal-count">
            <span>{formatSignalDirection(direction, language)}</span>
            <strong>{counts[direction]}</strong>
          </div>
        ))}
      </div>

      {totalCount === 0 ? (
        <ViewEmptyState
          title={
            zh
              ? "此信号快照不包含信号记录。"
              : "This signal snapshot contains no signal records."
          }
        />
      ) : filtered.length === 0 ? (
        <p className="published-workspace__muted" role="status">
          {zh
            ? "当前方向筛选下没有信号。"
            : "No signals match this direction filter."}
        </p>
      ) : (
        <>
          <div className="published-workspace__table-wrap">
            <table className="published-workspace__table published-workspace__table--signals">
              <caption className="research-library__sr-only">
                {zh ? "已发布信号记录" : "Published signal records"}
              </caption>
              <thead>
                <tr>
                  <th scope="col">{zh ? "标的" : "Symbol"}</th>
                  <th scope="col">{zh ? "信号" : "Signal"}</th>
                  <th scope="col">{zh ? "方向" : "Direction"}</th>
                  <th scope="col">{zh ? "分数" : "Score"}</th>
                  <th scope="col">{zh ? "置信度" : "Confidence"}</th>
                  <th scope="col">{zh ? "期限" : "Horizon"}</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((signal) => (
                  <tr key={`${signal.symbol}-${signal.signal_name}`}>
                    <td>
                      <code>{signal.symbol}</code>
                    </td>
                    <td>{signal.signal_name}</td>
                    <td>{formatSignalDirection(signal.direction, language)}</td>
                    <td>{formatNullableNumber(signal.score)}</td>
                    <td>{formatNullableNumber(signal.confidence)}</td>
                    <td>{formatNullableText(signal.horizon)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <ul className="published-workspace__signal-cards" data-testid="signal-cards">
            {filtered.map((signal) => (
              <li
                key={`card-${signal.symbol}-${signal.signal_name}`}
                className="published-workspace__signal-card"
              >
                <p className="published-workspace__signal-card-title">
                  <code>{signal.symbol}</code> · {signal.signal_name}
                </p>
                <dl>
                  <div>
                    <dt>{zh ? "方向" : "Direction"}</dt>
                    <dd>{formatSignalDirection(signal.direction, language)}</dd>
                  </div>
                  <div>
                    <dt>{zh ? "分数" : "Score"}</dt>
                    <dd>{formatNullableNumber(signal.score)}</dd>
                  </div>
                  <div>
                    <dt>{zh ? "置信度" : "Confidence"}</dt>
                    <dd>{formatNullableNumber(signal.confidence)}</dd>
                  </div>
                  <div>
                    <dt>{zh ? "期限" : "Horizon"}</dt>
                    <dd>{formatNullableText(signal.horizon)}</dd>
                  </div>
                </dl>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
