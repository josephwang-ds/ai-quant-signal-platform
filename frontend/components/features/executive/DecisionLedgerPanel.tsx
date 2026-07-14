"use client";

import WorkspacePlaceholder from "@/components/features/research/WorkspacePlaceholder";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

/**
 * 决策留痕台账：尚无真实治理决策证据可记录，
 * 因此展示诚实的规划状态占位，不再渲染任何虚构台账条目。
 */
export default function DecisionLedgerPanel() {
  const { tr } = useWorkspaceLanguage();

  return (
    <WorkspacePlaceholder
      title={tr("decisionLedger")}
      summary={tr("decisionLedgerPlaceholderSummary")}
      plannedCapabilities={[
        tr("decisionLedgerPlaceholderCap1"),
        tr("decisionLedgerPlaceholderCap2"),
        tr("decisionLedgerPlaceholderCap3"),
      ]}
      deferredNote={tr("publicPreviewDeferredNote")}
    />
  );
}
