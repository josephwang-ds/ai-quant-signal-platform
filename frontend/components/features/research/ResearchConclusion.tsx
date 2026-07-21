"use client";

import StatusBadge from "@/components/ui/StatusBadge";
import type { Language } from "@/lib/i18n";
import type {
  EvaluationStatus,
  ResearchEvaluationResult,
} from "@/types/researchEvaluation";

export type ResearchConclusionLabels = {
  title: string;
  notRequested: string;
  incomplete: string;
  blocked: string;
  completed: string;
  coverageLabel: string;
  keyStrengthsLabel: string;
  limitationLabel: string;
  nextActionLabel: string;
};

export type ResearchConclusionProps = {
  language: Language;
  evaluation: ResearchEvaluationResult | null;
  evaluationReady: boolean;
  labels: ResearchConclusionLabels;
  showTitle?: boolean;
};

function statusBadgeTone(status: EvaluationStatus): "success" | "warning" | "danger" {
  if (status === "completed") return "success";
  if (status === "blocked") return "danger";
  return "warning";
}

function localizeEvaluationText(value: string, language: Language): string {
  if (language !== "zh") return value;
  const exact: Record<string, string> = {
    "Historical backtest": "历史回测",
    "Benchmark comparison": "基准对比",
    "Out-of-sample validation": "样本外验证",
    "Parameter sensitivity": "参数敏感性",
    "Transaction-cost sensitivity": "交易成本敏感性",
    "Data quality": "数据质量",
    "Full-history deterministic MA-crossover evidence was calculated.": "已完成全历史区间的确定性均线交叉回测。",
    "The strategy was compared with same-asset buy-and-hold.": "策略已与同一标的的买入并持有基准完成对比。",
    "Chronological OOS evidence completed with fixed parameters.": "已使用固定参数完成按时间顺序切分的样本外验证。",
    "Evaluation is based on historical evidence only; it performs no new calculations.": "评估仅基于历史证据，不执行新的计算。",
  };
  return exact[value] ?? value;
}

export default function ResearchConclusion({
  language,
  evaluation,
  evaluationReady,
  labels,
  showTitle = true,
}: ResearchConclusionProps) {
  if (!evaluationReady || !evaluation) {
    return null;
  }

  const statusLabel =
    evaluation.evaluation_status === "completed"
      ? labels.completed
      : evaluation.evaluation_status === "blocked"
        ? labels.blocked
        : labels.incomplete;

  const strongestEvidence = (() => {
    const completed = evaluation.evidence_summary.find((item) => item.status === "completed");
    if (!completed) return null;
    return `${localizeEvaluationText(completed.label, language)}: ${localizeEvaluationText(completed.summary, language)}`;
  })();

  const mostImportantLimitation = evaluation.limitations?.[0]
    ? localizeEvaluationText(evaluation.limitations[0], language)
    : null;

  const nextRequiredAction = (() => {
    if (evaluation.evaluation_status === "completed") {
      return null;
    }
    if (evaluation.outstanding_evidence?.length) {
      return localizeEvaluationText(evaluation.outstanding_evidence[0], language);
    }
    if (evaluation.evaluation_status === "blocked") {
      return labels.blocked;
    }
    return labels.incomplete;
  })();

  const coverage = evaluation.evidence_coverage?.coverage_percentage ?? null;

  return (
    <section
      className={`overview-conclusion overview-conclusion--${statusBadgeTone(evaluation.evaluation_status)}`}
      aria-label={labels.title}
    >
      <header className="overview-conclusion__header">
        {showTitle ? (
          <h3 className="overview-conclusion__eyebrow">{labels.title}</h3>
        ) : (
          <span className="overview-conclusion__eyebrow-spacer" />
        )}
        <StatusBadge
          label={statusLabel}
          variant={statusBadgeTone(evaluation.evaluation_status)}
        />
      </header>

      <div className="overview-conclusion__items">
        {strongestEvidence ? (
          <p className="overview-conclusion__finding">
            <span className="overview-conclusion__finding-label">{labels.keyStrengthsLabel}</span>
            {strongestEvidence}
          </p>
        ) : null}
        {mostImportantLimitation ? (
          <p className="overview-conclusion__finding overview-conclusion__finding--secondary">
            <span className="overview-conclusion__finding-label">{labels.limitationLabel}</span>
            {mostImportantLimitation}
          </p>
        ) : null}
        {nextRequiredAction ? (
          <p className="overview-conclusion__finding overview-conclusion__finding--secondary">
            <span className="overview-conclusion__finding-label">{labels.nextActionLabel}</span>
            {nextRequiredAction}
          </p>
        ) : null}
      </div>

      {coverage !== null ? (
        <p className="overview-conclusion__coverage section-meta">
          {labels.coverageLabel}: {coverage}%
        </p>
      ) : null}
    </section>
  );
}
