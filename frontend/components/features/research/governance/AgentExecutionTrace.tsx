"use client";

import type { AgentTraceAuthority, AgentTraceEvent, AgentTraceStatus } from "@/types/researchAgent";

type Props = {
  events: AgentTraceEvent[];
  language: "en" | "zh";
  defaultOpen?: boolean;
};

function authorityLabel(authority: AgentTraceAuthority | undefined, zh: boolean): string {
  switch (authority) {
    case "deterministic":
      return zh ? "确定性" : "Deterministic";
    case "llm":
      return zh ? "LLM" : "LLM";
    case "human":
      return zh ? "人工" : "Human";
    default:
      return zh ? "系统" : "System";
  }
}

function statusLabel(status: AgentTraceStatus | undefined, zh: boolean): string {
  switch (status) {
    case "blocked":
      return zh ? "待批准" : "Blocked";
    case "unavailable":
      return zh ? "不可用" : "Unavailable";
    case "failed":
      return zh ? "失败" : "Failed";
    case "running":
      return zh ? "运行中" : "Running";
    case "pending":
      return zh ? "待处理" : "Pending";
    default:
      return zh ? "完成" : "Completed";
  }
}

function sortedEvents(events: AgentTraceEvent[]): AgentTraceEvent[] {
  return [...events].sort((a, b) => {
    const left = a.sequence ?? a.step ?? 0;
    const right = b.sequence ?? b.step ?? 0;
    return left - right;
  });
}

export default function AgentExecutionTrace({
  events,
  language,
  defaultOpen = false,
}: Props) {
  const zh = language === "zh";
  const ordered = sortedEvents(events);

  if (ordered.length === 0) {
    return null;
  }

  return (
    <details className="agent-execution-trace" open={defaultOpen || undefined}>
      <summary className="agent-execution-trace__summary">
        {zh ? "执行记录" : "Execution trace"}
        <span className="section-meta">
          {zh ? `${ordered.length} 步 · 默认折叠` : `${ordered.length} steps · collapsed by default`}
        </span>
      </summary>
      <ol className="agent-execution-trace__list">
        {ordered.map((event) => {
          const authority = event.authority || "system";
          const status = event.status || "completed";
          const key = `${event.sequence ?? event.step}-${event.node}-${event.event}`;
          return (
            <li
              key={key}
              className={`agent-execution-trace__item is-authority-${authority} is-status-${status}`}
              data-authority={authority}
              data-status={status}
            >
              <div className="agent-execution-trace__item-head">
                <strong>{event.label || `${event.node}: ${event.event}`}</strong>
                <span className="agent-execution-trace__badges">
                  <span className={`agent-execution-trace__badge is-${authority}`}>
                    {authorityLabel(authority, zh)}
                  </span>
                  <span className={`agent-execution-trace__badge is-status-${status}`}>
                    {statusLabel(status, zh)}
                  </span>
                </span>
              </div>
              <p className="agent-execution-trace__item-summary">
                {event.summary || event.detail || "—"}
              </p>
              {(event.evidence_ids && event.evidence_ids.length > 0) ||
              (event.methodology_citations && event.methodology_citations.length > 0) ? (
                <p className="section-meta">
                  {event.evidence_ids && event.evidence_ids.length > 0
                    ? `${zh ? "证据" : "Evidence"}: ${event.evidence_ids.join(", ")}`
                    : null}
                  {event.methodology_citations && event.methodology_citations.length > 0
                    ? ` · ${zh ? "方法" : "Methodology"}: ${event.methodology_citations.join(", ")}`
                    : null}
                </p>
              ) : null}
              {event.timestamp || event.at ? (
                <p className="section-meta">{event.timestamp || event.at}</p>
              ) : null}
            </li>
          );
        })}
      </ol>
    </details>
  );
}
