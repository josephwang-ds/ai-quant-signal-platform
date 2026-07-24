"use client";

import { useState } from "react";
import StatusBadge from "@/components/ui/StatusBadge";
import { loadResearchGuidance } from "@/lib/researchGuidance";
import { reviewResearchEvidence } from "@/lib/researchReviewerApi";
import type { DecisionCenterModel } from "@/lib/researchDecision";
import type { Language } from "@/lib/i18n";
import type { FactorValidationResult } from "@/types/factorValidation";
import type { ResearchDetail } from "@/types/research";
import type { BenchmarkEvaluation } from "@/types/researchBenchmark";
import type { ResearchValidationResult } from "@/types/researchValidation";
import type {
  EvidenceReviewResult,
  ResearchReviewerResponse,
} from "@/types/researchReviewer";

type Props = {
  research: ResearchDetail;
  model: DecisionCenterModel;
  benchmark: BenchmarkEvaluation | null;
  validation: ResearchValidationResult | null;
  factorValidation: FactorValidationResult | null;
  evidenceTimestamp: string | null;
  language: Language;
  onApplyToNote: (value: string) => void;
};

export default function DeepSeekEvidenceReviewerCard({
  research,
  model,
  benchmark,
  validation,
  factorValidation,
  evidenceTimestamp,
  language,
  onApplyToNote,
}: Props) {
  const zh = language === "zh";
  const [status, setStatus] = useState<"idle" | "loading" | "ready" | "error">(
    "idle"
  );
  const [error, setError] = useState("");
  const [review, setReview] =
    useState<ResearchReviewerResponse<EvidenceReviewResult> | null>(null);

  async function runReview() {
    setStatus("loading");
    setError("");
    try {
      const definition = loadResearchGuidance(research);
      const response = await reviewResearchEvidence({
        research_definition: {
          research_question: definition.researchQuestion,
          hypothesis: definition.hypothesis,
          null_hypothesis: definition.nullHypothesis,
          mechanism: definition.mechanism,
          primary_benchmark: definition.primaryBenchmark,
        },
        configured_success_criteria: definition.successCriteria.filter(
          (item) => item.active
        ),
        benchmark_evaluation: benchmark ?? {
          verdict: "unavailable",
          checks: [],
          rationale: "Deterministic benchmark evidence is unavailable.",
        },
        deterministic_decision_support: {
          suggested_decision: model.suggestedDecision,
          benchmark_verdict: model.benchmarkVerdict,
          evidence_summary: model.evidenceSummary,
          checks: model.checks,
          required_next_steps: model.requiredNextSteps,
        },
        validation_metrics: validation
          ? {
              status: validation.validation_status,
              oos: validation.oos,
              transaction_cost_sensitivity:
                validation.transaction_cost_sensitivity,
            }
          : {},
        robustness_results: validation
          ? {
              parameter_sensitivity: {
                status: validation.parameter_sensitivity.status,
                valid_combination_count:
                  validation.parameter_sensitivity.valid_combination_count,
                positive_sharpe_count:
                  validation.parameter_sensitivity.positive_sharpe_count,
                median_sharpe: validation.parameter_sensitivity.median_sharpe,
              },
            }
          : factorValidation
            ? { rank_ic_summary: factorValidation.ic.summary }
            : {},
        data_quality_findings: validation?.data_quality ?? {},
        known_limitations: definition.knownLimitations,
        evidence_snapshot_timestamp: evidenceTimestamp,
      });
      setReview(response);
      setStatus("ready");
    } catch (cause) {
      setStatus("error");
      setError(
        cause instanceof Error
          ? cause.message
          : zh
            ? "DeepSeek 证据审阅当前不可用。"
            : "DeepSeek evidence review is unavailable."
      );
    }
  }

  if (!review) {
    return (
      <div className="research-reviewer-launch">
        <div>
          <strong>
            {zh ? "DeepSeek 证据审阅" : "DeepSeek Evidence Review"}
          </strong>
          <p>
            {zh
              ? "只解释当前确定性证据快照，不重新计算指标，也不覆盖系统建议或人工决定。"
              : "Interprets the current deterministic evidence snapshot only; it does not recalculate metrics or override system/human decisions."}
          </p>
          {error ? <p className="field-error">{error}</p> : null}
        </div>
        <button
          type="button"
          className="btn"
          disabled={status === "loading"}
          onClick={() => void runReview()}
        >
          {status === "loading"
            ? zh
              ? "正在审阅…"
              : "Reviewing…"
            : zh
              ? "审阅研究证据"
              : "Review Research Evidence"}
        </button>
      </div>
    );
  }

  const note = [
    review.result.executive_summary,
    review.result.benchmark_assessment,
    ...review.result.decision_considerations,
  ].join("\n");

  return (
    <article className="research-reviewer-card">
      <header>
        <div>
          <p className="section-eyebrow">
            {zh ? "AI 辅助解释 · 未保存" : "AI-assisted interpretation · unsaved"}
          </p>
          <h4>{zh ? "证据审阅" : "Evidence review"}</h4>
        </div>
        <span>
          {review.provider} · {review.model} ·{" "}
          {new Date(review.generated_at).toLocaleString()}
        </span>
      </header>
      <div className="research-reviewer-card__body">
        <StatusBadge
          label={review.result.hypothesis_assessment.replaceAll("_", " ")}
          variant={
            review.result.hypothesis_assessment === "supported"
              ? "success"
              : review.result.hypothesis_assessment === "not_supported"
                ? "danger"
                : "warning"
          }
        />
        <p>{review.result.executive_summary}</p>
        <p>{review.result.benchmark_assessment}</p>
        {[
          ["Supporting evidence", review.result.supporting_evidence],
          ["Contradicting evidence", review.result.contradicting_evidence],
        ].map(([title, items]) =>
          Array.isArray(items) && items.length ? (
            <div key={String(title)}>
              <strong>{String(title)}</strong>
              <ul>
                {items.map((item) => (
                  <li key={item.evidence_reference}>
                    {item.claim} <code>{item.evidence_reference}</code>
                  </li>
                ))}
              </ul>
            </div>
          ) : null
        )}
        {review.result.recommended_additional_validation.length ? (
          <div>
            <strong>{zh ? "建议补充验证" : "Additional validation"}</strong>
            <ul>
              {review.result.recommended_additional_validation.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
      <footer>
        <button
          type="button"
          className="btn btn--primary"
          onClick={() => {
            onApplyToNote(note);
            setReview(null);
          }}
        >
          {zh ? "应用到审阅备注" : "Apply to reviewer note"}
        </button>
        <button
          type="button"
          className="btn"
          onClick={() => onApplyToNote(note)}
        >
          {zh ? "应用并编辑" : "Apply & Edit"}
        </button>
        <button type="button" className="btn" onClick={() => setReview(null)}>
          {zh ? "忽略" : "Dismiss"}
        </button>
      </footer>
      <p className="section-meta">
        {zh
          ? `证据快照：${review.evidence_snapshot_timestamp ?? "未提供"}。AI 不提供投资建议。`
          : `Evidence snapshot: ${review.evidence_snapshot_timestamp ?? "not supplied"}. AI does not provide investment advice.`}
      </p>
    </article>
  );
}
