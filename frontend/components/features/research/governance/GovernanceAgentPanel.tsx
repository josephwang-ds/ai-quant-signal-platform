"use client";

import { useCallback, useState } from "react";
import Button from "@/components/ui/Button";
import ErrorAlert from "@/components/ui/ErrorAlert";
import LoadingState from "@/components/ui/LoadingState";
import SectionCard from "@/components/ui/SectionCard";
import SectionHeader from "@/components/ui/SectionHeader";
import StatusBadge from "@/components/ui/StatusBadge";
import { getApiUserMessage } from "@/lib/apiRequest";
import {
  cancelAgentRun,
  createAgentRun,
  getAgentRun,
  resumeAgentRun,
} from "@/lib/researchAgentApi";
import { getResearchDecisionRecord } from "@/lib/researchDecisionRecord";
import { buildAgentResearchDefinition } from "@/lib/researchGuidance";
import type { ResearchDetail } from "@/types/research";
import type {
  AgentIntent,
  AgentResumeAction,
  AgentRunDetail,
  AgentStatus,
} from "@/types/researchAgent";

type Props = {
  research: ResearchDetail;
  isFactorTemplate: boolean;
  evidenceSnapshotId: string | null;
  language: "en" | "zh";
};

const INTENTS: { id: AgentIntent; labelEn: string; labelZh: string }[] = [
  {
    id: "review_definition",
    labelEn: "Review Research Definition",
    labelZh: "审查研究定义",
  },
  {
    id: "review_readiness",
    labelEn: "Check Research Readiness",
    labelZh: "检查研究就绪度",
  },
  {
    id: "review_evidence",
    labelEn: "Review Current Evidence",
    labelZh: "审查当前证据",
  },
  {
    id: "prepare_decision",
    labelEn: "Prepare Decision Review",
    labelZh: "准备决策审查",
  },
];

function statusVariant(
  status: AgentStatus
): "success" | "warning" | "danger" | "neutral" {
  if (status === "completed") return "success";
  if (status === "awaiting_approval") return "warning";
  if (status === "failed" || status === "cancelled") return "danger";
  return "neutral";
}

