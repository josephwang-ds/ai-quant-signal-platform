"use client";

import { useEffect, useState } from "react";
import type { Language } from "@/lib/i18n";
import {
  buildResearchGuidanceTemplate,
  loadResearchGuidance,
  saveResearchGuidance,
  type ResearchGuidanceDefinition,
  type ResearchSuccessCriterion,
} from "@/lib/researchGuidance";
import {
  isFactorRunConfiguration,
  researchTemplateId,
  type ResearchDetail,
} from "@/types/research";
import {
  draftResearchDefinition,
  identifyMissingResearchSteps,
  reviewResearchHypothesis,
} from "@/lib/researchReviewerApi";
import type {
  CompletionReviewResult,
  DraftResearchDefinitionResult,
  HypothesisReviewResult,
  ResearchReviewerResponse,
} from "@/types/researchReviewer";

type Props = {
  research: ResearchDetail;
  language: Language;
};

type GuidanceReview =
  | {
      kind: "draft" | "criteria";
      response: ResearchReviewerResponse<DraftResearchDefinitionResult>;
    }
  | {
      kind: "hypothesis";
      response: ResearchReviewerResponse<HypothesisReviewResult>;
    }
  | {
      kind: "missing";
      response: ResearchReviewerResponse<CompletionReviewResult>;
    };

