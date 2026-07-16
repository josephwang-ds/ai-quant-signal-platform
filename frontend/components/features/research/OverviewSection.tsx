import Button from "@/components/ui/Button";
import MetricSummaryCard from "@/components/ui/MetricSummaryCard";
import StatusBadge from "@/components/ui/StatusBadge";
import type { ReactNode } from "react";
import type { Language } from "@/lib/i18n";
import type { ResearchDetail } from "@/types/research";
import type { ResearchExecutionResult, ResearchExecutionStatus } from "@/types/researchExecution";
import type {
  ResearchEvaluationResult,
  EvaluationStatus,
  ResearchEvaluationRequestStatus,
} from "@/types/researchEvaluation";
import type { ResearchValidationResult, ResearchValidationStatus } from "@/types/researchValidation";

export type OverviewSectionLabels = {
  briefTitle: string;
  keyResultsTitle: string;
  guidedWorkflowTitle: string;
  conclusionTitle: string;

  datasetPeriodLabel: string;
  strategyRuleLabel: string;
  evidenceStatusLabel: string;
  decisionStatusLabel: string;

  evidenceComplete: string;
  evidenceIncomplete: string;
  evidencePending: string;

  decisionPending: string;
  evaluationCompleted: string;
  evaluationIncomplete: string;
  evaluationBlocked: string;

  coverageLabel: string;
  keyStrengthsLabel: string;
  limitationLabel: string;
  nextActionLabel: string;

  // Key results metric labels
  strategyTotalReturnLabel: string;
  benchmarkTotalReturnLabel: string;
  maxDrawdownLabel: string;
  oosSharpeLabel: string;

  // Unavailable messages (no fabricated placeholder metrics)
  keyResultsUnavailable: string;
  oosSharpeUnavailable: string;

  // Guided workflow step labels / CTAs
  stepRunResearch: string;
  stepValidateEvidence: string;
  stepReviewEvaluation: string;
  stepAskCopilot: string;

  ctaRunResearch: string;
  ctaResearchLoading: string;
  ctaRetryResearch: string;

  ctaRunValidation: string;
  ctaRequestEvaluation: string;
  ctaAskCopilot: string;
};

export type OverviewSectionProps = {
  language: Language;
  research: ResearchDetail;
  executionStatus: ResearchExecutionStatus;
  execution: ResearchExecutionResult | null;
  validationStatus: ResearchValidationStatus;
  validation: ResearchValidationResult | null;
  evaluationStatus: ResearchEvaluationRequestStatus;
  evaluation: ResearchEvaluationResult | null;
  onRunResearch: () => void;
  onRunValidation: () => void;
  onRequestEvaluation: () => void;
  onAskCopilot: () => void;
  labels: OverviewSectionLabels;
  provenanceSlot?: ReactNode;
};

function formatIsoDateShort(value: string, language: Language): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const locale = language === "zh" ? "zh-CN" : "en-US";
  return date.toLocaleDateString(locale, { year: "numeric", month: "short", day: "numeric" });
}

function formatPct(value: number | null | undefined): string | null {
  if (value === null || value === undefined || Number.isNaN(value)) return null;
  return `${(value * 100).toFixed(1)}%`;
}

function formatNum2(value: number | null | undefined): string | null {
  if (value === null || value === undefined || Number.isNaN(value)) return null;
  return value.toFixed(2);
}

