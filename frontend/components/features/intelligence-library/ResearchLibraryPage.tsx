"use client";

import AppShell from "@/components/layout/AppShell";
import LatestPublishedRunCard from "@/components/features/intelligence-library/LatestPublishedRunCard";
import PublishedRunCard from "@/components/features/intelligence-library/PublishedRunCard";
import RunTypeFilter from "@/components/features/intelligence-library/RunTypeFilter";
import {
  ResearchLibraryEmptyState,
  ResearchLibraryErrorState,
  ResearchLibraryLoading,
} from "@/components/features/intelligence-library/ResearchLibraryStates";
import { usePublishedRuns } from "@/lib/intelligence/usePublishedRuns";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

/**
 * Phase 4.6B — Published Research Library.
 * Source of truth: Phase 4.5 intelligence query layer only.
 */
export default function ResearchLibraryPage() {
  const { language, setLanguage } = useWorkspaceLanguage();
  const {
    status,
    filteredRuns,
    latest,
    listError,
    runTypeFilter,
    availableRunTypes,
    setRunTypeFilter,
    reload,
  } = usePublishedRuns();
  const zh = language === "zh";

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <div className="research-library" data-testid="research-library">
        <header className="research-library__header">
          <h1>{zh ? "研究资料库" : "Research Library"}</h1>
          <p>
            {zh
              ? "审阅已发布的量化研究，保留证据、验证记录与可复现出处。"
              : "Review published quantitative research with preserved evidence, validation and reproducible provenance."}
          </p>
        </header>

        {status === "loading" ? <ResearchLibraryLoading language={language} /> : null}

        {status === "error" || status === "inconsistent" ? (
          listError ? (
            <ResearchLibraryErrorState
              language={language}
              error={listError}
              onRetry={reload}
            />
          ) : null
        ) : null}

        {status === "empty" ? (
          <ResearchLibraryEmptyState language={language} />
        ) : null}

        {status === "ready" ? (
          <>
            {latest.kind === "ready" ? (
              <LatestPublishedRunCard run={latest.run} language={language} />
            ) : null}

            {latest.kind === "unavailable" ? (
              <p
                className="research-library__latest-note"
                role="status"
                data-testid="latest-unavailable-note"
              >
                {zh
                  ? "最新已发布研究暂时不可用；下方列表仍可浏览。"
                  : "Latest published research is temporarily unavailable; the list below remains available."}
              </p>
            ) : null}

            <section
              className="research-library__runs"
              aria-labelledby="published-runs-title"
              data-testid="published-runs-section"
            >
              <header className="research-library__section-header research-library__section-header--row">
                <h2 id="published-runs-title">
                  {zh ? "已发布研究运行" : "Published Research Runs"}
                </h2>
                <RunTypeFilter
                  language={language}
                  value={runTypeFilter}
                  options={availableRunTypes}
                  onChange={setRunTypeFilter}
                />
              </header>

              {filteredRuns.length === 0 ? (
                <p className="research-library__filter-empty" role="status">
                  {zh
                    ? "当前类型下没有已发布研究。"
                    : "No published runs match this run type."}
                </p>
              ) : (
                <ul className="research-library__grid">
                  {filteredRuns.map((run) => (
                    <li key={run.run_id}>
                      <PublishedRunCard run={run} language={language} />
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </>
        ) : null}

        <p className="research-library__disclaimer" data-testid="research-library-disclaimer">
          {zh
            ? "仅供研究与作品集演示。非投资建议，不用于实盘交易。"
            : "For research and portfolio demonstration only. Not investment advice and not intended for live trading."}
        </p>
      </div>
    </AppShell>
  );
}