function lines(value: string): string[] {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

export default function ResearchGuidancePanel({ research, language }: Props) {
  const zh = language === "zh";
  const [definition, setDefinition] = useState<ResearchGuidanceDefinition>(() =>
    buildResearchGuidanceTemplate(research)
  );
  const [saved, setSaved] = useState(false);
  const [assistantStatus, setAssistantStatus] = useState<
    "idle" | "loading" | "ready" | "error"
  >("idle");
  const [assistantMessage, setAssistantMessage] = useState("");
  const [review, setReview] = useState<GuidanceReview | null>(null);

  useEffect(() => {
    setDefinition(loadResearchGuidance(research));
    setSaved(false);
    setAssistantStatus("idle");
    setAssistantMessage("");
    setReview(null);
  }, [research]);

  const runConfiguration = research.runConfiguration;
  const factor = isFactorRunConfiguration(runConfiguration);
  const reviewerContext = {
    research_type: researchTemplateId(research),
    symbol_or_universe: factor
      ? runConfiguration.universeId
      : research.configuration.symbol || "SPY",
    parameters: runConfiguration ?? {},
    date_range: {
      start: runConfiguration?.startDate ?? "2018-01-01",
      end: runConfiguration?.endDate ?? null,
    },
    benchmark: {
      type: factor
        ? "equal_weight_universe"
        : "same_asset_buy_and_hold",
      name: definition.primaryBenchmark,
    },
    transaction_cost: runConfiguration?.transactionCost ?? 0.001,
    available_validation_methods: definition.requiredValidation,
    known_system_limitations: definition.knownLimitations,
  };

  async function runReviewer(
    kind: GuidanceReview["kind"]
  ) {
    setAssistantStatus("loading");
    setAssistantMessage("");
    try {
      if (kind === "draft" || kind === "criteria") {
        const response = await draftResearchDefinition(reviewerContext);
        setReview({ kind, response });
      } else if (kind === "hypothesis") {
        const response = await reviewResearchHypothesis({
          research_type: researchTemplateId(research),
          research_question: definition.researchQuestion,
          hypothesis: definition.hypothesis,
          null_hypothesis: definition.nullHypothesis,
          benchmark: definition.primaryBenchmark,
          success_criteria: definition.successCriteria.filter(
            (item) => item.active
          ),
          available_validation_methods: definition.requiredValidation,
        });
        setReview({ kind, response });
      } else {
        const response = await identifyMissingResearchSteps({
          definition_completeness: {
            research_question: Boolean(definition.researchQuestion.trim()),
            hypothesis: Boolean(definition.hypothesis.trim()),
            null_hypothesis: Boolean(definition.nullHypothesis.trim()),
            benchmark: Boolean(definition.primaryBenchmark.trim()),
            active_success_criteria: definition.successCriteria.filter(
              (item) => item.active
            ).length,
          },
          experiment_status: "workspace_state_not_supplied",
          validation_status: "workspace_state_not_supplied",
          robustness_status: "workspace_state_not_supplied",
          benchmark_status: "workspace_state_not_supplied",
          decision_status: "workspace_state_not_supplied",
          limitations_acknowledged: definition.knownLimitations.length > 0,
          missing_evidence: definition.requiredValidation,
        });
        setReview({ kind, response });
      }
      setAssistantStatus("ready");
      setAssistantMessage(
        zh
          ? "DeepSeek 结果已生成，但尚未应用或保存。"
          : "The DeepSeek result is ready, but has not been applied or saved."
      );
    } catch (error) {
      setAssistantStatus("error");
      setAssistantMessage(
        error instanceof Error
          ? error.message
          : zh
            ? "LLM 引导当前不可用，确定性模板仍可正常使用。"
            : "LLM guidance is unavailable; the deterministic template still works."
      );
    }
  }

  function aiCriteria(
    result: DraftResearchDefinitionResult
  ): ResearchSuccessCriterion[] {
    return result.proposed_success_criteria.map((item) => ({
      criterionId: item.criterion_id,
      metric: item.metric,
      operator: item.operator,
      threshold: null,
      severity: item.severity,
      description: `${item.description} ${item.threshold_guidance}`.trim(),
      source: "ai_proposed",
      active: false,
    }));
  }

  function applyReview(edit = false) {
    if (!review) return;
    if (review.kind === "draft") {
      const result = review.response.result;
      setDefinition({
        researchQuestion: result.research_question,
        hypothesis: result.hypothesis,
        nullHypothesis: result.null_hypothesis,
        mechanism: result.mechanism,
        primaryBenchmark: result.primary_benchmark.name,
        successCriteria: aiCriteria(result),
        failureCriteria: result.failure_criteria.map(
          (item) => `${item.condition} — ${item.reason}`
        ),
        requiredValidation: result.required_validation,
        knownLimitations: result.known_limitations,
      });
    } else if (review.kind === "criteria") {
      setDefinition((current) => ({
        ...current,
        successCriteria: [
          ...current.successCriteria,
          ...aiCriteria(review.response.result),
        ],
      }));
    } else if (review.kind === "hypothesis") {
      const revision = review.response.result.suggested_revision;
      setDefinition((current) => ({
        ...current,
        researchQuestion: revision.research_question,
        hypothesis: revision.hypothesis,
        nullHypothesis: revision.null_hypothesis,
      }));
    } else if (review.kind === "missing") {
      setDefinition((current) => ({
        ...current,
        requiredValidation: Array.from(
          new Set([
            ...current.requiredValidation,
            ...review.response.result.recommended_next_steps,
          ])
        ),
      }));
    }
    setSaved(false);
    if (!edit) setReview(null);
  }

  function update(
    key: keyof ResearchGuidanceDefinition,
    value: string | string[] | ResearchSuccessCriterion[]
  ) {
    setDefinition((current) => ({ ...current, [key]: value }));
    setSaved(false);
  }

  const listFields: Array<{
    key:
      | "failureCriteria"
      | "requiredValidation"
      | "knownLimitations";
    label: string;
  }> = [
    { key: "failureCriteria", label: zh ? "失败标准" : "Failure criteria" },
    {
      key: "requiredValidation",
      label: zh ? "必须完成的验证" : "Required validation",
    },
    {
      key: "knownLimitations",
      label: zh ? "已知局限" : "Known limitations",
    },
  ];

  return (
    <section className="research-guidance" aria-labelledby="research-guidance-title">
      <header className="research-guidance__header">
        <div>
          <p className="section-eyebrow">
            {zh ? "第 2 层 · 研究引导" : "Layer 2 · Research guidance"}
          </p>
          <h3 id="research-guidance-title">
            {zh ? "可证伪的研究定义" : "Falsifiable research definition"}
          </h3>
          <p className="section-meta">
            {zh
              ? "模板只帮助定义问题，不计算指标、不改写证据，也不会自动做研究决策。每项内容都可编辑并保存在当前浏览器。"
              : "Templates frame the study; they do not calculate metrics, alter evidence, or make the final decision. Every field is editable and saved in this browser."}
          </p>
        </div>
        <span className="research-guidance__mode">
          {zh ? "无 LLM 也可用" : "Works without an LLM"}
        </span>
      </header>

      <div className="research-guidance__grid">
        {[
          {
            key: "researchQuestion" as const,
            label: zh ? "研究问题" : "Research question",
          },
          {
            key: "hypothesis" as const,
            label: zh ? "假设" : "Hypothesis",
          },
          {
            key: "nullHypothesis" as const,
            label: zh ? "零假设" : "Null hypothesis",
          },
          {
            key: "mechanism" as const,
            label: zh ? "机制 / 理由" : "Mechanism / rationale",
          },
          {
            key: "primaryBenchmark" as const,
            label: zh ? "主要基准" : "Primary benchmark",
          },
        ].map((field) => (
          <label key={field.key}>
            <span>{field.label}</span>
            <textarea
              rows={field.key === "primaryBenchmark" ? 2 : 4}
              value={definition[field.key]}
              onChange={(event) => update(field.key, event.target.value)}
            />
          </label>
        ))}
        <div className="research-guidance__criteria-editor">
          <div className="research-guidance__criteria-heading">
            <span>{zh ? "结构化成功标准" : "Structured success criteria"}</span>
            <small>
              {zh
                ? "AI 建议默认不启用；阈值必须由研究者审核。"
                : "AI proposals stay inactive until reviewed; thresholds remain researcher-owned."}
            </small>
          </div>
          {definition.successCriteria.map((criterion, index) => (
            <article key={criterion.criterionId}>
              <div className="research-guidance__criterion-meta">
                <strong>{criterion.metric}</strong>
                <span>{criterion.source}</span>
                <span>{criterion.severity}</span>
              </div>
              <p>{criterion.description}</p>
              <div className="research-guidance__criterion-controls">
                <label>
                  <span>{zh ? "运算符" : "Operator"}</span>
                  <select
                    value={criterion.operator}
                    onChange={(event) => {
                      const next = [...definition.successCriteria];
                      next[index] = {
                        ...criterion,
                        operator: event.target
                          .value as ResearchSuccessCriterion["operator"],
                        source:
                          criterion.source === "template"
                            ? "user"
                            : criterion.source,
                      };
                      update("successCriteria", next);
                    }}
                  >
                    {["gte", "lte", "gt", "lt", "positive", "non_negative"].map(
                      (operator) => (
                        <option key={operator} value={operator}>
                          {operator}
                        </option>
                      )
                    )}
                  </select>
                </label>
                <label>
                  <span>{zh ? "阈值" : "Threshold"}</span>
                  <input
                    type="number"
                    step="any"
                    value={criterion.threshold ?? ""}
                    placeholder={zh ? "需要人工设置" : "Researcher sets"}
                    onChange={(event) => {
                      const next = [...definition.successCriteria];
                      next[index] = {
                        ...criterion,
                        threshold:
                          event.target.value === ""
                            ? null
                            : Number(event.target.value),
                        source:
                          criterion.source === "template"
                            ? "user"
                            : criterion.source,
                      };
                      update("successCriteria", next);
                    }}
                  />
                </label>
                <label className="research-guidance__criterion-active">
                  <input
                    type="checkbox"
                    checked={criterion.active}
                    onChange={(event) => {
                      const next = [...definition.successCriteria];
                      next[index] = {
                        ...criterion,
                        active: event.target.checked,
                      };
                      update("successCriteria", next);
                    }}
                  />
                  <span>{zh ? "启用" : "Active"}</span>
                </label>
              </div>
            </article>
          ))}
        </div>
        {listFields.map((field) => (
          <label key={field.key}>
            <span>{field.label}</span>
            <textarea
              rows={6}
              value={definition[field.key].join("\n")}
              onChange={(event) => update(field.key, lines(event.target.value))}
            />
            <small>{zh ? "每行一项" : "One item per line"}</small>
          </label>
        ))}
      </div>

      <div className="research-guidance__actions">
        <button
          type="button"
          className="btn"
          disabled={assistantStatus === "loading"}
          onClick={() => void runReviewer("draft")}
        >
          {assistantStatus === "loading"
            ? zh
              ? "DeepSeek 审阅中…"
              : "DeepSeek reviewing…"
            : zh
              ? "AI 起草研究定义"
              : "Draft Research Definition"}
        </button>
        <button
          type="button"
          className="btn"
          disabled={assistantStatus === "loading"}
          onClick={() => void runReviewer("hypothesis")}
        >
          {zh ? "审阅假设" : "Review Hypothesis"}
        </button>
        <button
          type="button"
          className="btn"
          disabled={assistantStatus === "loading"}
          onClick={() => void runReviewer("criteria")}
        >
          {zh ? "建议成功标准" : "Suggest Success Criteria"}
        </button>
        <button
          type="button"
          className="btn"
          disabled={assistantStatus === "loading"}
          onClick={() => void runReviewer("missing")}
        >
          {zh ? "识别缺失步骤" : "Identify Missing Steps"}
        </button>
        <button
          type="button"
          className="btn"
          onClick={() => {
            setDefinition(buildResearchGuidanceTemplate(research));
            setSaved(false);
          }}
        >
          {zh ? "恢复确定性模板" : "Restore deterministic template"}
        </button>
        <button
          type="button"
          className="btn btn--primary"
          onClick={() => {
            saveResearchGuidance(research.id, definition);
            setSaved(true);
          }}
        >
          {saved ? (zh ? "已保存" : "Saved") : zh ? "保存定义" : "Save definition"}
        </button>
      </div>
      {assistantMessage ? (
        <p
          className={`research-guidance__assistant-message research-guidance__assistant-message--${assistantStatus}`}
          role="status"
        >
          {assistantMessage}
        </p>
      ) : null}
      {review ? (
        <article className="research-reviewer-card">
          <header>
            <div>
              <p className="section-eyebrow">
                {zh ? "AI 辅助解释 · 尚未应用" : "AI-assisted interpretation · not applied"}
              </p>
              <h4>{review.kind.replaceAll("_", " ")}</h4>
            </div>
            <span>
              {review.response.provider} · {review.response.model} ·{" "}
              {new Date(review.response.generated_at).toLocaleString()}
            </span>
          </header>
          {review.kind === "draft" || review.kind === "criteria" ? (
            <div className="research-reviewer-card__body">
              {review.kind === "draft" ? (
                <>
                  <p>{review.response.result.research_question}</p>
                  <p>{review.response.result.hypothesis}</p>
                </>
              ) : null}
              <strong>
                {zh ? "AI 建议标准（默认未启用）" : "AI-proposed criteria (inactive by default)"}
              </strong>
              <ul>
                {review.response.result.proposed_success_criteria.map((item) => (
                  <li key={item.criterion_id}>
                    {item.metric} · {item.operator} · {item.threshold_guidance}
                  </li>
                ))}
              </ul>
            </div>
          ) : review.kind === "hypothesis" ? (
            <div className="research-reviewer-card__body">
              <p>
                {zh ? "可测试" : "Testable"}:{" "}
                {String(review.response.result.is_testable)} ·{" "}
                {zh ? "可证伪" : "Falsifiable"}:{" "}
                {String(review.response.result.is_falsifiable)}
              </p>
              <ul>
                {[
                  ...review.response.result.problems,
                  ...review.response.result.missing_elements,
                  ...review.response.result.warnings,
                ].map((item) => <li key={item}>{item}</li>)}
              </ul>
            </div>
          ) : review.kind === "missing" ? (
            <div className="research-reviewer-card__body">
              <p>{review.response.result.readiness_summary}</p>
              <ul>
                {review.response.result.recommended_next_steps.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ) : null}
          <footer>
            <button type="button" className="btn btn--primary" onClick={() => applyReview(false)}>
              {zh ? "应用" : "Apply"}
            </button>
            <button type="button" className="btn" onClick={() => applyReview(true)}>
              {zh ? "应用并编辑" : "Apply & Edit"}
            </button>
            <button type="button" className="btn" onClick={() => setReview(null)}>
              {zh ? "忽略" : "Dismiss"}
            </button>
          </footer>
          <p className="section-meta">
            {zh
              ? "AI 不计算指标、不覆盖确定性判定，也不做投资建议。"
              : "AI does not calculate metrics, override deterministic verdicts, or provide investment advice."}
          </p>
        </article>
      ) : null}
    </section>
  );
}
