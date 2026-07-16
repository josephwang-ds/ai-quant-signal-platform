"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import AppShell from "@/components/layout/AppShell";
import NewResearchModal from "@/components/features/research/NewResearchModal";
import ResearchCard from "@/components/features/research/ResearchCard";
import ResearchListSkeleton from "@/components/features/research/ResearchListSkeleton";
import ResearchWorkspaceSummary from "@/components/features/research/ResearchWorkspaceSummary";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import ErrorAlert from "@/components/ui/ErrorAlert";
import LoadingState from "@/components/ui/LoadingState";
import SectionCard from "@/components/ui/SectionCard";
import { getResearchRepository } from "@/lib/localResearchRepository";
import type { CreateResearchInput } from "@/lib/researchRepository";
import {
  DEFAULT_RESEARCH_LIST_FILTERS,
  filterAndSortResearchList,
  getUniqueResearchOwners,
  getUniqueResearchTags,
  type ResearchListFilters,
} from "@/lib/researchListFilters";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";
import {
  RESEARCH_LIFECYCLE_STATUSES,
  type ResearchListItem,
} from "@/types/research";
import { useResearchExecution } from "@/components/features/research/execution/useResearchExecution";
import { applyExecutionToListItem } from "@/lib/applyResearchExecution";
import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";
import { ownerLabel, researchStatusLabel } from "@/lib/researchDisplay";

type LoadStatus = "loading" | "ready" | "error";

function filtersAreActive(filters: ResearchListFilters): boolean {
  return (
    filters.query.trim() !== "" ||
    filters.status !== "all" ||
    filters.owner !== "all" ||
    filters.tag !== "all"
  );
}

/**
 * Research Workspace home — Research-first list (Sprint 1 IA).
 * Persistence: ResearchRepository → LocalResearchRepository (localStorage).
 */
