"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import ResearchCard from "@/components/features/research/ResearchCard";
import ResearchListSkeleton from "@/components/features/research/ResearchListSkeleton";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import ErrorAlert from "@/components/ui/ErrorAlert";
import LoadingState from "@/components/ui/LoadingState";
import SectionCard from "@/components/ui/SectionCard";
import {
  loadMockResearchProjects,
  MockResearchListError,
} from "@/lib/mockResearchList";
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
 * Research Workspace 首页：研究项目列表（PR-002 / Story 2.1）。
 *
 * TODO(backend): 用 listResearch() 替换 loadMockResearchProjects()。
 * TODO(api): New Research → CreateResearch 命令。
 * TODO(database): 本页不引入持久化。
 */
export default function ResearchListPage() {
  const { language, setLanguage, tr } = useWorkspaceLanguage();
  const [items, setItems] = useState<ResearchListItem[]>([]);
  const [filters, setFilters] = useState<ResearchListFilters>(DEFAULT_RESEARCH_LIST_FILTERS);
  const [loadStatus, setLoadStatus] = useState<LoadStatus>("loading");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  const loadList = useCallback(async () => {
    setLoadStatus("loading");
    setLoadError(null);
    setActionNotice(null);
    try {
      const data = await loadMockResearchProjects();
      setItems(data);
      setLoadStatus("ready");
    } catch (error) {
      const message =
        error instanceof MockResearchListError
          ? error.message
          : "The research list could not be loaded. Please retry.";
      setItems([]);
      setLoadError(message);
      setLoadStatus("error");
    }
  }, []);

  useEffect(() => {
    void loadList();
  }, [loadList, reloadToken]);

  const owners = useMemo(() => getUniqueResearchOwners(items), [items]);
  const tags = useMemo(() => getUniqueResearchTags(items), [items]);
  const visible = useMemo(
    () => filterAndSortResearchList(items, filters),
    [items, filters]
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
    // TODO(api): POST /api/research（CreateResearch）
    setActionNotice(tr("researchListNewResearchTodo"));
  }

  function handleDuplicate(id: string) {
    // TODO(api): POST /api/research/{id}/duplicate
    const source = items.find((item) => item.id === id);
    if (!source) {
      return;
    }
    const now = new Date().toISOString();
    const copy: ResearchListItem = {
      ...source,
      id: `${source.id}-copy-${Date.now()}`,
      name: `${source.name} (Copy)`,
      status: "Draft",
      confidenceScore: null,
      createdAt: now,
      updatedAt: now,
      experimentCount: 0,
      lastValidation: "No formal validation yet",
      currentRecommendation: "Refine scope before first experiment",
      tags: [...source.tags],
    };
    setItems((prev) => [copy, ...prev]);
    setActionNotice(tr("researchListDuplicated"));
  }

  function handleArchive(id: string) {
    // TODO(api): POST /api/research/{id}/archive
    setItems((prev) =>
      prev.map((item) =>
        item.id === id
          ? {
              ...item,
              status: "Archived",
              updatedAt: new Date().toISOString(),
              currentRecommendation: "Archived from Research List",
            }
          : item
      )
    );
    setActionNotice(tr("researchListArchived"));
  }

  function handleMore(id: string) {
    // TODO(product): 更多操作菜单（rename / export / share）
    setActionNotice(`${tr("researchListMoreTodo")} (${id})`);
  }

  const cardLabels = {
    openWorkspace: tr("researchListOpenWorkspace"),
    duplicate: tr("researchListDuplicate"),
    archive: tr("researchListArchive"),
    more: tr("researchListMore"),
    experiments: tr("researchListExperimentCount"),
    lastValidation: tr("researchListLastValidation"),
    recommendation: tr("researchListRecommendation"),
    updated: tr("researchListUpdated"),
    owner: tr("researchListOwner"),
    confidence: tr("researchListConfidence"),
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
            <p className="research-list-header__eyebrow">{tr("researchListEyebrow")}</p>
            <h1 className="research-list-header__title">{tr("researchListTitle")}</h1>
            <p className="research-list-header__subtitle">{tr("researchListSubtitle")}</p>
          </div>
          <Button primary onClick={handleNewResearch} disabled={loadStatus === "loading"}>
            {tr("researchListNewResearch")}
          </Button>
        </header>

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
                    {status}
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
                    {owner}
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
                <option value="confidence">{tr("researchListSortConfidence")}</option>
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
              <ErrorAlert title={tr("researchListErrorTitle")} message={loadError} />
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
                    <Button primary onClick={handleNewResearch}>
                      {tr("researchListNewResearch")}
                    </Button>
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
                      onDuplicate={handleDuplicate}
                      onArchive={handleArchive}
                      onMore={handleMore}
                    />
                  ))}
                </div>
              ) : null}
            </>
          ) : null}
        </div>
      </SectionCard>
    </AppShell>
  );
}
