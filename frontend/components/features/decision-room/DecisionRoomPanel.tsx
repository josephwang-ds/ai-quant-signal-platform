"use client";

import WorkspacePlaceholder from "@/components/features/research/WorkspacePlaceholder";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

/**
 * 策略决策室：尚无治理化的真实 AI 解读能力可解释信号 → 闸口 → 动作，
 * 因此展示诚实的规划状态占位，不再渲染任何虚构角色解读或检索片段。
 */
export default function DecisionRoomPanel() {
  const { tr } = useWorkspaceLanguage();

  return (
    <WorkspacePlaceholder
      title={tr("decisionRoom")}
      summary={tr("decisionRoomPlaceholderSummary")}
      plannedCapabilities={[
        tr("decisionRoomPlaceholderCap1"),
        tr("decisionRoomPlaceholderCap2"),
        tr("decisionRoomPlaceholderCap3"),
      ]}
      deferredNote={tr("publicPreviewDeferredNote")}
    />
  );
}
