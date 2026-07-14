"use client";

import WorkspacePlaceholder from "@/components/features/research/WorkspacePlaceholder";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

/**
 * 风控闸口审查：尚无确定性治理规则可应用于真实策略证据，
 * 因此展示诚实的规划状态占位，不再渲染任何虚构信号/闸口结论。
 */
export default function RiskGateReview() {
  const { tr } = useWorkspaceLanguage();

  return (
    <WorkspacePlaceholder
      title={tr("riskGateReview")}
      summary={tr("riskGateReviewPlaceholderSummary")}
      plannedCapabilities={[
        tr("riskGateReviewPlaceholderCap1"),
        tr("riskGateReviewPlaceholderCap2"),
        tr("riskGateReviewPlaceholderCap3"),
      ]}
      deferredNote={tr("publicPreviewDeferredNote")}
    />
  );
}
