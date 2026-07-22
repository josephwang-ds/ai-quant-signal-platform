"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ExperimentRunCard } from "@/components/features/experiments/ExperimentRunCard";
import AppShell from "@/components/layout/AppShell";
import Button from "@/components/ui/Button";
import DataTable from "@/components/ui/DataTable";
import ErrorAlert from "@/components/ui/ErrorAlert";
import LoadingState from "@/components/ui/LoadingState";
import MetricCard from "@/components/ui/MetricCard";
import SectionCard from "@/components/ui/SectionCard";
import SectionHeader from "@/components/ui/SectionHeader";
import StatusBadge from "@/components/ui/StatusBadge";
import {
  deleteBacktestRun,
  getBacktestRun,
  listBacktestRuns,
} from "@/lib/api";
import {
  buildExperimentCompareLabel,
  buildExperimentCompareSummary,
  getDrawdownMetric,
  isExperimentCompareHighlighted,
  MAX_COMPARE_RUNS,
} from "@/lib/experimentCompare";
import {
  DEFAULT_EXPERIMENT_LIST_FILTERS,
  filterAndSortExperimentRuns,
  getUniqueExperimentStrategies,
  getUniqueExperimentTickers,
  sanitizeExperimentListFilters,
  type ExperimentListFilters,
} from "@/lib/experimentListFilters";
import {
  formatMetricPercent,
  formatMetricSharpe,
  formatMetricTrades,
  formatPrice,
  getDrawdownTone,
  getReturnTone,
  getSharpeTone,
} from "@/lib/formatters";
import {
  formatMessage,
  translateBackendText,
  translateStrategyName,
} from "@/lib/i18n";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";
import type { BacktestRunDetail, BacktestRunSummary } from "@/types/market";
import type { Language } from "@/lib/i18n";

function formatCreatedAt(value: string, language: Language): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString(language === "zh" ? "zh-CN" : "en-US");
}

function getExperimentTradeCount(run: BacktestRunSummary): number {
  return run.trade_count ?? run.metrics?.number_of_trades ?? 0;
}

function notesSnippet(notes?: string | null): string {
  if (!notes) {
    return "—";
  }
  return notes.length > 48 ? `${notes.slice(0, 48)}…` : notes;
}

type ExperimentDetailPanelProps = {
  language: Language;
  tr: (key: import("@/lib/i18n").TranslationKey) => string;
  selectedId: string | null;
  detail: BacktestRunDetail | null;
  detailLoading: boolean;
  detailError: string | null;
  actionMessage: string | null;
  deleteLoading: boolean;
  onClose: () => void;
  onDelete: () => void;
};