function statusBadgeTone(evaluationStatus: EvaluationStatus): "success" | "warning" | "danger" {
  if (evaluationStatus === "completed") return "success";
  if (evaluationStatus === "blocked") return "danger";
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
    "Stress testing": "压力测试",
    "Regime analysis": "市场状态分析",
    "Walk-forward validation": "滚动前向验证",
    "Monte Carlo simulation": "蒙特卡洛模拟",
    "Paper trading": "模拟试盘",
    "Full-history deterministic MA-crossover evidence was calculated.": "已完成全历史区间的确定性均线交叉回测。",
    "The strategy was compared with same-asset buy-and-hold.": "策略已与同一标的的买入并持有基准完成对比。",
    "Chronological OOS evidence completed with fixed parameters.": "已使用固定参数完成按时间顺序切分的样本外验证。",
    "Data-quality review found 0 fatal issues and 3 non-fatal limitations.": "数据质量检查未发现致命问题，记录了 3 项非致命限制。",
    "Evaluation is based on historical evidence only; it performs no new calculations.": "评估仅基于历史证据，不执行新的计算。",
    "Independent benchmark comparison is unavailable; benchmark evidence uses same-asset buy-and-hold only.": "当前基准证据仅使用同一标的买入并持有，尚无独立基准对比。",
    "Stress testing is not implemented.": "尚未完成压力测试。",
    "Regime analysis is not implemented.": "尚未完成市场状态分析。",
    "Walk-forward validation is not implemented.": "尚未完成滚动前向验证。",
    "Monte Carlo simulation is not implemented.": "尚未完成蒙特卡洛模拟。",
    "Research has not been published.": "研究尚未发布。",
    "Paper trading is unavailable.": "尚未进入模拟试盘。",
  };
  if (exact[value]) return exact[value];
  return value;
}

