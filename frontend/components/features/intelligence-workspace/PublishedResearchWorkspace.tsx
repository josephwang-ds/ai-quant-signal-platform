"use client";

import { useEffect, useMemo } from "react";
import { useSearchParams } from "next/navigation";
import AppShell from "@/components/layout/AppShell";
import WorkspaceHeader from "@/components/features/intelligence-workspace/WorkspaceHeader";
import WorkspaceNav from "@/components/features/intelligence-workspace/WorkspaceNav";
import {
  WorkspaceGateError,
  WorkspaceGateLoading,
} from "@/components/features/intelligence-workspace/WorkspaceStates";
import EvidenceView from "@/components/features/intelligence-workspace/views/EvidenceView";
import OverviewView from "@/components/features/intelligence-workspace/views/OverviewView";
import SignalsView from "@/components/features/intelligence-workspace/views/SignalsView";
import ValidationView from "@/components/features/intelligence-workspace/views/ValidationView";
import { usePublishedRun } from "@/lib/intelligence/usePublishedRun";
import {
  useSignalSnapshotContent,
  useSummarySnapshotContent,
} from "@/lib/intelligence/useSnapshotContent";
import {
  resolveWorkspaceView,
  selectSnapshotReference,
} from "@/lib/intelligence/workspaceDisplay";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

export type PublishedResearchWorkspaceProps = {
  runId: string;
};

/**
 * Phase 4.6C2 — published workspace with Overview + Signals snapshot content
 * on the accepted C1 shell (Evidence + Validation + hard gate).
 * Never imports localResearchRepository / ResearchRecord / catalog types.
 */
