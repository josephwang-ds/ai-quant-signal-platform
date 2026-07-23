"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import AppShell from "@/components/layout/AppShell";
import PageHero from "@/components/layout/PageHero";
import NewResearchModal from "@/components/features/research/NewResearchModal";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import ErrorAlert from "@/components/ui/ErrorAlert";
import LoadingState from "@/components/ui/LoadingState";
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
  getLibraryProgressRatio,
  getLibraryRecentActivityForResearchIds,
  getOverviewWorkflowProgress,
  getWorkspaceOverviewStats,
  overviewWorkflowTab,
  selectContinueResearch,
  type LibraryLifecycleStageId,
  type OverviewWorkflowStageId,
  OVERVIEW_WORKFLOW_STAGES,
} from "@/lib/researchLibrary";
import type { Language } from "@/lib/i18n";
import type { ResearchTimelineEventKind } from "@/types/notebook";

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

function formatOccurredAt(value: string, language: Language): string | null {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleString(language === "zh" ? "zh-CN" : "en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Research Library — workspace homepage operating overview.
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

  const stats = useMemo(
    () => getWorkspaceOverviewStats(displayedItems),
    [displayedItems]
  );

  const recentActivity = useMemo(
    () =>
      getLibraryRecentActivityForResearchIds(
        displayedItems.map((item) => item.id)
      ).slice(0, 8),
    [displayedItems]
  );

  const workflowProgress = useMemo(
    () =>
      continueResearch
        ? getOverviewWorkflowProgress(continueResearch.status)
        : { completed: [] as OverviewWorkflowStageId[], current: null },
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

  const workflowLabels: Record<OverviewWorkflowStageId, string> = {
    research: tr("researchOverviewWorkflowResearch"),
    validation: tr("researchOverviewWorkflowValidation"),
    risk_review: tr("researchOverviewWorkflowRiskReview"),
    deployment: tr("researchOverviewWorkflowDeployment"),
  };

  const activityKindLabel = (kind: ResearchTimelineEventKind): string => {
    switch (kind) {
      case "validation":
        return tr("researchOverviewActivityKindValidation");
      case "experiment":
        return tr("researchOverviewActivityKindBacktest");
      case "stage_change":
        return tr("researchOverviewActivityKindStage");
      case "notebook_entry":
      default:
        return tr("researchOverviewActivityKindUpdate");
    }
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

  const continueHref = continueResearch
    ? `/research/${encodeURIComponent(continueResearch.id)}`
    : null;

  const heroCta = continueHref
    ? {
        label: tr("researchLibraryContinueButton"),
        href: continueHref,
      }
    : {
        label: tr("researchListCreateResearch"),
        onClick: handleNewResearch,
      };

  const aiSummary =
    continueResearch && continueHref
      ? tr("researchOverviewAiSummaryFocus")
          .replace(
            "{name}",
            researchNameLabel(
              continueResearch.id,
              continueResearch.name,
              language
            )
          )
          .replace(
            "{stage}",
            stageLabels[getCurrentLibraryStage(continueResearch.status)]
          )
          .replace("{count}", String(stats.active))
      : tr("researchOverviewAiSummaryEmpty");

  const aiAction = continueHref
    ? {
        label: tr("researchOverviewAiActionResume"),
        href: continueHref,
      }
    : {
        label: tr("researchListCreateResearch"),
        onClick: handleNewResearch,
      };

  function workflowHref(stage: OverviewWorkflowStageId): string {
    if (!continueResearch) {
      if (stage === "risk_review") return "/risk-gate-review";
      if (stage === "research") return "/strategy-lab";
      return "#research-library-projects";
    }
    const tab = overviewWorkflowTab(stage);
    return `/research/${encodeURIComponent(continueResearch.id)}?tab=${tab}`;
  }

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <div className="research-overview" data-testid="research-overview">
        <PageHero
          title={tr("researchOverviewHeroTitle")}
          sentence={tr("researchOverviewHeroSentence")}
          stats={
            loadStatus === "ready"
              ? [
                  {
                    label: tr("researchOverviewStatActive"),
                    value: stats.active,
                  },
                  {
                    label: tr("researchOverviewStatReview"),
                    value: stats.inReview,
                  },
                  {
                    label: tr("researchOverviewStatPaper"),
                    value: stats.paperTrading,
                  },
                  {
                    label: tr("researchOverviewStatExperiments"),
                    value: stats.experiments,
                  },
                ]
              : []
          }
          primaryCta={heroCta}
        />

        {actionNotice ? (
          <p className="research-overview__notice">{actionNotice}</p>
        ) : null}

        {loadStatus === "loading" ? (
          <div className="research-overview__loading" aria-busy="true">
            <LoadingState message={tr("researchListLoading")} />
          </div>
        ) : null}

        {loadStatus === "error" && loadError ? (
          <div className="research-overview__error">
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
          <>
            <div className="research-overview__priority-grid">
              {/* 2. Continue Research */}
              <section
                className="research-overview__section research-overview__section--focus"
                aria-labelledby="research-overview-continue"
              >
              <header className="research-overview__section-head">
                <h2 id="research-overview-continue">
                  {tr("researchLibraryContinueTitle")}
                </h2>
                <p>{tr("researchOverviewContinueHint")}</p>
              </header>

              {continueResearch && continueHref ? (
                <article className="research-overview__continue-card">
                  <div className="research-overview__continue-main">
                    <p className="research-overview__continue-kicker">
                      {tr("researchOverviewRecentWork")}
                    </p>
                    <h3 className="research-overview__continue-title">
                      {researchNameLabel(
                        continueResearch.id,
                        continueResearch.name,
                        language
                      )}
                    </h3>
                    <p className="research-overview__continue-subtitle">
                      {continueResearch.researchQuestion}
                    </p>
                    <div className="research-overview__continue-meta">
                      <StatusBadge
                        label={researchStatusLabel(
                          continueResearch.status,
                          language
                        )}
                        variant={researchLifecycleVariant(
                          continueResearch.status
                        )}
                      />
                      <span>
                        {tr("researchLibraryCurrentStage")}:{" "}
                        {
                          stageLabels[
                            getCurrentLibraryStage(continueResearch.status)
                          ]
                        }
                      </span>
                      {formatUpdatedAt(continueResearch.updatedAt, language) ? (
                        <span>
                          {tr("researchLibraryLastUpdated")}:{" "}
                          {formatUpdatedAt(
                            continueResearch.updatedAt,
                            language
                          )}
                        </span>
                      ) : null}
                    </div>
                    <div
                      className="research-overview__progress"
                      role="meter"
                      aria-valuenow={Math.round(
                        getLibraryProgressRatio(continueResearch.status) * 100
                      )}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-label={tr("researchOverviewProgressLabel")}
                    >
                      <span
                        style={{
                          width: `${Math.round(
                            getLibraryProgressRatio(continueResearch.status) *
                              100
                          )}%`,
                        }}
                      />
                    </div>
                  </div>
                  <Link href={continueHref} className="btn btn--primary">
                    {tr("researchOverviewResume")}
                  </Link>
                </article>
              ) : (
                <EmptyState description={tr("researchLibraryContinueEmpty")} />
              )}
              </section>

              {/* 3. Research Lifecycle */}
              <section
                className="research-overview__section research-overview__section--lifecycle"
                aria-labelledby="research-overview-lifecycle"
              >
              <header className="research-overview__section-head">
                <h2 id="research-overview-lifecycle">
                  {tr("researchLibraryLifecycleTitle")}
                </h2>
                <p>{tr("researchOverviewLifecycleHint")}</p>
              </header>

              <ol className="research-overview__workflow">
                {OVERVIEW_WORKFLOW_STAGES.map((stage, index) => {
                  const isCurrent = workflowProgress.current === stage;
                  const isDone = workflowProgress.completed.includes(stage);
                  return (
                    <li key={stage}>
                      <Link
                        href={workflowHref(stage)}
                        className={[
                          "research-overview__workflow-step",
                          isCurrent ? "is-current" : "",
                          isDone ? "is-done" : "",
                        ]
                          .filter(Boolean)
                          .join(" ")}
                      >
                        <span className="research-overview__workflow-index">
                          {index + 1}
                        </span>
                        <span className="research-overview__workflow-label">
                          {workflowLabels[stage]}
                        </span>
                      </Link>
                    </li>
                  );
                })}
              </ol>
              </section>
            </div>

            <div className="research-overview__operations-grid">
              {/* 4. Research Library */}
              <section
                id="research-library-projects"
                className="research-overview__section research-overview__section--library"
                aria-labelledby="research-overview-library"
              >
              <header className="research-overview__section-head research-overview__section-head--row">
                <div>
                  <h2 id="research-overview-library">
                    {tr("researchLibraryProjectsTitle")}
                  </h2>
                  <p>{tr("researchOverviewLibraryHint")}</p>
                </div>
                <Button onClick={handleNewResearch}>
                  {tr("researchLibraryActionNew")}
                </Button>
              </header>

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
                <ul className="research-overview__library">
                  {displayedItems.map((item) => {
                    const stage = getCurrentLibraryStage(item.status);
                    const ratio = getLibraryProgressRatio(item.status);
                    const pct = Math.round(ratio * 100);
                    const href = `/research/${encodeURIComponent(item.id)}`;
                    const strategy =
                      item.configuration.strategyName &&
                      item.configuration.strategyName !== "Not configured" &&
                      item.configuration.strategyName !== "未配置"
                        ? item.configuration.strategyName
                        : item.researchQuestion;
                    return (
                      <li key={item.id}>
                        <article className="research-overview__project-card">
                          <div className="research-overview__project-main">
                            <div className="research-overview__project-top">
                              <h3>
                                <Link href={href}>
                                  {researchNameLabel(
                                    item.id,
                                    item.name,
                                    language
                                  )}
                                </Link>
                              </h3>
                              <StatusBadge
                                label={researchStatusLabel(
                                  item.status,
                                  language
                                )}
                                variant={researchLifecycleVariant(item.status)}
                              />
                            </div>
                            <p className="research-overview__project-subtitle">
                              {strategy}
                            </p>
                            <div className="research-overview__project-meta">
                              <span>
                                {tr("researchLibraryCurrentStage")}:{" "}
                                {stageLabels[stage]}
                              </span>
                              {formatUpdatedAt(item.updatedAt, language) ? (
                                <span>
                                  {tr("researchLibraryLastUpdated")}:{" "}
                                  {formatUpdatedAt(item.updatedAt, language)}
                                </span>
                              ) : null}
                            </div>
                            <div
                              className="research-overview__progress"
                              role="meter"
                              aria-valuenow={pct}
                              aria-valuemin={0}
                              aria-valuemax={100}
                              aria-label={tr("researchOverviewProgressLabel")}
                            >
                              <span style={{ width: `${pct}%` }} />
                            </div>
                          </div>
                          <Link href={href} className="btn">
                            {tr("researchOverviewOpen")}
                          </Link>
                        </article>
                      </li>
                    );
                  })}
                </ul>
              )}
              </section>

              {/* 5. Recent Activity */}
              <section
                className="research-overview__section research-overview__section--activity"
                aria-labelledby="research-overview-activity"
              >
              <header className="research-overview__section-head">
                <h2 id="research-overview-activity">
                  {tr("researchLibraryActivityTitle")}
                </h2>
                <p>{tr("researchOverviewActivityHint")}</p>
              </header>

              {recentActivity.length === 0 ? (
                <EmptyState description={tr("researchLibraryActivityEmpty")} />
              ) : (
                <ol className="research-overview__timeline">
                  {recentActivity.map((event) => (
                    <li key={event.id}>
                      <div className="research-overview__timeline-rail" aria-hidden />
                      <div className="research-overview__timeline-body">
                        <div className="research-overview__timeline-meta">
                          <span className="research-overview__timeline-kind">
                            {activityKindLabel(event.kind)}
                          </span>
                          {formatOccurredAt(event.occurredAt, language) ? (
                            <time dateTime={event.occurredAt}>
                              {formatOccurredAt(event.occurredAt, language)}
                            </time>
                          ) : null}
                        </div>
                        <p className="research-overview__timeline-title">
                          {event.title}
                        </p>
                        <p className="research-overview__timeline-summary">
                          {event.summary}
                        </p>
                      </div>
                    </li>
                  ))}
                </ol>
              )}
              </section>
            </div>

            {/* 6. AI Daily Summary */}
            <section
              className="research-overview__section research-overview__section--ai"
              aria-labelledby="research-overview-ai"
              data-testid="research-overview-ai-summary"
            >
              <header className="research-overview__section-head">
                <h2 id="research-overview-ai">
                  {tr("researchOverviewAiTitle")}
                </h2>
              </header>
              <div className="research-overview__ai-panel">
                <p>{aiSummary}</p>
                {"href" in aiAction && aiAction.href ? (
                  <Link href={aiAction.href} className="btn">
                    {aiAction.label}
                  </Link>
                ) : (
                  <Button onClick={aiAction.onClick}>{aiAction.label}</Button>
                )}
              </div>
            </section>
          </>
        ) : null}
      </div>

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