export default function OverviewSection({
  language,
  research,
  executionStatus,
  execution,
  validationStatus,
  validation,
  evaluationStatus,
  evaluation,
  onRunResearch,
  onRunValidation,
  onRequestEvaluation,
  onAskCopilot,
  labels,
  provenanceSlot = null,
}: OverviewSectionProps) {
  const executionReady = executionStatus === "ready" && Boolean(execution);
  const validationRunId = validation?.validation_run_id ?? null;
  const validationReady = validationStatus === "ready" && Boolean(validation);
  const evidenceComplete = Boolean(validation?.evidence_complete);

  const evaluationReady = evaluationStatus === "ready" && Boolean(evaluation);
  const evaluationCoverage = evaluation?.evidence_coverage?.coverage_percentage ?? null;

  const datasetPeriod =
    execution?.provenance?.actual_start && execution?.provenance?.actual_end
      ? `${formatIsoDateShort(execution.provenance.actual_start, language)} → ${formatIsoDateShort(execution.provenance.actual_end, language)}`
      : research.runConfiguration
        ? `${formatIsoDateShort(research.runConfiguration.startDate, language)} → ${
            research.runConfiguration.endDate
              ? formatIsoDateShort(research.runConfiguration.endDate, language)
              : "—"
          }`
        : null;

  const benchmarkSymbol =
    execution?.provenance?.symbol ?? research.configuration?.symbol ?? research.configuration?.benchmark;

  const maWindows = (() => {
    const shortFromExecution =
      execution && typeof (execution.strategy as any)?.short_window === "number"
        ? ((execution.strategy as any).short_window as number)
        : null;
    const longFromExecution =
      execution && typeof (execution.strategy as any)?.long_window === "number"
        ? ((execution.strategy as any).long_window as number)
        : null;
    if (typeof shortFromExecution === "number" && typeof longFromExecution === "number") {
      return { shortWindow: shortFromExecution, longWindow: longFromExecution };
    }

    const parameterLines = research.configuration?.parameterLines ?? [];
    const shortMatch = parameterLines
      .map((line) => line.trim())
      .find((line) => /^Short Window\s*:/i.test(line));
    const longMatch = parameterLines
      .map((line) => line.trim())
      .find((line) => /^Long Window\s*:/i.test(line));
    const shortWindow = shortMatch ? Number(shortMatch.replace(/[^\d]/g, "")) : null;
    const longWindow = longMatch ? Number(longMatch.replace(/[^\d]/g, "")) : null;
    if (typeof shortWindow === "number" && typeof longWindow === "number") {
      return { shortWindow, longWindow };
    }
    return { shortWindow: null, longWindow: null };
  })();

  const strategyRule =
    maWindows.shortWindow && maWindows.longWindow
      ? `MA${maWindows.shortWindow} / MA${maWindows.longWindow} · ${benchmarkSymbol ?? "—"}`
      : "—";

  const evidenceStatus =
    validationReady
      ? evidenceComplete
        ? labels.evidenceComplete
        : labels.evidenceIncomplete
      : labels.evidencePending;

  const decisionStatus = (() => {
    if (!evaluationReady || !evaluation) return labels.decisionPending;
    if (evaluation.evaluation_status === "completed") return labels.evaluationCompleted;
    if (evaluation.evaluation_status === "blocked") return labels.evaluationBlocked;
    return labels.evaluationIncomplete;
  })();

  const oosSharpeValue = validation?.oos?.out_of_sample_metrics?.sharpe_ratio ?? null;
  const oosSharpeFormatted = formatNum2(oosSharpeValue);

  const strategyTotalReturnFormatted = formatPct(execution?.metrics?.total_return);
  const benchmarkTotalReturnFormatted = formatPct(execution?.benchmark_metrics?.total_return);
  const maxDrawdownFormatted = formatPct(execution?.metrics?.maximum_drawdown);

  const primaryStep = (() => {
    if (!executionReady) return "research";
    if (!validationRunId) return "validation";
    if (!evaluationReady) return "evaluation";
    return "copilot";
  })();

  function primaryButton(): { label: string; onClick: () => void; disabled: boolean } {
    if (primaryStep === "research") {
      if (executionStatus === "error") {
        return { label: labels.ctaRetryResearch, onClick: onRunResearch, disabled: false };
      }
      if (executionStatus === "loading" || executionStatus === "idle") {
        return { label: labels.ctaResearchLoading, onClick: onRunResearch, disabled: true };
      }
      return { label: labels.ctaRunResearch, onClick: onRunResearch, disabled: false };
    }
    if (primaryStep === "validation") {
      return { label: labels.ctaRunValidation, onClick: onRunValidation, disabled: false };
    }
    if (primaryStep === "evaluation") {
      return { label: labels.ctaRequestEvaluation, onClick: onRequestEvaluation, disabled: false };
    }
    return { label: labels.ctaAskCopilot, onClick: onAskCopilot, disabled: false };
  }

  const primary = primaryButton();

  const strongestEvidence = (() => {
    if (!evaluation) return null;
    const completed = evaluation.evidence_summary.find((item) => item.status === "completed");
    if (!completed) return null;
    return `${localizeEvaluationText(completed.label, language)}: ${localizeEvaluationText(completed.summary, language)}`;
  })();

  const mostImportantLimitation = (() => {
    if (!evaluation?.limitations?.length) return null;
    return localizeEvaluationText(evaluation.limitations[0], language);
  })();

  const nextRequiredAction = (() => {
    if (!evaluation) return null;
    if (evaluation.evaluation_status === "completed") {
      return labels.stepAskCopilot;
    }
    if (evaluation.outstanding_evidence?.length) {
      return localizeEvaluationText(evaluation.outstanding_evidence[0], language);
    }
    return null;
  })();

  return (
    <div className="overview-narrative">
      <section className="overview-block" aria-label={labels.briefTitle}>
        <h3 className="overview-block__title">{labels.briefTitle}</h3>

        <dl className="research-overview-hero__meta">
          <div>
            <dt>{labels.datasetPeriodLabel}</dt>
            <dd>{datasetPeriod ?? "—"}</dd>
          </div>
          <div>
            <dt>{labels.strategyRuleLabel}</dt>
            <dd>{strategyRule || "—"}</dd>
          </div>
          <div>
            <dt>{evidenceStatus ? labels.evidenceStatusLabel : labels.evidenceStatusLabel}</dt>
            <dd>{evidenceStatus}</dd>
          </div>
          <div>
            <dt>{labels.decisionStatusLabel}</dt>
            <dd>{decisionStatus}</dd>
          </div>
        </dl>
      </section>

      <section className="overview-block" aria-label={labels.keyResultsTitle}>
        <h3 className="overview-block__title">{labels.keyResultsTitle}</h3>

        {!executionReady ? (
          <p className="section-meta">{labels.keyResultsUnavailable}</p>
        ) : (
          <div className="research-overview__metrics">
            <MetricSummaryCard
              label={labels.strategyTotalReturnLabel}
              value={strategyTotalReturnFormatted ?? "—"}
            />
            <MetricSummaryCard
              label={labels.benchmarkTotalReturnLabel}
              value={benchmarkTotalReturnFormatted ?? "—"}
            />
            <MetricSummaryCard
              label={labels.maxDrawdownLabel}
              value={maxDrawdownFormatted ?? "—"}
            />
            <MetricSummaryCard
              label={labels.oosSharpeLabel}
              value={
                oosSharpeFormatted
                  ? oosSharpeFormatted
                  : labels.oosSharpeUnavailable
              }
            />
          </div>
        )}
      </section>

      <section className="overview-block" aria-label={labels.guidedWorkflowTitle}>
        <h3 className="overview-block__title">{labels.guidedWorkflowTitle}</h3>

        <ul className="research-guided-steps">
          <li className={`research-guided-step ${primaryStep === "research" ? "is-current" : ""}`}>
            <span className="research-guided-step__name">{labels.stepRunResearch}</span>
            <span className="research-guided-step__status">{executionReady ? "✓" : "•"}</span>
          </li>
          <li className={`research-guided-step ${primaryStep === "validation" ? "is-current" : ""}`}>
            <span className="research-guided-step__name">{labels.stepValidateEvidence}</span>
            <span className="research-guided-step__status">{validationRunId ? "✓" : "•"}</span>
          </li>
          <li className={`research-guided-step ${primaryStep === "evaluation" ? "is-current" : ""}`}>
            <span className="research-guided-step__name">{labels.stepReviewEvaluation}</span>
            <span className="research-guided-step__status">{evaluationReady ? "✓" : "•"}</span>
          </li>
          <li className={`research-guided-step ${primaryStep === "copilot" ? "is-current" : ""}`}>
            <span className="research-guided-step__name">{labels.stepAskCopilot}</span>
            <span className="research-guided-step__status">{evaluationReady ? "✓" : "•"}</span>
          </li>
        </ul>

        <div className="overview-guided-cta">
          <Button primary disabled={primary.disabled} onClick={primary.onClick}>
            {primary.label}
          </Button>
        </div>
      </section>

      <section className="overview-block overview-conclusion" aria-label={labels.conclusionTitle}>
        <h3 className="overview-block__title">{labels.conclusionTitle}</h3>

        {evaluationReady && evaluation ? (
          <>
            <div className="overview-conclusion__status">
              <StatusBadge
                label={
                  evaluation.evaluation_status === "completed"
                    ? labels.evaluationCompleted
                    : evaluation.evaluation_status === "blocked"
                      ? labels.evaluationBlocked
                      : labels.evaluationIncomplete
                }
                variant={statusBadgeTone(evaluation.evaluation_status)}
              />
              {evaluationCoverage !== null ? (
                <span className="section-meta">
                  {labels.coverageLabel}: {evaluationCoverage}%
                </span>
              ) : null}
            </div>

            <div className="overview-conclusion__items">
              <div>
                <dt className="sr-only">{labels.keyStrengthsLabel}</dt>
                <p className="section-meta">
                  <strong>{labels.keyStrengthsLabel}:</strong> {strongestEvidence ?? "—"}
                </p>
              </div>
              <div>
                <p className="section-meta">
                  <strong>{labels.limitationLabel}:</strong> {mostImportantLimitation ?? "—"}
                </p>
              </div>
              <div>
                <p className="section-meta">
                  <strong>{labels.nextActionLabel}:</strong> {nextRequiredAction ?? "—"}
                </p>
              </div>
            </div>
          </>
        ) : (
          <p className="section-meta">{labels.decisionPending}</p>
        )}
      </section>

      {provenanceSlot ? <div className="overview-provenance">{provenanceSlot}</div> : null}
    </div>
  );
}