export default function GovernanceAgentPanel({
  research,
  isFactorTemplate,
  evidenceSnapshotId,
  language,
}: Props) {
  const [intent, setIntent] = useState<AgentIntent>("review_definition");
  const [run, setRun] = useState<AgentRunDetail | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [decision, setDecision] = useState("Hold");
  const [rationale, setRationale] = useState("");
  const [overrideRationale, setOverrideRationale] = useState("");

  const zh = language === "zh";

  const refresh = useCallback(async (agentRunId: string) => {
    const detail = await getAgentRun(agentRunId);
    setRun(detail);
    return detail;
  }, []);

  const startRun = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const previous = getResearchDecisionRecord(research.id);
      const definitionPayload = buildAgentResearchDefinition(research);
      const summary = await createAgentRun({
        research_id: research.id,
        intent,
        research_type: isFactorTemplate ? "factor" : "trend_following",
        research_definition: definitionPayload,
        evidence_snapshot_id: evidenceSnapshotId,
        previous_decisions: previous
          ? [
              {
                decision: previous.outcome,
                rationale: previous.rationale,
                recorded_at: previous.decidedAt,
              },
            ]
          : [],
      });
      await refresh(summary.agent_run_id);
    } catch (err) {
      setRun(null);
      setError(
        getApiUserMessage(
          err,
          zh
            ? "治理 Agent 不可用。未伪造任何 Agent 结果。"
            : "Governance Agent is unavailable. No fabricated Agent result was shown."
        )
      );
    } finally {
      setBusy(false);
    }
  }, [
    evidenceSnapshotId,
    intent,
    isFactorTemplate,
    refresh,
    research.id,
    zh,
  ]);

  const onResume = useCallback(
    async (
      action: AgentResumeAction,
      payload: Record<string, unknown> = {}
    ) => {
      if (!run) return;
      setBusy(true);
      setError(null);
      try {
        const detail = await resumeAgentRun(run.agent_run_id, action, payload);
        setRun(detail);
      } catch (err) {
        setError(
          getApiUserMessage(
            err,
            zh ? "无法恢复 Agent 运行。" : "Could not resume the Agent run."
          )
        );
      } finally {
        setBusy(false);
      }
    },
    [run, zh]
  );

  const onCancel = useCallback(async () => {
    if (!run) return;
    setBusy(true);
    try {
      const detail = await cancelAgentRun(run.agent_run_id);
      setRun(detail);
    } catch (err) {
      setError(getApiUserMessage(err, "Cancel failed."));
    } finally {
      setBusy(false);
    }
  }, [run]);

  const pendingType = String(run?.pending_approval?.type || "");
  const decisionReview = run?.decision_review || {};
  const deterministicSuggestion = String(
    decisionReview.deterministic_suggestion || "Hold"
  );

  return (
    <SectionCard>
      <div className="governance-agent">
      <SectionHeader
        title={zh ? "证据治理 Agent" : "Evidence Governance Agent"}
        description={
          zh
            ? "在定义、验证和基准证据准备后，用 DeepSeek 解释缺口并准备人工审查。定量结果仍由确定性后端计算。"
            : "After definition, validation, and benchmark evidence are ready, use DeepSeek to explain gaps and prepare human review. Deterministic services still own every quantitative result."
        }
      />
      <p className="section-meta">
        {zh
          ? "证据优先 · AI 其次 · 人类最终。Agent 支持生命周期，不是新的生命周期阶段。"
          : "Evidence First · AI Second · Human Final. The Agent supports the lifecycle; it is not another lifecycle stage."}
      </p>

      <div className="governance-agent__tasks">
        {INTENTS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={
              intent === item.id
                ? "governance-agent__task is-active"
                : "governance-agent__task"
            }
            onClick={() => setIntent(item.id)}
            disabled={busy}
          >
            {zh ? item.labelZh : item.labelEn}
          </button>
        ))}
      </div>

      <div className="governance-agent__actions">
        <Button primary onClick={() => void startRun()} disabled={busy}>
          {busy
            ? zh
              ? "运行中…"
              : "Running…"
            : zh
              ? "审查当前研究"
              : "Review current research"}
        </Button>
        {run ? (
          <Button onClick={() => void onCancel()} disabled={busy}>
            {zh ? "取消运行" : "Cancel run"}
          </Button>
        ) : null}
      </div>

      {error ? (
        <ErrorAlert title={zh ? "Agent 错误" : "Agent error"} message={error} />
      ) : null}
      {busy && !run ? (
        <LoadingState
          message={zh ? "正在编排工作流…" : "Orchestrating workflow…"}
        />
      ) : null}

      {run ? (
        <div className="governance-agent__run">
          <div className="governance-agent__meta">
            <StatusBadge label={run.status} variant={statusVariant(run.status)} />
            <span>
              {zh ? "当前节点" : "Current node"}: {run.current_node}
            </span>
            <span>
              {run.llm_available
                ? `${run.llm_provider || "llm"} / ${run.llm_model || "model"}`
                : zh
                  ? "AI 不可用（确定性路径仍可用）"
                  : "AI unavailable (deterministic path still works)"}
            </span>
          </div>
          <p className="governance-agent__summary">{run.summary}</p>

          <h4>{zh ? "运行轨迹" : "Run trace"}</h4>
          <ol className="governance-agent__trace">
            {(run.trace || []).map((event) => (
              <li key={`${event.step}-${event.node}-${event.event}`}>
                <strong>{event.node}</strong> — {event.event}
                {event.detail ? `: ${event.detail}` : ""}
              </li>
            ))}
          </ol>

          {(run.knowledge_context || []).length > 0 ? (
            <>
              <h4>
                {zh ? "知识引用（Rulebook）" : "Knowledge citations (Rulebook)"}
              </h4>
              <ul className="governance-agent__knowledge">
                {run.knowledge_context.map((item) => (
                  <li key={String(item.knowledge_id)}>
                    <strong>{String(item.title)}</strong>
                    <span className="section-meta">
                      {" "}
                      {String(item.knowledge_id)} · {String(item.version)}
                    </span>
                    <p>{String(item.excerpt || "").slice(0, 220)}</p>
                  </li>
                ))}
              </ul>
            </>
          ) : null}

          {(run.tool_results || []).length > 0 ? (
            <>
              <h4>{zh ? "工具调用" : "Tool calls"}</h4>
              <ul className="governance-agent__tools">
                {run.tool_results.map((tool) => (
                  <li key={String(tool.tool_call_id || tool.tool_name)}>
                    <strong>{String(tool.tool_name)}</strong> —{" "}
                    {String(tool.status)}
                  </li>
                ))}
              </ul>
            </>
          ) : null}

          {run.ai_interpretation &&
          Object.keys(run.ai_interpretation).length > 0 ? (
            <>
              <h4>
                {zh
                  ? "证据审查（AI 解释）"
                  : "Evidence review (AI interpretation)"}
              </h4>
              <p>{String(run.ai_interpretation.executive_summary || "—")}</p>
              <p className="section-meta">
                {zh ? "假设评估" : "Hypothesis assessment"}:{" "}
                {String(
                  run.ai_interpretation.hypothesis_assessment || "inconclusive"
                )}
              </p>
            </>
          ) : null}

          {run.decision_review && Object.keys(run.decision_review).length > 0 ? (
            <>
              <h4>{zh ? "决策审查" : "Decision review"}</h4>
              <ul className="governance-agent__decision">
                <li>
                  <strong>
                    {zh ? "确定性建议" : "Deterministic suggestion"}
                  </strong>
                  <span>{deterministicSuggestion}</span>
                </li>
                <li>
                  <strong>{zh ? "AI 解释" : "AI interpretation"}</strong>
                  <span>
                    {String(decisionReview.agent_interpretation || "—")}
                  </span>
                </li>
                <li>
                  <strong>{zh ? "人类决策" : "Human decision"}</strong>
                  <span>
                    {run.human_decision?.decision
                      ? String(run.human_decision.decision)
                      : zh
                        ? "尚未记录"
                        : "Not recorded"}
                  </span>
                </li>
              </ul>
            </>
          ) : null}

          {run.status === "awaiting_approval" &&
          pendingType === "tool_approval" ? (
            <div className="governance-agent__approval">
              <h4>{zh ? "待批准的工具" : "Pending tool approval"}</h4>
              <ul>
                {(
                  (run.pending_approval.tools as Array<
                    Record<string, unknown>
                  >) || []
                ).map((tool) => (
                  <li key={String(tool.tool_name)}>
                    <strong>{String(tool.tool_name)}</strong> —{" "}
                    {String(tool.reason)}
                  </li>
                ))}
              </ul>
              <div className="governance-agent__actions">
                <Button
                  primary
                  onClick={() => void onResume("approve")}
                  disabled={busy}
                >
                  {zh ? "批准" : "Approve"}
                </Button>
                <Button onClick={() => void onResume("skip")} disabled={busy}>
                  {zh ? "跳过" : "Skip"}
                </Button>
                <Button onClick={() => void onCancel()} disabled={busy}>
                  {zh ? "取消" : "Cancel"}
                </Button>
              </div>
            </div>
          ) : null}

          {run.status === "awaiting_approval" &&
          pendingType === "human_decision" ? (
            <div className="governance-agent__approval">
              <h4>{zh ? "记录人类决策" : "Record human decision"}</h4>
              <label className="governance-agent__field">
                {zh ? "决策" : "Decision"}
                <select
                  value={decision}
                  onChange={(event) => setDecision(event.target.value)}
                >
                  {["Promote", "Hold", "Reject", "Archive"].map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </label>
              <label className="governance-agent__field">
                {zh ? "理由" : "Rationale"}
                <textarea
                  value={rationale}
                  onChange={(event) => setRationale(event.target.value)}
                  rows={3}
                />
              </label>
              {decision !== deterministicSuggestion ? (
                <label className="governance-agent__field">
                  {zh ? "覆盖理由（必填）" : "Override rationale (required)"}
                  <textarea
                    value={overrideRationale}
                    onChange={(event) =>
                      setOverrideRationale(event.target.value)
                    }
                    rows={2}
                  />
                </label>
              ) : null}
              <div className="governance-agent__actions">
                <Button
                  primary
                  onClick={() =>
                    void onResume("record_decision", {
                      decision,
                      rationale,
                      override_rationale: overrideRationale,
                    })
                  }
                  disabled={
                    busy ||
                    !rationale.trim() ||
                    (decision !== deterministicSuggestion &&
                      !overrideRationale.trim())
                  }
                >
                  {zh ? "记录决策" : "Record decision"}
                </Button>
                <Button
                  onClick={() => void onResume("run_additional_validation")}
                  disabled={busy}
                >
                  {zh ? "追加验证" : "Run additional validation"}
                </Button>
                <Button onClick={() => void onCancel()} disabled={busy}>
                  {zh ? "取消" : "Cancel"}
                </Button>
              </div>
            </div>
          ) : null}

          {(run.errors || []).length > 0 ? (
            <ErrorAlert
              title={zh ? "运行错误" : "Run errors"}
              message={run.errors.join("; ")}
            />
          ) : null}
        </div>
      ) : null}
      </div>
    </SectionCard>
  );
}