function ExperimentDetailPanel({
  language,
  tr,
  detail,
  detailLoading,
  detailError,
  actionMessage,
  deleteLoading,
  onClose,
  onDelete,
}: Omit<ExperimentDetailPanelProps, "selectedId">) {
  return (
    <div className="experiments-detail-panel">
      <h3 className="module-card__title">{tr("experimentsDetail")}</h3>
      <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", marginBottom: "0.75rem" }}>
        <Button onClick={onClose}>{tr("experimentsBackToList")}</Button>
        <Button onClick={onDelete} disabled={deleteLoading}>
          {deleteLoading ? tr("running") : tr("experimentsDelete")}
        </Button>
      </div>

      {actionMessage ? <p className="section-meta">{actionMessage}</p> : null}
      {detailLoading ? <LoadingState message={tr("experimentsLoading")} /> : null}
      {detailError ? (
        <ErrorAlert
          title={tr(detail ? "experimentsDeleteFailed" : "experimentsLoadFailed")}
          message={detailError}
        />
      ) : null}

      {detail && !detailLoading ? (
        <>
          <p className="section-meta">
            {detail.ticker} · {translateStrategyName(language, detail.strategy)} ·{" "}
            {tr("experimentsCreatedAt")}: {formatCreatedAt(detail.created_at, language)}
          </p>

          <div className="metric-grid">
            <MetricCard
              label={tr("totalReturn")}
              value={formatMetricPercent(detail.metrics?.total_return ?? null)}
              featured
              tone={getReturnTone(detail.metrics?.total_return ?? null)}
            />
            <MetricCard
              label={tr("sharpeRatio")}
              value={formatMetricSharpe(detail.metrics?.sharpe_ratio ?? null)}
              featured
              tone={getSharpeTone(detail.metrics?.sharpe_ratio ?? null)}
            />
            <MetricCard
              label={tr("strategyMaxDrawdown")}
              value={formatMetricPercent(getDrawdownMetric(detail))}
              featured
              tone={getDrawdownTone(getDrawdownMetric(detail))}
            />
            <MetricCard
              label={tr("benchmarkReturn")}
              value={formatMetricPercent(detail.metrics?.benchmark_return ?? null)}
              tone={getReturnTone(detail.metrics?.benchmark_return ?? null)}
            />
          </div>

          {detail.notes ? (
            <>
              <h3 className="module-card__title">{tr("experimentsNotes")}</h3>
              <p className="section-meta">{detail.notes}</p>
            </>
          ) : null}

          <h3 className="module-card__title">{tr("experimentsConfig")}</h3>
          <pre
            className="section-meta font-mono"
            style={{ whiteSpace: "pre-wrap", wordBreak: "break-word", fontSize: "0.8125rem" }}
          >
            {JSON.stringify(detail.strategy_config, null, 2)}
          </pre>

          <h3 className="module-card__title">{tr("tradeLog")}</h3>
          {(detail.trades ?? []).length === 0 ? (
            <p className="section-meta">{tr("experimentsNoTrades")}</p>
          ) : (
            <DataTable className="table-scroll--trade-log">
              <thead>
                <tr>
                  <th>{tr("tradeDate")}</th>
                  <th>{tr("tradeLogAction")}</th>
                  <th className="num">{tr("price")}</th>
                  <th>{tr("tradeLogReason")}</th>
                  <th className="num">{tr("positionAfter")}</th>
                </tr>
              </thead>
              <tbody>
                {detail.trades.map((trade) => (
                  <tr key={`${trade.id}-${trade.trade_date}-${trade.action}`}>
                    <td>{trade.trade_date}</td>
                    <td>
                      <StatusBadge
                        label={trade.action === "BUY" ? tr("tradeBuy") : tr("tradeSell")}
                        variant={trade.action === "BUY" ? "buy" : "sell"}
                      />
                    </td>
                    <td className="num">
                      {trade.price == null ? "—" : formatPrice(Number(trade.price))}
                    </td>
                    <td>
                      {trade.reason ? translateBackendText(language, trade.reason) : "—"}
                    </td>
                    <td className="num">{trade.position_after ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
          )}
        </>
      ) : null}
    </div>
  );
}

export default function ExperimentsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { language, setLanguage, tr } = useWorkspaceLanguage();
  const [items, setItems] = useState<BacktestRunSummary[]>([]);
  const [listLoading, setListLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<BacktestRunDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [showCompare, setShowCompare] = useState(false);
  const [compareError, setCompareError] = useState<string | null>(null);
  const [listFilters, setListFilters] = useState<ExperimentListFilters>(
    DEFAULT_EXPERIMENT_LIST_FILTERS
  );
  const handledSavedId = useRef<string | null>(null);

  const displayedItems = useMemo(
    () => filterAndSortExperimentRuns(items, listFilters),
    [items, listFilters]
  );
  const tickerOptions = useMemo(() => getUniqueExperimentTickers(items), [items]);
  const strategyOptions = useMemo(
    () => getUniqueExperimentStrategies(items),
    [items]
  );

  const compareRuns = useMemo(
    () =>
      compareIds
        .map((id) => items.find((item) => item.id === id))
        .filter((item): item is BacktestRunSummary => item != null),
    [items, compareIds]
  );
  const compareSummary = useMemo(
    () => buildExperimentCompareSummary(compareRuns),
    [compareRuns]
  );

  async function loadList() {
    setListLoading(true);
    setListError(null);
    try {
      const response = await listBacktestRuns(50, 0);
      setItems(response.items);
      setCompareIds((current) =>
        current.filter((id) => response.items.some((item) => item.id === id))
      );
    } catch (error) {
      setListError(
        error instanceof Error ? error.message : tr("experimentsLoadFailed")
      );
    } finally {
      setListLoading(false);
    }
  }

  useEffect(() => {
    void loadList();
    // 仅挂载时加载一次
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    setListFilters((current) => sanitizeExperimentListFilters(current, items));
  }, [items, tickerOptions, strategyOptions]);

  useEffect(() => {
    const savedId = searchParams.get("saved");
    if (!savedId || listLoading || handledSavedId.current === savedId) {
      return;
    }
    const savedRun = items.find((item) => item.id === savedId);
    if (!savedRun) {
      return;
    }
    handledSavedId.current = savedId;
    setActionMessage(tr("experimentsSavedRedirect"));
    void handleSelectRun(savedId);
    router.replace("/experiments");
  }, [items, listLoading, router, searchParams, tr]);

  function handleResetFilters() {
    setListFilters(DEFAULT_EXPERIMENT_LIST_FILTERS);
  }

  function toggleCompareSelection(runId: string) {
    setCompareError(null);
    setCompareIds((current) => {
      if (current.includes(runId)) {
        return current.filter((id) => id !== runId);
      }
      if (current.length >= MAX_COMPARE_RUNS) {
        setCompareError(tr("experimentsCompareMax"));
        return current;
      }
      return [...current, runId];
    });
  }

  function handleShowCompare() {
    if (compareIds.length < 2) {
      setCompareError(tr("experimentsCompareNeedTwo"));
      setShowCompare(false);
      return;
    }
    setCompareError(null);
    setShowCompare(true);
  }

  function handleClearCompare() {
    setCompareIds([]);
    setShowCompare(false);
    setCompareError(null);
  }

  async function handleSelectRun(runId: string) {
    setSelectedId(runId);
    setDetailLoading(true);
    setDetailError(null);
    setActionMessage(null);
    try {
      const response = await getBacktestRun(runId);
      setDetail(response);
    } catch (error) {
      setDetail(null);
      setDetailError(
        error instanceof Error ? error.message : tr("experimentsLoadFailed")
      );
    } finally {
      setDetailLoading(false);
    }
  }

  async function handleDelete() {
    if (!selectedId) {
      return;
    }
    if (!window.confirm(tr("experimentsDeleteConfirm"))) {
      return;
    }
    setDeleteLoading(true);
    setDetailError(null);
    setActionMessage(null);
    try {
      await deleteBacktestRun(selectedId);
      setActionMessage(tr("experimentsDeleted"));
      setSelectedId(null);
      setDetail(null);
      await loadList();
    } catch (error) {
      setDetailError(
        error instanceof Error ? error.message : tr("experimentsDeleteFailed")
      );
    } finally {
      setDeleteLoading(false);
    }
  }

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <SectionCard>
        <SectionHeader
          title={tr("experimentsPageTitle")}
          description={tr("experimentsPageDesc")}
        />

        {listLoading ? <LoadingState message={tr("experimentsLoading")} /> : null}
        {listError ? (
          <ErrorAlert title={tr("experimentsLoadFailed")} message={listError} />
        ) : null}
        {!listLoading && !listError && items.length === 0 ? (
          <p className="section-meta">{tr("experimentsEmpty")}</p>
        ) : null}

        {!listLoading && items.length > 0 ? (
          <>
            <div className="experiments-filter-bar">
              <label className="form-field">
                <span className="form-label">{tr("experimentsFilterTicker")}</span>
                <select
                  className="form-select"
                  value={listFilters.ticker}
                  onChange={(event) =>
                    setListFilters((current) => ({
                      ...current,
                      ticker: event.target.value,
                    }))
                  }
                >
                  <option value="all">{tr("experimentsFilterAll")}</option>
                  {tickerOptions.map((ticker) => (
                    <option key={ticker} value={ticker}>
                      {ticker}
                    </option>
                  ))}
                </select>
              </label>

              <label className="form-field">
                <span className="form-label">{tr("experimentsFilterStrategy")}</span>
                <select
                  className="form-select"
                  value={listFilters.strategy}
                  onChange={(event) =>
                    setListFilters((current) => ({
                      ...current,
                      strategy: event.target.value,
                    }))
                  }
                >
                  <option value="all">{tr("experimentsFilterAll")}</option>
                  {strategyOptions.map((strategy) => (
                    <option key={strategy} value={strategy}>
                      {translateStrategyName(language, strategy)}
                    </option>
                  ))}
                </select>
              </label>

              <label className="form-field">
                <span className="form-label">{tr("experimentsSortBy")}</span>
                <select
                  className="form-select"
                  value={listFilters.sortKey}
                  onChange={(event) =>
                    setListFilters((current) => ({
                      ...current,
                      sortKey: event.target.value as ExperimentListFilters["sortKey"],
                    }))
                  }
                >
                  <option value="created_at">{tr("experimentsSortCreatedAt")}</option>
                  <option value="total_return">{tr("experimentsSortTotalReturn")}</option>
                  <option value="sharpe_ratio">{tr("experimentsSortSharpe")}</option>
                  <option value="drawdown">{tr("experimentsSortDrawdown")}</option>
                </select>
              </label>

              <label className="form-field">
                <span className="form-label">{tr("experimentsSortDirection")}</span>
                <select
                  className="form-select"
                  value={listFilters.sortDirection}
                  onChange={(event) =>
                    setListFilters((current) => ({
                      ...current,
                      sortDirection: event.target
                        .value as ExperimentListFilters["sortDirection"],
                    }))
                  }
                >
                  <option value="desc">{tr("experimentsSortDesc")}</option>
                  <option value="asc">{tr("experimentsSortAsc")}</option>
                </select>
              </label>

              <Button onClick={handleResetFilters}>{tr("experimentsFilterReset")}</Button>
            </div>

            <div className="experiments-toolbar-row">
              <p className="section-meta" style={{ margin: 0 }}>
                {formatMessage(tr("experimentsShowingCount"), {
                  shown: displayedItems.length,
                  total: items.length,
                })}
              </p>
              <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
                <Button onClick={handleShowCompare} disabled={compareIds.length < 2}>
                  {tr("experimentsCompareSelect")} ({compareIds.length})
                </Button>
                <Button onClick={handleClearCompare} disabled={compareIds.length === 0}>
                  {tr("experimentsCompareClear")}
                </Button>
              </div>
            </div>

            {compareError ? (
              <ErrorAlert title={tr("experimentsCompareTitle")} message={compareError} />
            ) : null}

            {displayedItems.length === 0 ? (
              <p className="section-meta">{tr("experimentsFilterEmpty")}</p>
            ) : (
              <div className="experiment-run-list">
                {displayedItems.map((item) => (
                  <ExperimentRunCard
                    key={item.id}
                    run={item}
                    language={language}
                    selected={selectedId === item.id}
                    compareSelected={compareIds.includes(item.id)}
                    tr={tr}
                    onSelect={() => void handleSelectRun(item.id)}
                    onToggleCompare={() => toggleCompareSelection(item.id)}
                  />
                ))}
              </div>
            )}
          </>
        ) : null}
      </SectionCard>

      {selectedId ? (
        <SectionCard>
          <ExperimentDetailPanel
            language={language}
            tr={tr}
            detail={detail}
            detailLoading={detailLoading}
            detailError={detailError}
            actionMessage={actionMessage}
            deleteLoading={deleteLoading}
            onClose={() => {
              setSelectedId(null);
              setDetail(null);
              setDetailError(null);
            }}
            onDelete={() => void handleDelete()}
          />
        </SectionCard>
      ) : null}

      {showCompare && compareRuns.length >= 2 ? (
        <SectionCard>
          <SectionHeader
            title={tr("experimentsCompareTitle")}
            description={tr("experimentsCompareDesc")}
          />
          <p className="section-meta">{tr("experimentsCompareSummary")}</p>
          <div className="metric-grid">
            <MetricCard
              label={tr("experimentsCompareBestReturn")}
              value={compareSummary.bestTotalReturn ?? tr("na")}
            />
            <MetricCard
              label={tr("experimentsCompareBestSharpe")}
              value={compareSummary.bestSharpe ?? tr("na")}
            />
            <MetricCard
              label={tr("experimentsCompareLowestDrawdown")}
              value={compareSummary.lowestDrawdown ?? tr("na")}
            />
          </div>

          <DataTable className="table-scroll">
            <thead>
              <tr>
                <th>{tr("experimentsCompareRunLabel")}</th>
                <th>{tr("ticker")}</th>
                <th>{tr("strategy")}</th>
                <th className="num">{tr("totalReturn")}</th>
                <th className="num">{tr("benchmarkReturn")}</th>
                <th className="num">{tr("cagr")}</th>
                <th className="num">{tr("sharpeRatio")}</th>
                <th className="num">{tr("strategyMaxDrawdown")}</th>
                <th className="num">{tr("winRate")}</th>
                <th className="num">{tr("numberOfTrades")}</th>
                <th>{tr("experimentsNotes")}</th>
              </tr>
            </thead>
            <tbody>
              {compareRuns.map((run) => {
                const highlighted = isExperimentCompareHighlighted(run, compareRuns);
                return (
                  <tr
                    key={run.id}
                    className={highlighted ? "experiments-row--selected" : undefined}
                  >
                    <td>{buildExperimentCompareLabel(run)}</td>
                    <td>{run.ticker}</td>
                    <td>{translateStrategyName(language, run.strategy)}</td>
                    <td className="num">
                      {formatMetricPercent(run.metrics?.total_return ?? null)}
                    </td>
                    <td className="num">
                      {formatMetricPercent(run.metrics?.benchmark_return ?? null)}
                    </td>
                    <td className="num">
                      {formatMetricPercent(run.metrics?.cagr ?? null)}
                    </td>
                    <td className="num">
                      {formatMetricSharpe(run.metrics?.sharpe_ratio ?? null)}
                    </td>
                    <td className="num">
                      {formatMetricPercent(getDrawdownMetric(run))}
                    </td>
                    <td className="num">
                      {formatMetricPercent(run.metrics?.win_rate ?? null)}
                    </td>
                    <td className="num">
                      {formatMetricTrades(getExperimentTradeCount(run))}
                    </td>
                    <td>{notesSnippet(run.notes)}</td>
                  </tr>
                );
              })}
            </tbody>
          </DataTable>
        </SectionCard>
      ) : null}
    </AppShell>
  );
}
