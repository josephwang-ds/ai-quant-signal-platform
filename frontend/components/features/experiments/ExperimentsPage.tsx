"use client";

import { useEffect, useState } from "react";
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
  formatMetricPercent,
  formatMetricSharpe,
  getDrawdownTone,
  getReturnTone,
  getSharpeTone,
} from "@/lib/formatters";
import {
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

  async function loadList() {
    setListLoading(true);
    setListError(null);
    try {
      const response = await listBacktestRuns(50, 0);
      setItems(response.items);
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
        <SectionHeader title={tr("experimentsPageTitle")} />
        {listLoading ? <LoadingState message={tr("experimentsLoading")} /> : null}
        {listError ? (
          <ErrorAlert title={tr("experimentsLoadFailed")} message={listError} />
        ) : null}
        {!listLoading && !listError && items.length === 0 ? (
          <p className="section-meta">{tr("experimentsEmpty")}</p>
        ) : null}
        {!listLoading && items.length > 0 ? (
          <DataTable className="table-scroll">
            <thead>
              <tr>
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
              {items.map((item) => (
                <tr
                  key={item.id}
                  onClick={() => void handleSelectRun(item.id)}
                  style={{
                    cursor: "pointer",
                    background:
                      selectedId === item.id ? "rgba(59, 130, 246, 0.08)" : undefined,
                  }}
                >
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
                    {formatMetricPercent(
                      item.metrics?.strategy_max_drawdown ??
                        item.metrics?.max_drawdown ??
                        null
                    )}
                  </td>
                  <td className="num">{item.trade_count ?? 0}</td>
                  <td>{notesSnippet(item.notes)}</td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        ) : null}
        {!selectedId && !listLoading && items.length > 0 ? (
          <p className="section-meta">{tr("experimentsSelectHint")}</p>
        ) : null}
      </SectionCard>

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
                  value={formatMetricPercent(
                    detail.metrics?.strategy_max_drawdown ??
                      detail.metrics?.max_drawdown ??
                      null
                  )}
                  featured
                  tone={getDrawdownTone(
                    detail.metrics?.strategy_max_drawdown ??
                      detail.metrics?.max_drawdown ??
                      null
                  )}
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
