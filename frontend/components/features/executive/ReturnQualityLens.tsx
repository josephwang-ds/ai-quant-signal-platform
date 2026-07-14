"use client";

import WorkspacePlaceholder from "@/components/features/research/WorkspacePlaceholder";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

/**
 * 收益质量透视：尚未接入研究执行/验证引擎产出的真实证据，
 * 因此展示诚实的规划状态占位，不再渲染任何虚构指标。
 */
export default function ReturnQualityLens() {
  const { tr } = useWorkspaceLanguage();

  return (
    <WorkspacePlaceholder
      title={tr("returnQualityLens")}
      summary={tr("returnQualityLensPlaceholderSummary")}
      plannedCapabilities={[
        tr("returnQualityLensPlaceholderCap1"),
        tr("returnQualityLensPlaceholderCap2"),
        tr("returnQualityLensPlaceholderCap3"),
      ]}
      deferredNote={tr("publicPreviewDeferredNote")}
    />
  );
}