export default function PublishedResearchWorkspace({
  runId,
}: PublishedResearchWorkspaceProps) {
  const { language, setLanguage } = useWorkspaceLanguage();
  const searchParams = useSearchParams();
  const activeView = resolveWorkspaceView(searchParams.get("view"));

  const {
    gateStatus,
    gateError,
    run,
    artifacts,
    snapshots,
    retryGate,
    retryArtifacts,
    retrySnapshots,
  } = usePublishedRun(runId);

  const snapshotsReady = snapshots.status === "ready";
  const snapshotItems = snapshotsReady ? snapshots.items : [];

  const summaryRef = useMemo(
    () => selectSnapshotReference(snapshotItems, "research_summary"),
    [snapshotItems]
  );
  const signalRef = useMemo(
    () => selectSnapshotReference(snapshotItems, "signal"),
    [snapshotItems]
  );

  const summaryContent = useSummarySnapshotContent(
    runId,
    summaryRef,
    gateStatus === "ready" && snapshotsReady && activeView === "overview"
  );
  const signalContent = useSignalSnapshotContent(
    runId,
    signalRef,
    gateStatus === "ready" && snapshotsReady && activeView === "signals"
  );

  useEffect(() => {
    const heading = document.getElementById("workspace-view-heading");
    if (heading) {
      heading.focus({ preventScroll: true });
    }
  }, [activeView, gateStatus]);

  const zh = language === "zh";

  if (gateStatus === "loading") {
    return (
      <AppShell language={language} onLanguageChange={setLanguage}>
        <div className="published-workspace" data-testid="published-workspace">
          <WorkspaceGateLoading language={language} />
        </div>
      </AppShell>
    );
  }

  if (gateStatus === "not_found") {
    return (
      <AppShell language={language} onLanguageChange={setLanguage}>
        <div className="published-workspace" data-testid="published-workspace">
          <WorkspaceGateError
            language={language}
            title={
              zh ? "未找到已发布研究运行" : "Published research run not found"
            }
            message={
              zh
                ? "找不到该已发布研究运行。"
                : "Published research run not found."
            }
          />
        </div>
      </AppShell>
    );
  }

  if (gateStatus === "not_published") {
    return (
      <AppShell language={language} onLanguageChange={setLanguage}>
        <div className="published-workspace" data-testid="published-workspace">
          <WorkspaceGateError
            language={language}
            title={
              zh
                ? "研究运行不可作为已发布研究使用"
                : "Run is not available as published research"
            }
            message={
              zh
                ? "该研究运行不可作为已发布研究使用。"
                : "This run is not available as published research."
            }
          />
        </div>
      </AppShell>
    );
  }

  if (gateStatus === "unavailable") {
    return (
      <AppShell language={language} onLanguageChange={setLanguage}>
        <div className="published-workspace" data-testid="published-workspace">
          <WorkspaceGateError
            language={language}
            title={
              zh ? "已发布研究不可用" : "Published research unavailable"
            }
            message={
              gateError?.message ??
              (zh
                ? "该已发布研究标识不可用。"
                : "This published research identity is unavailable.")
            }
          />
        </div>
      </AppShell>
    );
  }

  if (gateStatus === "error" || !run) {
    return (
      <AppShell language={language} onLanguageChange={setLanguage}>
        <div className="published-workspace" data-testid="published-workspace">
          <WorkspaceGateError
            language={language}
            title={
              gateError?.category === "backend_unavailable"
                ? gateError.transportCode === "HTTP_429" ||
                  (gateError.message ?? "").toLowerCase().includes("busy right now")
                  ? zh
                    ? "请求过于频繁"
                    : "Too many requests"
                  : zh
                    ? "后端暂时不可用"
                    : "Backend temporarily unavailable"
                : gateError?.status === 401 || gateError?.status === 403
                  ? zh
                    ? "无权访问已发布研究"
                    : "Published research access denied"
                  : zh
                    ? "无法加载已发布研究"
                    : "Could not load published research"
            }
            message={
              gateError?.message ??
              (zh
                ? "已发布研究请求未能完成。"
                : "The published research request could not be completed.")
            }
            onRetry={
              gateError?.status === 401 || gateError?.status === 403
                ? undefined
                : retryGate
            }
          />
        </div>
      </AppShell>
    );
  }

  // Prefer cached summary content even when Overview is not the active view
  // (hook preserves ready/content while disabled).
  const analysisWindow = summaryContent.content?.analysis_window ?? null;
  const universeOverride =
    !run.universe && summaryContent.content?.universe
      ? summaryContent.content.universe
      : undefined;

  const overviewStatus =
    snapshots.status === "loading" || snapshots.status === "idle"
      ? "loading"
      : snapshots.status === "error"
        ? "error"
        : summaryContent.status;
  const signalsStatus =
    snapshots.status === "loading" || snapshots.status === "idle"
      ? "loading"
      : snapshots.status === "error"
        ? "error"
        : signalContent.status;

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <div className="published-workspace" data-testid="published-workspace">
        <WorkspaceHeader
          run={run}
          language={language}
          analysisWindow={analysisWindow}
          universeOverride={universeOverride}
        />
        <WorkspaceNav runId={run.run_id} activeView={activeView} language={language} />

        {activeView === "overview" ? (
          <OverviewView
            run={run}
            language={language}
            reference={
              snapshots.status === "ready" || snapshots.status === "error"
                ? summaryRef
                : null
            }
            status={overviewStatus}
            content={summaryContent.content}
            error={
              snapshots.status === "error"
                ? snapshots.error
                : summaryContent.error
            }
            onRetry={
              snapshots.status === "error"
                ? retrySnapshots
                : summaryContent.retry
            }
          />
        ) : null}

        {activeView === "signals" ? (
          <SignalsView
            runId={run.run_id}
            language={language}
            reference={
              snapshots.status === "ready" || snapshots.status === "error"
                ? signalRef
                : null
            }
            status={signalsStatus}
            content={signalContent.content}
            error={
              snapshots.status === "error"
                ? snapshots.error
                : signalContent.error
            }
            onRetry={
              snapshots.status === "error"
                ? retrySnapshots
                : signalContent.retry
            }
          />
        ) : null}

        {activeView === "evidence" ? (
          <EvidenceView
            language={language}
            snapshots={snapshots}
            artifacts={artifacts}
            onRetrySnapshots={retrySnapshots}
            onRetryArtifacts={retryArtifacts}
          />
        ) : null}

        {activeView === "validation" ? (
          <ValidationView
            run={run}
            language={language}
            summaryValidationStatus={
              summaryContent.content?.validation_status ?? null
            }
          />
        ) : null}
      </div>
    </AppShell>
  );
}
