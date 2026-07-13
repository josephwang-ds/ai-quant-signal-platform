"use client";

import { useEffect, useMemo } from "react";
import SectionHeader from "@/components/ui/SectionHeader";
import StatusBadge from "@/components/ui/StatusBadge";
import {
  buildBacktestExplanationPayload,
  buildBacktestManagementInterpretation,
  buildBacktestReviewFindings,
  calculateBacktestRiskLevel,
  calculatePaperTradingEligibility,
  riskLevelToBadgeLevel,
} from "@/lib/backtestReview";
import { paperRiskVariant, translateRiskLabel } from "@/lib/i18n";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";
import type { BacktestResponse } from "@/types/market";

type BacktestReviewPanelProps = {
  result: BacktestResponse;
};

export default function BacktestReviewPanel({ result }: BacktestReviewPanelProps) {
  const { language, tr } = useWorkspaceLanguage();

  const maxDrawdown =
    result.metrics.strategy_max_drawdown ?? result.metrics.max_drawdown;
  const riskLevel = calculateBacktestRiskLevel(maxDrawdown);
  const eligibility = calculatePaperTradingEligibility(riskLevel);
  const findings = buildBacktestReviewFindings(result, language);
  const managementInterpretation = buildBacktestManagementInterpretation(
    result,
    riskLevel,
    eligibility,
    language
  );

  const explanationPayload = useMemo(
    () => buildBacktestExplanationPayload(result, language),
    [result, language]
  );

  useEffect(() => {
    if (process.env.NODE_ENV !== "production") {
      console.debug("[BacktestReview] explanationPayload", explanationPayload);
    }
  }, [explanationPayload]);

  const eligibilityLabel =
    eligibility === "eligible"
      ? tr("backtestReviewEligible")
      : eligibility === "watch"
        ? tr("backtestReviewWatch")
        : tr("backtestReviewNotEligible");

  const eligibilityVariant =
    eligibility === "eligible" ? "success" : eligibility === "watch" ? "warning" : "danger";

  return (
    <section className="backtest-review">
      <SectionHeader
        title={tr("backtestReviewTitle")}
        description={tr("backtestReviewDesc")}
      />
      <p className="section-meta">{tr("backtestReviewNote")}</p>

      <div className="backtest-review__status-row">
        <div className="backtest-review__status">
          <span className="backtest-review__label">{tr("backtestReviewRiskLevel")}</span>
          <StatusBadge
            label={translateRiskLabel(language, riskLevel)}
            variant={paperRiskVariant(riskLevelToBadgeLevel(riskLevel))}
          />
        </div>
        <div className="backtest-review__status">
          <span className="backtest-review__label">{tr("backtestReviewPaperEligibility")}</span>
          <StatusBadge label={eligibilityLabel} variant={eligibilityVariant} />
        </div>
      </div>

      <h4 className="paper-subtitle">{tr("backtestReviewKeyFindings")}</h4>
      <ul className="paper-reason-list backtest-review__findings">
        {findings.map((finding) => (
          <li key={finding}>{finding}</li>
        ))}
      </ul>

      <h4 className="paper-subtitle">{tr("backtestReviewManagement")}</h4>
      <p className="section-meta backtest-review__interpretation">{managementInterpretation}</p>
    </section>
  );
}
