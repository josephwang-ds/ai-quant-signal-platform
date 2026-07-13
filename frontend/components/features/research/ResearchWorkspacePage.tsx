"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import AppShell from "@/components/layout/AppShell";
import EvidenceSummary from "@/components/features/research/EvidenceSummary";
import OverviewSection from "@/components/features/research/OverviewSection";
import ResearchActionPanel from "@/components/features/research/ResearchActionPanel";
import ResearchWorkspaceHeader from "@/components/features/research/ResearchWorkspaceHeader";
import ResearchWorkspaceNavigation from "@/components/features/research/ResearchWorkspaceNavigation";
import ResearchWorkspaceSkeleton from "@/components/features/research/ResearchWorkspaceSkeleton";
import WorkspacePlaceholder from "@/components/features/research/WorkspacePlaceholder";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import ErrorAlert from "@/components/ui/ErrorAlert";
import LoadingState from "@/components/ui/LoadingState";
import SectionCard from "@/components/ui/SectionCard";
import type { TranslationKey } from "@/lib/i18n";
import {
  loadMockResearchById,
  MockResearchError,
} from "@/lib/mockResearchCatalog";
import { isResearchWorkspaceSection } from "@/lib/researchWorkspace";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";
import type {
  ResearchDetail,
  ResearchWorkspaceSection,
} from "@/types/research";

type LoadStatus = "loading" | "ready" | "error" | "not_found";

type PlaceholderCopy = {
  titleKey: TranslationKey;
  summaryKey: TranslationKey;
  capabilityKeys: TranslationKey[];
};

const PLACEHOLDER_COPY: Record<
  Exclude<ResearchWorkspaceSection, "overview">,
  PlaceholderCopy
> = {
  notebook: {
    titleKey: "researchWsNotebookTitle",
    summaryKey: "researchWsNotebookSummary",
    capabilityKeys: [
      "researchWsNotebookCap1",
      "researchWsNotebookCap2",
      "researchWsNotebookCap3",
    ],
  },
  experiments: {
    titleKey: "researchWsExperimentsTitle",
    summaryKey: "researchWsExperimentsSummary",
    capabilityKeys: [
      "researchWsExperimentsCap1",
      "researchWsExperimentsCap2",
      "researchWsExperimentsCap3",
    ],
  },
  validation: {
    titleKey: "researchWsValidationTitle",
    summaryKey: "researchWsValidationSectionSummary",
    capabilityKeys: [
      "researchWsValidationCap1",
      "researchWsValidationCap2",
      "researchWsValidationCap3",
    ],
  },
  evaluation: {
    titleKey: "researchWsEvaluationTitle",
    summaryKey: "researchWsEvaluationSummary",
    capabilityKeys: [
      "researchWsEvaluationCap1",
      "researchWsEvaluationCap2",
      "researchWsEvaluationCap3",
    ],
  },
  timeline: {
    titleKey: "researchWsTimelineTitle",
    summaryKey: "researchWsTimelineSummary",
    capabilityKeys: [
      "researchWsTimelineCap1",
      "researchWsTimelineCap2",
      "researchWsTimelineCap3",
    ],
  },
  files: {
    titleKey: "researchWsFilesTitle",
    summaryKey: "researchWsFilesSummary",
    capabilityKeys: [
      "researchWsFilesCap1",
      "researchWsFilesCap2",
      "researchWsFilesCap3",
    ],
  },
  settings: {
    titleKey: "researchWsSettingsTitle",
    summaryKey: "researchWsSettingsSummary",
    capabilityKeys: [
      "researchWsSettingsCap1",
      "researchWsSettingsCap2",
      "researchWsSettingsCap3",
    ],
  },
};

export type ResearchWorkspacePageProps = {
  researchId: string;
};

/**
 * Research Workspace Detail（PR-003）。
 * TODO(backend): 用 getResearch(id) 替换 loadMockResearchById。
 */
