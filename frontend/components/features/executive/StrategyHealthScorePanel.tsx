"use client";

import WorkspacePlaceholder from "@/components/features/research/WorkspacePlaceholder";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

/**
 * 策略健康度评分：尚无真实的验证/评估证据可支撑综合评分方法，
 * 因此展示诚实的规划状态占位，不再渲染任何虚构分数。
 */
export default function StrategyHealthScorePanel() {
  const { tr } = useWorkspaceLanguage();

  return (
    <WorkspacePlaceholder
      title={tr("strategyHealthScore")}
      summary={tr("strategyHealthScorePlaceholderSummary")}
      plannedCapabilities={[
        tr("strategyHealthScorePlaceholderCap1"),
        tr("strategyHealthScorePlaceholderCap2"),
        tr("strategyHealthScorePlaceholderCap3"),
      ]}
      deferredNote={tr("publicPreviewDeferredNote")}
    />
  );
}