export default function ResearchListPage() {
  const { language, setLanguage, tr } = useWorkspaceLanguage();
  const router = useRouter();
  const repository = useMemo(() => getResearchRepository(), []);
  const [items, setItems] = useState<ResearchListItem[]>([]);
  const [summary, setSummary] = useState({
    total: 0,
    defined: 0,
    evidenceAvailable: 0,
    reviewOrArchived: 0,
  });
  const [filters, setFilters] = useState<ResearchListFilters>(
    DEFAULT_RESEARCH_LIST_FILTERS
  );
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
      const [data, nextSummary] = await Promise.all([
        repository.list(),
        repository.getSummary(),
      ]);
      setItems(data);
      setSummary(nextSummary);
      setLoadStatus("ready");
    } catch {
      setItems([]);
      setSummary({
        total: 0,
        defined: 0,
        evidenceAvailable: 0,
        reviewOrArchived: 0,
      });
      setLoadError("The research list could not be loaded. Please retry.");
      setLoadStatus("error");
    }
  }, [repository]);

  useEffect(() => {
    void loadList();
  }, [loadList, reloadToken]);

  const owners = useMemo(() => getUniqueResearchOwners(items), [items]);
  const tags = useMemo(() => getUniqueResearchTags(items), [items]);
  const displayedItems = useMemo(() => {
    if (executionStatus !== "ready" || !execution) {
      return items;
    }
    return items.map((item) =>
      item.id === CANONICAL_RESEARCH_ID
        ? applyExecutionToListItem(item, execution)
        : item
    );
  }, [items, executionStatus, execution]);
  const visible = useMemo(
    () => filterAndSortResearchList(displayedItems, filters),
    [displayedItems, filters]
  );

  function updateFilter<K extends keyof ResearchListFilters>(
    key: K,
    value: ResearchListFilters[K]
  ) {
    setFilters((prev) => ({ ...prev, [key]: value }));
  }

  function handleRetry() {
    setReloadToken((token) => token + 1);
  }

  function handleClearFilters() {
    setFilters(DEFAULT_RESEARCH_LIST_FILTERS);
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

  async function handleArchive(id: string) {
    await repository.archive(id);
    setActionNotice(tr("researchListArchived"));
    setReloadToken((token) => token + 1);
  }

  async function handleLoadDemo() {
    await repository.includeDemoResearch();
    setActionNotice(tr("researchListDemoLoaded"));
    setReloadToken((token) => token + 1);
  }

  const cardLabels = {
    openWorkspace: tr("researchListOpenWorkspace"),
    archive: tr("researchListArchive"),
    experiments: tr("researchListExperimentCount"),
    updated: tr("researchListUpdated"),
    symbol: tr("researchListSymbol"),
    strategy: tr("researchListStrategy"),
    evidenceStatus: tr("researchListEvidenceStatus"),
    more: tr("researchListMore"),
  };

  const showToolbar = loadStatus !== "error";
  const isFilterEmpty =
    loadStatus === "ready" && visible.length === 0 && filtersAreActive(filters);
  const isCatalogEmpty =
    loadStatus === "ready" && items.length === 0 && !filtersAreActive(filters);

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <SectionCard>
        <header className="research-list-header">
          <div className="research-list-header__copy">
            <p className="research-list-header__eyebrow">
              {tr("researchListEyebrow")}
            </p>
            <h1 className="research-list-header__title">
              {tr("researchListTitle")}
            </h1>
            <p className="research-list-header__subtitle">
              {tr("researchListSubtitle")}
            </p>
          </div>
          <Button
            primary
            onClick={handleNewResearch}
            disabled={loadStatus === "loading"}
          >
            {tr("researchListNewResearch")}
          </Button>
        </header>

        {loadStatus === "ready" || loadStatus === "loading" ? (
          <ResearchWorkspaceSummary
            total={summary.total}
            defined={summary.defined}
            evidenceAvailable={summary.evidenceAvailable}
            reviewOrArchived={summary.reviewOrArchived}
            labels={{
              research: tr("researchListKpiResearch"),
              ariaLabel: tr("researchListSummaryAria"),
              defined: tr("researchListKpiDefined"),
              evidenceAvailable: tr("researchListKpiEvidenceAvailable"),
              reviewOrArchived: tr("researchListKpiReviewArchived"),
            }}
          />
        ) : null}

        {showToolbar ? (
          <div className="research-list-toolbar" role="search">
            <div className="form-field research-list-toolbar__search">
              <label className="form-label" htmlFor="research-search">
                {tr("researchListSearch")}
              </label>
              <input
                id="research-search"
                className="form-input"
                type="search"
                value={filters.query}
                placeholder={tr("researchListSearchPlaceholder")}
                onChange={(event) => updateFilter("query", event.target.value)}
                disabled={loadStatus === "loading"}
              />
            </div>

            <div className="form-field">
              <label className="form-label" htmlFor="research-status">
                {tr("researchListFilterStatus")}
              </label>
              <select
                id="research-status"
                className="form-select"
                value={filters.status}
                disabled={loadStatus === "loading"}
                onChange={(event) =>
                  updateFilter(
                    "status",
                    event.target.value as ResearchListFilters["status"]
                  )
                }
              >
                <option value="all">{tr("researchListFilterAll")}</option>
                {RESEARCH_LIFECYCLE_STATUSES.map((status) => (
                  <option key={status} value={status}>
                    {researchStatusLabel(status, language)}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-field">
              <label className="form-label" htmlFor="research-owner">
                {tr("researchListFilterOwner")}
              </label>
              <select
                id="research-owner"
                className="form-select"
                value={filters.owner}
                disabled={loadStatus === "loading" || owners.length === 0}
                onChange={(event) => updateFilter("owner", event.target.value)}
              >
                <option value="all">{tr("researchListFilterAll")}</option>
                {owners.map((owner) => (
                  <option key={owner} value={owner}>
                    {ownerLabel(owner, language)}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-field">
              <label className="form-label" htmlFor="research-tag">
                {tr("researchListFilterTag")}
              </label>
              <select
                id="research-tag"
                className="form-select"
                value={filters.tag}
                disabled={loadStatus === "loading" || tags.length === 0}
                onChange={(event) => updateFilter("tag", event.target.value)}
              >
                <option value="all">{tr("researchListFilterAll")}</option>
                {tags.map((tag) => (
                  <option key={tag} value={tag}>
                    {tag}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-field">
              <label className="form-label" htmlFor="research-sort">
                {tr("researchListSort")}
              </label>
              <select
                id="research-sort"
                className="form-select"
                value={filters.sort}
                disabled={loadStatus === "loading"}
                onChange={(event) =>
                  updateFilter(
                    "sort",
                    event.target.value as ResearchListFilters["sort"]
                  )
                }
              >
                <option value="updated">{tr("researchListSortUpdated")}</option>
                <option value="created">{tr("researchListSortCreated")}</option>
                <option value="name">{tr("researchListSortName")}</option>
                <option value="confidence">
                  {tr("researchListSortConfidence")}
                </option>
              </select>
            </div>
          </div>
        ) : null}

        {actionNotice ? <p className="section-meta">{actionNotice}</p> : null}

        <div
          className="research-list-body"
          aria-busy={loadStatus === "loading"}
          aria-live="polite"
        >
          {loadStatus === "loading" ? (
            <div className="research-list-loading">
              <LoadingState message={tr("researchListLoading")} />
              <ResearchListSkeleton />
            </div>
          ) : null}

          {loadStatus === "error" && loadError ? (
            <div className="research-list-error">
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
              <p className="research-list-count section-meta">
                {visible.length} {tr("researchListResultCount")}
              </p>

              {isFilterEmpty ? (
                <EmptyState
                  title={tr("researchListEmptyFilterTitle")}
                  description={tr("researchListEmptyFilterDescription")}
                  action={
                    <Button onClick={handleClearFilters}>
                      {tr("researchListClearFilters")}
                    </Button>
                  }
                />
              ) : null}

              {isCatalogEmpty ? (
                <EmptyState
                  title={tr("researchListEmptyTitle")}
                  description={tr("researchListEmptyDescription")}
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
              ) : null}

              {visible.length > 0 ? (
                <div className="research-list-grid">
                  {visible.map((item) => (
                    <ResearchCard
                      key={item.id}
                      item={item}
                      language={language}
                      labels={cardLabels}
                      onArchive={(id) => void handleArchive(id)}
                    />
                  ))}
                </div>
              ) : null}
            </>
          ) : null}
        </div>
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
          symbol: tr("researchListSymbol"),
          startDate: tr("researchExpComposerStart"),
          endDate: tr("researchExpComposerEnd"),
          shortWindow: tr("researchValShortWindow"),
          longWindow: tr("researchValLongWindow"),
          transactionCost: tr("researchValTransactionCost"),
          tags: tr("researchWsTags"),
          tagsHint: tr("researchListModalTagsHint"),
          owner: tr("researchListOwner"),
          create: tr("researchListModalCreate"),
          cancel: tr("researchListModalCancel"),
          errorName: tr("researchListModalNameRequired"),
          errorQuestion: tr("researchListModalQuestionRequired"),
          errorSymbol: tr("researchListModalSymbolRequired"),
          errorShortWindow: tr("researchListModalShortInvalid"),
          errorLongWindow: tr("researchListModalLongInvalid"),
          errorDateRange: tr("researchListModalDateInvalid"),
          errorTransactionCost: tr("researchListModalCostInvalid"),
        }}
      />
    </AppShell>
  );
}