export default function ResearchWorkspacePage({
  researchId,
}: ResearchWorkspacePageProps) {
  const { language, setLanguage, tr } = useWorkspaceLanguage();
  const searchParams = useSearchParams();
  const sectionParam = searchParams.get("section");
  const activeSection: ResearchWorkspaceSection = isResearchWorkspaceSection(
    sectionParam
  )
    ? sectionParam
    : "overview";

  const [research, setResearch] = useState<ResearchDetail | null>(null);
  const [loadStatus, setLoadStatus] = useState<LoadStatus>("loading");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const loadDetail = useCallback(async () => {
    setLoadStatus("loading");
    setLoadError(null);
    try {
      const data = await loadMockResearchById(researchId);
      if (!data) {
        setResearch(null);
        setLoadStatus("not_found");
        return;
      }
      setResearch(data);
      setLoadStatus("ready");
    } catch (error) {
      const message =
        error instanceof MockResearchError
          ? error.message
          : "The research workspace could not be loaded. Please retry.";
      setResearch(null);
      setLoadError(message);
      setLoadStatus("error");
    }
  }, [researchId]);

  useEffect(() => {
    void loadDetail();
  }, [loadDetail, reloadToken]);

  const navLabels = useMemo(
    () => ({
      overview: tr("researchWsNavOverview"),
      notebook: tr("researchWsNavNotebook"),
      experiments: tr("researchWsNavExperiments"),
      validation: tr("researchWsNavValidation"),
      evaluation: tr("researchWsNavEvaluation"),
      timeline: tr("researchWsNavTimeline"),
      files: tr("researchWsNavFiles"),
      settings: tr("researchWsNavSettings"),
    }),
    [tr]
  );

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <SectionCard>
        {loadStatus === "loading" ? (
          <div className="research-workspace-loading">
            <LoadingState message={tr("researchWsLoading")} />
            <ResearchWorkspaceSkeleton />
          </div>
        ) : null}

        {loadStatus === "error" && loadError ? (
          <div className="research-workspace-error">
            <ErrorAlert title={tr("researchWsErrorTitle")} message={loadError} />
            <Button primary onClick={() => setReloadToken((token) => token + 1)}>
              {tr("researchWsRetry")}
            </Button>
          </div>
        ) : null}

        {loadStatus === "not_found" ? (
          <EmptyState
            title={tr("researchWsNotFoundTitle")}
            description={tr("researchWsNotFoundDescription")}
            action={
              <Link href="/" className="btn btn--primary">
                {tr("researchWsBackToList")}
              </Link>
            }
          />
        ) : null}

        {loadStatus === "ready" && research ? (
          <div className="research-workspace">
            <ResearchWorkspaceHeader
              research={research}
              language={language}
              labels={{
                back: tr("researchWsBackToList"),
                moreActions: tr("researchWsMoreActions"),
                moreActionsHint: tr("researchWsMoreActionsHint"),
                owner: tr("researchListOwner"),
                created: tr("researchWsCreated"),
                updated: tr("researchListUpdated"),
                recommendation: tr("researchListRecommendation"),
                confidence: tr("researchListConfidence"),
                tags: tr("researchWsTags"),
              }}
            />

            <ResearchWorkspaceNavigation
              researchId={research.id}
              activeSection={activeSection}
              labels={navLabels}
            />

            <div className="research-workspace__layout">
              <div className="research-workspace__main">
                {activeSection === "overview" ? (
                  <OverviewSection
                    research={research}
                    labels={{
                      researchQuestion: tr("researchWsQuestion"),
                      hypothesis: tr("researchWsHypothesis"),
                      researchObjective: tr("researchWsObjective"),
                      currentStage: tr("researchWsCurrentStage"),
                      researchConfidence: tr("researchWsConfidence"),
                      currentRecommendation: tr("researchListRecommendation"),
                      researchSummary: tr("researchWsSummary"),
                      evidenceNarrative: tr("researchWsEvidenceNarrative"),
                      validationSummary: tr("researchWsValidationSummary"),
                      keyStrengths: tr("researchWsKeyStrengths"),
                      knownWeaknesses: tr("researchWsKnownWeaknesses"),
                      openQuestions: tr("researchWsOpenQuestions"),
                      nextActions: tr("researchWsNextActions"),
                      lifecycleTitle: tr("researchWsLifecycleTitle"),
                      lifecycleDescription: tr("researchWsLifecycleDescription"),
                      evidenceTitle: tr("researchWsEvidenceTitle"),
                      evidenceDescription: tr("researchWsEvidenceDescription"),
                      confidence: tr("researchListConfidence"),
                    }}
                  />
                ) : (
                  <WorkspacePlaceholder
                    title={tr(PLACEHOLDER_COPY[activeSection].titleKey)}
                    summary={tr(PLACEHOLDER_COPY[activeSection].summaryKey)}
                    plannedCapabilities={PLACEHOLDER_COPY[
                      activeSection
                    ].capabilityKeys.map((key) => tr(key))}
                    deferredNote={tr("researchWsDeferredNote")}
                  />
                )}

                {activeSection !== "overview" ? (
                  <div className="research-workspace__placeholder-evidence">
                    <EvidenceSummary
                      items={research.evidenceItems.slice(0, 3)}
                      title={tr("researchWsEvidencePreviewTitle")}
                      description={tr("researchWsEvidencePreviewDescription")}
                    />
                  </div>
                ) : null}
              </div>

              <ResearchActionPanel
                labels={{
                  title: tr("researchWsActionsTitle"),
                  description: tr("researchWsActionsDescription"),
                  addNotebook: tr("researchWsActionNotebook"),
                  createExperiment: tr("researchWsActionExperiment"),
                  runValidation: tr("researchWsActionValidation"),
                  requestEvaluation: tr("researchWsActionEvaluation"),
                  exportResearch: tr("researchWsActionExport"),
                  comingLater: tr("researchWsComingLater"),
                }}
              />
            </div>
          </div>
        ) : null}
      </SectionCard>
    </AppShell>
  );
}
