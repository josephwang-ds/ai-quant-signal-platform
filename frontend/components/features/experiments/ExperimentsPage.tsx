"use client";

import { useEffect, useMemo, useState } from "react";
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
  type ExperimentListFilters,
} from "@/lib/experimentListFilters";
import {
  formatMetricPercent,
  formatMetricSharpe,
  formatMetricTrades,
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

function formatCreatedAt(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

function notesSnippet(notes?: string | null): string {
  if (!notes) {
    return "—";
  }
  return notes.length > 48 ? `${notes.slice(0, 48)}…` : notes;
}

export default function ExperimentsPage() {
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
    () => items.filter((item) => compareIds.includes(item.id)),
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
      </SectionCard>

      <SectionCard>
        <SectionHeader
          title={tr("experimentsPageTitle")}
          description={tr("experimentsCompareDesc")}
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
            <div
              style={{
                display: "grid",
                gap: "0.75rem",
                gridTemplateColumns: "repeat(auto-fit, minmax(12rem, 1fr))",
              }}
            >
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
            </div>

            <p className="section-meta">
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
            {compareError ? (
              <ErrorAlert title={tr("experimentsCompareTitle")} message={compareError} />
            ) : null}

            {displayedItems.length === 0 ? (
              <p className="section-meta">{tr("experimentsFilterEmpty")}</p>
            ) : (
            <DataTable className="table-scroll">
              <thead>
                <tr>
                  <th aria-label="compare" />
                  <th>{tr("experimentsCreatedAt")}</th>
                  <th>{tr("ticker")}</th>
                  <th>{tr("strategy")}</th>
                  <th className="num">{tr("totalReturn")}</th>
                  <th className="num">{tr("sharpeRatio")}</th>
                  <th className="num">{tr("strategyMaxDrawdown")}</th>
                  <th className="num">{tr("experimentsTradeCount")}</th>
                  <th>{tr("experimentsNotes")}</th>
                </tr>
              </thead>
              <tbody>
                {displayedItems.map((item) => (
                  <tr
                    key={item.id}
                    onClick={() => void handleSelectRun(item.id)}
                    style={{
                      cursor: "pointer",
                      background:
                        selectedId === item.id
                          ? "rgba(59, 130, 246, 0.08)"
                          : compareIds.includes(item.id)
                            ? "rgba(16, 185, 129, 0.08)"
                            : undefined,
                    }}
                  >
                    <td onClick={(event) => event.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={compareIds.includes(item.id)}
                        onChange={() => toggleCompareSelection(item.id)}
                        aria-label={`compare-${item.id}`}
                      />
                    </td>
                    <td>{formatCreatedAt(item.created_at)}</td>
                    <td>{item.ticker}</td>
                    <td>{translateStrategyName(language, item.strategy)}</td>
                    <td className="num">
                      {formatMetricPercent(item.metrics?.total_return ?? null)}
                    </td>
                    <td className="num">
                      {formatMetricSharpe(item.metrics?.sharpe_ratio ?? null)}
                    </td>
                    <td className="num">
                      {formatMetricPercent(getDrawdownMetric(item))}
                    </td>
                    <td className="num">{item.trade_count ?? 0}</td>
                    <td>{notesSnippet(item.notes)}</td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
            )}
          </>
        ) : null}
        {!selectedId && !listLoading && items.length > 0 ? (
          <p className="section-meta">{tr("experimentsSelectHint")}</p>
        ) : null}
      </SectionCard>

      {showCompare && compareRuns.length >= 2 ? (
        <SectionCard>
          <SectionHeader title={tr("experimentsCompareTitle")} />
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
                const highlighted = isExperimentCompareHighlighted(run, compareSummary);
                return (
                  <tr
                    key={run.id}
                    style={
                      highlighted
                        ? { background: "rgba(59, 130, 246, 0.08)" }
                        : undefined
                    }
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
                      {formatMetricTrades(run.metrics?.number_of_trades ?? null)}
                    </td>
                    <td>{notesSnippet(run.notes)}</td>
                  </tr>
                );
              })}
            </tbody>
          </DataTable>
        </SectionCard>
      ) : null}

      {selectedId ? (
        <SectionCard>
          <SectionHeader title={tr("experimentsDetail")} />
          <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
            <Button
              onClick={() => {
                setSelectedId(null);
                setDetail(null);
                setDetailError(null);
              }}
            >
              {tr("experimentsBackToList")}
            </Button>
            <Button onClick={() => void handleDelete()} disabled={deleteLoading}>
              {deleteLoading ? tr("running") : tr("experimentsDelete")}
            </Button>
          </div>

          {actionMessage ? <p className="section-meta">{actionMessage}</p> : null}
          {detailLoading ? <LoadingState message={tr("experimentsLoading")} /> : null}
          {detailError ? (
            <ErrorAlert title={tr("experimentsLoadFailed")} message={detailError} />
          ) : null}

          {detail && !detailLoading ? (
            <>
              <p className="section-meta">
                {detail.ticker} · {translateStrategyName(language, detail.strategy)} ·{" "}
                {tr("experimentsCreatedAt")}: {formatCreatedAt(detail.created_at)}
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
                className="section-meta"
                style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}
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
                            label={
                              trade.action === "BUY" ? tr("tradeBuy") : tr("tradeSell")
                            }
                            variant={trade.action === "BUY" ? "buy" : "sell"}
                          />
                        </td>
                        <td className="num">
                          {trade.price == null ? "—" : Number(trade.price).toFixed(2)}
                        </td>
                        <td>
                          {trade.reason
                            ? translateBackendText(language, trade.reason)
                            : "—"}
                        </td>
                        <td className="num">{trade.position_after ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </DataTable>
              )}
            </>
          ) : null}
        </SectionCard>
      ) : null}
    </AppShell>
  );
}
