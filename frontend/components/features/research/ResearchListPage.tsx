"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import AppShell from "@/components/layout/AppShell";
import NewResearchModal from "@/components/features/research/NewResearchModal";
import ResearchGlyph from "@/components/features/research/ResearchGlyph";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import ErrorAlert from "@/components/ui/ErrorAlert";
import LoadingState from "@/components/ui/LoadingState";
import SectionCard from "@/components/ui/SectionCard";
import StatusBadge, { researchLifecycleVariant } from "@/components/ui/StatusBadge";
import { getResearchRepository } from "@/lib/localResearchRepository";
import type { CreateResearchInput } from "@/lib/researchRepository";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";
import type { ResearchListItem } from "@/types/research";
import { useResearchExecution } from "@/components/features/research/execution/useResearchExecution";
import { applyExecutionToListItem } from "@/lib/applyResearchExecution";
import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";
import {
  researchNameLabel,
  researchStatusLabel,
} from "@/lib/researchDisplay";
import {
  getCurrentLibraryStage,
  getLibraryRecentActivity,
  selectContinueResearch,
  type LibraryLifecycleStageId,
} from "@/lib/researchLibrary";
import type { Language } from "@/lib/i18n";

type LoadStatus = "loading" | "ready" | "error";

function formatUpdatedAt(value: string, language: Language): string | null {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleDateString(language === "zh" ? "zh-CN" : "en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/**
 * Research Library — workspace homepage for research projects.
 * Reuses existing repository research only; never fabricates projects or activity.
 */
export default function ResearchListPage() {
  const { language, setLanguage, tr } = useWorkspaceLanguage();
  const router = useRouter();
  const repository = useMemo(() => getResearchRepository(), []);
  const [items, setItems] = useState<ResearchListItem[]>([]);
  const [loadStatus, setLoadStatus] = useState<LoadStatus>("loading");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);
  const [actionNotice, setActionNotice] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const { status: executionStatus, execution } = useResearchExecution(
    CANONICAL_RESEARCH_ID
  );

  const loadList = useCallback(async () => {
    setLoadStatus("loading");
    setLoadError(null);
    try {
      const data = await repository.list();
      setItems(data);
      setLoadStatus("ready");
    } catch {
      setItems([]);
      setLoadError("The research list could not be loaded. Please retry.");
      setLoadStatus("error");
    }
  }, [repository]);

  useEffect(() => {
    void loadList();
  }, [loadList, reloadToken]);

  const displayedItems = useMemo(() => {
    // Hide archived research from the landing (continue, projects, empty state).
    const visible = items.filter((item) => item.status !== "Archived");
    if (executionStatus !== "ready" || !execution) {
      return visible;
    }
    return visible.map((item) =>
      item.id === CANONICAL_RESEARCH_ID
        ? applyExecutionToListItem(item, execution)
        : item
    );
  }, [items, executionStatus, execution]);

  const continueResearch = useMemo(
    () => selectContinueResearch(displayedItems),
    [displayedItems]
  );

  const recentActivity = useMemo(
    () => getLibraryRecentActivity(continueResearch?.id ?? null),
    [continueResearch]
  );

  const stageLabels: Record<LibraryLifecycleStageId, string> = {
    research: tr("researchLibraryStageResearch"),
    experiment: tr("researchLibraryStageExperiment"),
    validation: tr("researchLibraryStageValidation"),
    robustness: tr("researchLibraryStageRobustness"),
    paper: tr("researchLibraryStagePaper"),
    decision: tr("researchLibraryStageDecision"),
    archive: tr("researchLibraryStageArchive"),
  };

  function handleRetry() {
    setReloadToken((token) => token + 1);
  }

  function handleNewResearch() {
    setActionNotice(null);
    setModalOpen(true);
  }

  async function handleCreateResearch(input: CreateResearchInput) {
    setCreating(true);
    try {
      const created = await repository.create(input);
      setModalOpen(false);
      setActionNotice(tr("researchListCreated"));
      router.push(`/research/${encodeURIComponent(created.id)}`);
    } catch (error) {
      setActionNotice(
        error instanceof Error ? error.message : tr("researchListCreateFailed")
      );
    } finally {
      setCreating(false);
    }
  }

  async function handleLoadDemo() {
    await repository.includeDemoResearch();
    setActionNotice(tr("researchListDemoLoaded"));
    setReloadToken((token) => token + 1);
  }

  const isCatalogEmpty = loadStatus === "ready" && displayedItems.length === 0;

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <SectionCard>
        <header className="research-library__header">
          <div>
            <p className="research-library__eyebrow">
              {tr("researchLibraryEyebrow")}
            </p>
            <h1 className="research-library__title">
              {tr("researchLibraryTitle")}
            </h1>
            <p className="research-library__subtitle">
              {tr("researchLibrarySubtitle")}
            </p>
          </div>
        </header>

        {actionNotice ? <p className="section-meta">{actionNotice}</p> : null}

        {loadStatus === "loading" ? (
          <div className="research-library__loading" aria-busy="true">
            <LoadingState message={tr("researchListLoading")} />
          </div>
        ) : null}

        {loadStatus === "error" && loadError ? (
          <div className="research-library__error research-library__fade-in">
            <ErrorAlert
              title={tr("researchListErrorTitle")}
              message={loadError}
            />
            <Button primary onClick={handleRetry}>
              {tr("researchListRetry")}
            </Button>
          </div>
        ) : null}

        {loadStatus === "ready" ? (
          <div className="research-library research-library__fade-in">
            {/* 1. Continue Research */}
            <section
              className="research-library__band"
              aria-label={tr("researchLibraryContinueTitle")}
            >
              <p className="overview-caption">
                <ResearchGlyph name="action" />
                <span>{tr("researchLibraryContinueTitle")}</span>
              </p>
              {continueResearch ? (
                <div className="research-library__continue">
                  <div className="research-library__continue-copy">
                    <h2 className="research-library__continue-name">
                      {researchNameLabel(
                        continueResearch.id,
                        continueResearch.name,
                        language
                      )}
                    </h2>
                    <p className="research-library__continue-meta">
                      {tr("researchLibraryCurrentStage")}:{" "}
                      {
                        stageLabels[
                          getCurrentLibraryStage(continueResearch.status)
                        ]
                      }
                    </p>
                    {formatUpdatedAt(continueResearch.updatedAt, language) ? (
                      <p className="research-library__continue-meta">
                        {tr("researchLibraryLastUpdated")}:{" "}
                        {formatUpdatedAt(continueResearch.updatedAt, language)}
                      </p>
                    ) : null}
                  </div>
                  <Link
                    href={`/research/${encodeURIComponent(continueResearch.id)}`}
                    className="btn btn--primary"
                  >
                    {tr("researchLibraryContinueButton")}
                  </Link>
                </div>
              ) : (
                <EmptyState description={tr("researchLibraryContinueEmpty")} />
              )}
            </section>

            <hr className="overview-divider" />

            {/* 2. Research Projects */}
            <section
              id="research-library-projects"
              className="research-library__band"
              aria-label={tr("researchLibraryProjectsTitle")}
            >
              <p className="overview-caption">
                <ResearchGlyph name="progress" />
                <span>{tr("researchLibraryProjectsTitle")}</span>
              </p>

              {isCatalogEmpty ? (
                <EmptyState
                  title={tr("researchLibraryEmptyTitle")}
                  description={tr("researchLibraryEmptyDescription")}
                  action={
                    <div className="research-list-empty-actions">
                      <Button primary onClick={handleNewResearch}>
                        {tr("researchListCreateResearch")}
                      </Button>
                      <Button onClick={() => void handleLoadDemo()}>
                        {tr("researchListLoadDemo")}
                      </Button>
                    </div>
                  }
                />
              ) : (
                <ul className="research-library__project-list">
                  {displayedItems.map((item) => {
                    const stage = getCurrentLibraryStage(item.status);
                    return (
                      <li key={item.id}>
                        <Link
                          href={`/research/${encodeURIComponent(item.id)}`}
                          className="research-library__project-card"
                        >
                          <div className="research-library__project-main">
                            <h3 className="research-library__project-title">
                              {researchNameLabel(item.id, item.name, language)}
                            </h3>
                            {item.configuration.strategyName &&
                            item.configuration.strategyName !== "Not configured" &&
                            item.configuration.strategyName !== "未配置" ? (
                              <p className="research-library__project-strategy">
                                {item.configuration.strategyName}
                              </p>
                            ) : null}
                            <p className="research-library__project-stage">
                              {tr("researchLibraryCurrentStage")}:{" "}
                              {stageLabels[stage]}
                            </p>
                          </div>
                          <StatusBadge
                            label={researchStatusLabel(item.status, language)}
                            variant={researchLifecycleVariant(item.status)}
                          />
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              )}
            </section>

            <hr className="overview-divider" />

            {/* 4. Recent Activity */}
            <section
              className="research-library__band"
              aria-label={tr("researchLibraryActivityTitle")}
            >
              <p className="overview-caption">
                <ResearchGlyph name="evidence" />
                <span>{tr("researchLibraryActivityTitle")}</span>
              </p>
              {recentActivity.length === 0 ? (
                <EmptyState description={tr("researchLibraryActivityEmpty")} />
              ) : (
                <ul className="research-library__activity">
                  {recentActivity.map((event) => (
                    <li key={event.id} className="research-library__activity-row">
                      <span className="research-library__activity-title">
                        {event.title}
                      </span>
                      <span className="research-library__activity-summary">
                        {event.summary}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <hr className="overview-divider" />

            {/* 5. Quick Actions */}
            <section
              className="research-library__band research-library__band--actions"
              aria-label={tr("researchLibraryActionsTitle")}
            >
              <p className="overview-caption">
                <ResearchGlyph name="action" />
                <span>{tr("researchLibraryActionsTitle")}</span>
              </p>
              <ul className="research-library__actions">
                <li>
                  <button
                    type="button"
                    className="research-library__action"
                    onClick={handleNewResearch}
                  >
                    {tr("researchLibraryActionNew")}
                  </button>
                </li>
                <li>
                  <Link href="/comparison" className="research-library__action">
                    {tr("researchLibraryActionCompare")}
                  </Link>
                </li>
                <li>
                  <Link href="/strategy-lab" className="research-library__action">
                    {tr("researchLibraryActionStrategyLab")}
                  </Link>
                </li>
                <li>
                  <Link
                    href={
                      continueResearch
                        ? `/research/${encodeURIComponent(continueResearch.id)}?tab=robustness`
                        : "/"
                    }
                    className="research-library__action"
                  >
                    {tr("researchLibraryActionRobustness")}
                  </Link>
                </li>
                <li>
                  <Link
                    href={
                      continueResearch
                        ? `/research/${encodeURIComponent(continueResearch.id)}?tab=paper`
                        : "/"
                    }
                    className="research-library__action"
                  >
                    {tr("researchLibraryActionPaper")}
                  </Link>
                </li>
              </ul>
            </section>
          </div>
        ) : null}
      </SectionCard>

      <NewResearchModal
        open={modalOpen}
        busy={creating}
        onClose={() => setModalOpen(false)}
        onCreate={handleCreateResearch}
        labels={{
          title: tr("researchListNewResearch"),
          localNote: tr("researchListModalLocalNote"),
          name: tr("researchListModalName"),
          question: tr("researchListModalQuestion"),
          hypothesis: tr("researchListModalHypothesis"),
          tags: tr("researchWsTags"),
          tagsHint: tr("researchListModalTagsHint"),
          create: tr("researchListModalCreate"),
          cancel: tr("researchListModalCancel"),
          errorName: tr("researchListModalNameRequired"),
          errorQuestion: tr("researchListModalQuestionRequired"),
          errorHypothesis: tr("researchListModalHypothesisRequired"),
        }}
      />
    </AppShell>
  );
}
