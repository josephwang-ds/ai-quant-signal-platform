"use client";

import WorkspacePlaceholder from "@/components/features/research/WorkspacePlaceholder";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

/**
 * 情景冲击测试：尚无真实的压力/regime 场景计算能力，
 * 因此展示诚实的规划状态占位，不再渲染任何虚构冲击结果。
 */
export default function ScenarioShockTestPanel() {
  const { tr } = useWorkspaceLanguage();

  return (
    <WorkspacePlaceholder
      title={tr("scenarioShockTest")}
      summary={tr("scenarioShockTestPlaceholderSummary")}
      plannedCapabilities={[
        tr("scenarioShockTestPlaceholderCap1"),
        tr("scenarioShockTestPlaceholderCap2"),
        tr("scenarioShockTestPlaceholderCap3"),
      ]}
      deferredNote={tr("publicPreviewDeferredNote")}
    />
  );
}
