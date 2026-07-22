"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import AppShell from "@/components/layout/AppShell";
import Button from "@/components/ui/Button";
import DataTable from "@/components/ui/DataTable";
import EmptyState from "@/components/ui/EmptyState";
import ErrorAlert from "@/components/ui/ErrorAlert";
import InterpretationPanel from "@/components/ui/InterpretationPanel";
import LoadingState from "@/components/ui/LoadingState";
import MetricCard from "@/components/ui/MetricCard";
import SectionCard from "@/components/ui/SectionCard";
import SectionHeader from "@/components/ui/SectionHeader";
import StatusBadge from "@/components/ui/StatusBadge";
import { runBacktest, saveBacktestRun } from "@/lib/api";
import { getApiDisplayMessage } from "@/lib/apiRequest";
import { generateBacktestInterpretation } from "@/lib/backtestInterpretation";
import {
  formatDateSeriesRange,
  formatMetricPercent,
  formatMetricSharpe,
  formatMetricTrades,
  formatPrice,
  getDrawdownTone,
  getReturnTone,
  getSharpeTone,
} from "@/lib/formatters";
import {
  getChartLabels,
  t,
  translateBackendText,
  translateDataSource,
  translateStrategyName,
  type Language,
  type TranslationKey,
} from "@/lib/i18n";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";
import type { BacktestResponse, BacktestStrategy, CombinedMode } from "@/types/market";

const BacktestChart = dynamic(() => import("@/components/BacktestChart"), {
  ssr: false,
  loading: () => <LoadingState message="Loading chart..." />,
});

const DEFAULT_CHART_START_DATE = "2022-01-01";
const DEFAULT_BACKTEST_TICKER = "AAPL";
const DEFAULT_SHORT_WINDOW = 20;
const DEFAULT_LONG_WINDOW = 60;
const DEFAULT_MOMENTUM_WINDOW = 60;
const DEFAULT_TRANSACTION_COST = 0.001;

const STRATEGY_GUIDE_KEYS: Record<
  BacktestStrategy,
  { what: TranslationKey; params: TranslationKey; read: TranslationKey }
> = {
  ma_crossover: {
    what: "strategyMaWhat",
    params: "strategyMaParams",
    read: "strategyMaRead",
  },
  momentum: {
    what: "strategyMomentumWhat",
    params: "strategyMomentumParams",
    read: "strategyMomentumRead",
  },
  combined_signal: {
    what: "strategyCombinedWhat",
    params: "strategyCombinedParams",
    read: "strategyCombinedRead",
  },
};

function getBacktestMetricHelp(lang: Language) {
  return {
    totalReturn: t(lang, "helpTotalReturn"),
    benchmarkReturn: t(lang, "helpBenchmarkReturn"),
    cagr: t(lang, "helpCagr"),
    sharpe: t(lang, "helpSharpe"),
    strategyMaxDrawdown: t(lang, "helpStrategyMaxDd"),
    benchmarkMaxDrawdown: t(lang, "helpBenchmarkMaxDd"),
    volatility: t(lang, "helpVolatility"),
    winRate: t(lang, "helpWinRate"),
    trades: t(lang, "helpTrades"),
    transactionCost: t(lang, "helpTransactionCost"),
  };
}

export default function StrategyLabPage() {
  const router = useRouter();
  const { language, setLanguage, tr } = useWorkspaceLanguage();
  const [backtestTicker, setBacktestTicker] = useState(DEFAULT_BACKTEST_TICKER);
  const [backtestStartDate, setBacktestStartDate] = useState(DEFAULT_CHART_START_DATE);
  const [backtestEndDate, setBacktestEndDate] = useState("");
  const [shortWindow, setShortWindow] = useState(DEFAULT_SHORT_WINDOW);
  const [longWindow, setLongWindow] = useState(DEFAULT_LONG_WINDOW);
  const [backtestStrategy, setBacktestStrategy] = useState<BacktestStrategy>("ma_crossover");
  const [momentumWindow, setMomentumWindow] = useState(DEFAULT_MOMENTUM_WINDOW);
  const [combinedMode, setCombinedMode] = useState<CombinedMode>("conservative");
  const [transactionCost, setTransactionCost] = useState(String(DEFAULT_TRANSACTION_COST));
  const [backtestResult, setBacktestResult] = useState<BacktestResponse | null>(null);
  const [backtestLoading, setBacktestLoading] = useState(false);
  const [backtestError, setBacktestError] = useState<string | null>(null);
  const [experimentNotes, setExperimentNotes] = useState("");
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);

  const chartLabels = getChartLabels(language);
  const backtestMetricHelp = getBacktestMetricHelp(language);

  async function handleRunBacktest() {
    const normalizedTicker = backtestTicker.trim().toUpperCase();
    const parsedShortWindow = Number(shortWindow);
    const parsedLongWindow = Number(longWindow);
    const parsedMomentumWindow = Number(momentumWindow);
    const parsedTransactionCost = Number(transactionCost);

    if (!normalizedTicker) {
      setBacktestError(tr("tickerEmpty"));
      return;
    }

    if (backtestStrategy === "ma_crossover" || backtestStrategy === "combined_signal") {
      if (!Number.isFinite(parsedShortWindow) || !Number.isFinite(parsedLongWindow)) {
        setBacktestError(tr("shortLongInvalid"));
        return;
      }

      if (parsedShortWindow >= parsedLongWindow) {
        setBacktestError(tr("shortLessThanLong"));
        return;
      }
    }

    if (backtestStrategy === "momentum" || backtestStrategy === "combined_signal") {
      if (!Number.isFinite(parsedMomentumWindow)) {
        setBacktestError(tr("momentumInvalid"));
        return;
      }
      if (parsedMomentumWindow < 5 || parsedMomentumWindow > 252) {
        setBacktestError(tr("momentumRange"));
        return;
      }
    }

    if (!Number.isFinite(parsedTransactionCost) || parsedTransactionCost < 0) {
      setBacktestError(tr("transactionCostInvalid"));
      return;
    }

    setBacktestLoading(true);
    setBacktestError(null);
    setBacktestResult(null);
    setSaveError(null);
    setSaveSuccess(null);

    try {
      const response = await runBacktest({
        ticker: normalizedTicker,
        start_date: backtestStartDate,
        end_date: backtestEndDate || undefined,
        strategy: backtestStrategy,
        short_window:
          backtestStrategy === "ma_crossover" || backtestStrategy === "combined_signal"
            ? parsedShortWindow
            : undefined,
        long_window:
          backtestStrategy === "ma_crossover" || backtestStrategy === "combined_signal"
            ? parsedLongWindow
            : undefined,
        momentum_window:
          backtestStrategy === "momentum" || backtestStrategy === "combined_signal"
            ? parsedMomentumWindow
            : undefined,
        combined_mode:
          backtestStrategy === "combined_signal" ? combinedMode : undefined,
        transaction_cost: parsedTransactionCost,
      });
      setBacktestResult(response);
    } catch (error) {
      setBacktestError(getApiDisplayMessage(error, tr("backtestFailed")));
    } finally {
      setBacktestLoading(false);
    }
  }

  async function handleSaveBacktestRun() {
    if (!backtestResult) {
      setSaveError(tr("saveRequiresResult"));
      return;
    }

    setSaveLoading(true);
    setSaveError(null);
    setSaveSuccess(null);

    try {
      const strategyConfig =
        backtestResult.strategy_config ??
        ({
          strategy: backtestResult.strategy,
          ...backtestResult.parameters,
        } as Record<string, unknown>);

      const response = await saveBacktestRun({
        ticker: backtestResult.ticker,
        data_source: backtestResult.data_source,
        strategy: backtestResult.strategy,
        strategy_config: strategyConfig,
        start_date: backtestResult.start_date,
        end_date: backtestResult.end_date,
        transaction_cost: backtestResult.parameters.transaction_cost,
        metrics: backtestResult.metrics as unknown as Record<string, unknown>,
        notes: experimentNotes.trim() || null,
        trade_log: (backtestResult.trade_log ?? []).map((trade) => ({
          date: trade.date,
          action: trade.action,
          price: trade.price,
          signal: trade.signal,
          position_after: trade.position_after,
          reason: trade.reason,
        })),
      });

      router.push(`/experiments?saved=${encodeURIComponent(response.id)}`);
    } catch (error) {
      setSaveError(getApiDisplayMessage(error, tr("saveBacktestFailed")));
    } finally {
      setSaveLoading(false);
    }
  }

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <SectionCard>
        <SectionHeader title={tr("strategyLab")} description={tr("strategyLabDesc")} />
        <p className="section-meta">{tr("strategyLabSimulatedNote")}</p>

        <div className="strategy-lab-guide">
          <p className="strategy-lab-guide__hint">{tr("strategySelectHint")}</p>
          <h3 className="strategy-lab-guide__title">
            {translateStrategyName(language, backtestStrategy)}
          </h3>
          <dl className="strategy-lab-guide__list">
            <div className="strategy-lab-guide__item">
              <dt>{tr("strategyGuideWhat")}</dt>
              <dd>{tr(STRATEGY_GUIDE_KEYS[backtestStrategy].what)}</dd>
            </div>
            <div className="strategy-lab-guide__item">
              <dt>{tr("strategyGuideParams")}</dt>
              <dd>{tr(STRATEGY_GUIDE_KEYS[backtestStrategy].params)}</dd>
            </div>
            <div className="strategy-lab-guide__item">
              <dt>{tr("strategyGuideRead")}</dt>
              <dd>{tr(STRATEGY_GUIDE_KEYS[backtestStrategy].read)}</dd>
            </div>
          </dl>
        </div>

        <div className="form-grid">
          <label className="form-field">
            <span className="form-label">{tr("ticker")}</span>
            <input
              className="form-input"
              type="text"
              value={backtestTicker}
              onChange={(e) => setBacktestTicker(e.target.value.toUpperCase())}
              placeholder="AAPL"
            />
          </label>

          <label className="form-field">
            <span className="form-label">{tr("backtestStartDate")}</span>
            <input
              className="form-input"
              type="date"
              value={backtestStartDate}
              onChange={(e) => setBacktestStartDate(e.target.value)}
            />
          </label>

          <label className="form-field">
            <span className="form-label">{tr("backtestEndDate")}</span>
            <input
              className="form-input"
              type="date"
              value={backtestEndDate}
              onChange={(e) => setBacktestEndDate(e.target.value)}
            />
          </label>

          <label className="form-field">
            <span className="form-label">{tr("strategy")}</span>
            <select
              className="form-select"
              value={backtestStrategy}
              onChange={(e) => setBacktestStrategy(e.target.value as BacktestStrategy)}
            >
              <option value="ma_crossover">{tr("maCrossover")}</option>
              <option value="momentum">{tr("momentumStrategy")}</option>
              <option value="combined_signal">{tr("combinedSignal")}</option>
            </select>
          </label>

          {(backtestStrategy === "ma_crossover" || backtestStrategy === "combined_signal") && (
            <>
              <label className="form-field">
                <span className="form-label">{tr("shortWindow")}</span>
                <input
                  className="form-input"
                  type="number"
                  min={2}
                  value={shortWindow}
                  onChange={(e) => setShortWindow(Number(e.target.value))}
                />
              </label>

              <label className="form-field">
                <span className="form-label">{tr("longWindow")}</span>
                <input
                  className="form-input"
                  type="number"
                  min={3}
                  value={longWindow}
                  onChange={(e) => setLongWindow(Number(e.target.value))}
                />
              </label>
            </>
          )}

          {(backtestStrategy === "momentum" || backtestStrategy === "combined_signal") && (
            <label className="form-field">
              <span className="form-label">{tr("momentumWindow")}</span>
              <input
                className="form-input"
                type="number"
                min={5}
                max={252}
                value={momentumWindow}
                onChange={(e) => setMomentumWindow(Number(e.target.value))}
              />
            </label>
          )}

          {backtestStrategy === "combined_signal" && (
            <label className="form-field">
              <span className="form-label">
                {tr("combinedMode")}
                <span className="form-label__hint">{tr("combinedModeHelper")}</span>
              </span>
              <select
                className="form-select"
                value={combinedMode}
                onChange={(e) => setCombinedMode(e.target.value as CombinedMode)}
              >
                <option value="conservative">{tr("conservative")}</option>
                <option value="aggressive">{tr("aggressive")}</option>
              </select>
            </label>
          )}

          <label className="form-field">
            <span className="form-label">
              {tr("transactionCost")}
              <span className="form-label__hint">{tr("transactionCostHelper")}</span>
            </span>
            <input
              className="form-input"
              type="number"
              min={0}
              step={0.0001}
              value={transactionCost}
              onChange={(e) => setTransactionCost(e.target.value)}
            />
          </label>
        </div>

        <Button onClick={handleRunBacktest} disabled={backtestLoading}>
          {backtestLoading ? tr("running") : tr("runBacktest")}
        </Button>

        <label className="form-field" style={{ marginTop: "1rem", display: "block" }}>
          <span className="form-label">{tr("experimentNotes")}</span>
          <textarea
            className="form-input"
            rows={3}
            value={experimentNotes}
            placeholder={tr("experimentNotesPlaceholder")}
            onChange={(e) => setExperimentNotes(e.target.value)}
          />
        </label>

        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", marginTop: "0.75rem" }}>
          <Button
            onClick={handleSaveBacktestRun}
            disabled={saveLoading || !backtestResult}
          >
            {saveLoading ? tr("savingBacktestRun") : tr("saveBacktestRun")}
          </Button>
          <Link href="/experiments" className="section-meta">
            {tr("openExperiments")}
          </Link>
        </div>

        {saveError && <ErrorAlert title={tr("saveBacktestFailed")} message={saveError} />}
        {saveSuccess && <p className="section-meta">{saveSuccess}</p>}

        <p className="section-meta">{tr("backtestBiasNote")}</p>
        <p className="section-meta">{tr("backtestWarmupNote")}</p>

        {backtestError && <ErrorAlert message={backtestError} />}
        {backtestLoading && <LoadingState message={tr("toolResultsLoading")} />}
        {!backtestLoading && !backtestResult && !backtestError && (
          <EmptyState
            title={tr("toolResultsEmptyTitle")}
            description={tr("toolResultsEmptyDescription")}
          />
        )}

        {backtestResult && (
          <>
            <div className="metric-grid">
              <MetricCard
                label={tr("totalReturn")}
                value={formatMetricPercent(backtestResult.metrics.total_return)}
                description={backtestMetricHelp.totalReturn}
                featured
                tone={getReturnTone(backtestResult.metrics.total_return)}
              />
              <MetricCard
                label={tr("benchmarkReturn")}
                value={formatMetricPercent(backtestResult.metrics.benchmark_return)}
                description={backtestMetricHelp.benchmarkReturn}
                featured
                tone={getReturnTone(backtestResult.metrics.benchmark_return)}
              />
              <MetricCard
                label={tr("cagr")}
                value={formatMetricPercent(backtestResult.metrics.cagr)}
                description={backtestMetricHelp.cagr}
                tone={getReturnTone(backtestResult.metrics.cagr)}
              />
              <MetricCard
                label={tr("sharpeRatio")}
                value={formatMetricSharpe(backtestResult.metrics.sharpe_ratio)}
                description={backtestMetricHelp.sharpe}
                featured
                tone={getSharpeTone(backtestResult.metrics.sharpe_ratio)}
              />
              <MetricCard
                label={tr("strategyMaxDrawdown")}
                value={formatMetricPercent(
                  backtestResult.metrics.strategy_max_drawdown ??
                    backtestResult.metrics.max_drawdown
                )}
                description={backtestMetricHelp.strategyMaxDrawdown}
                featured
                tone={getDrawdownTone(
                  backtestResult.metrics.strategy_max_drawdown ??
                    backtestResult.metrics.max_drawdown
                )}
              />
              <MetricCard
                label={tr("benchmarkMaxDrawdown")}
                value={formatMetricPercent(backtestResult.metrics.benchmark_max_drawdown)}
                description={backtestMetricHelp.benchmarkMaxDrawdown}
                tone={getDrawdownTone(backtestResult.metrics.benchmark_max_drawdown)}
              />
              <MetricCard
                label={tr("volatility")}
                value={formatMetricPercent(backtestResult.metrics.volatility)}
                description={backtestMetricHelp.volatility}
              />
              <MetricCard
                label={tr("winRate")}
                value={formatMetricPercent(backtestResult.metrics.win_rate)}
                description={backtestMetricHelp.winRate}
              />
              <MetricCard
                label={tr("numberOfTrades")}
                value={formatMetricTrades(backtestResult.metrics.number_of_trades)}
                description={backtestMetricHelp.trades}
              />
              <MetricCard
                label={tr("transactionCostTotal")}
                value={formatMetricPercent(backtestResult.metrics.transaction_cost_total)}
                description={backtestMetricHelp.transactionCost}
              />
            </div>

            <InterpretationPanel
              title={tr("backtestInterpretation")}
              sentences={generateBacktestInterpretation(backtestResult, language)}
              note={tr("backtestInterpretationNote")}
            />

            <details
              className="collapsible-panel"
              open={(backtestResult.trade_log ?? []).length > 0}
            >
              <summary>
                {tr("tradeLog")}
                {(backtestResult.trade_log ?? []).length > 0
                  ? ` (${(backtestResult.trade_log ?? []).length})`
                  : ""}
              </summary>
              <p className="collapsible-panel__desc">{tr("tradeLogDesc")}</p>
              <p className="collapsible-panel__desc">{tr("tradeLogDateNote")}</p>
              <div className="collapsible-panel__body">
                {(backtestResult.trade_log ?? []).length === 0 ? (
                  <EmptyState message={tr("tradeLogEmpty")} />
                ) : (
                  <>
                    {(backtestResult.trade_log ?? []).length > 15 && (
                      <p className="section-meta">{tr("tradeLogScrollHint")}</p>
                    )}
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
                        {(backtestResult.trade_log ?? []).map((trade) => (
                          <tr key={`${trade.date}-${trade.action}`}>
                            <td>{trade.date}</td>
                            <td>
                              <StatusBadge
                                label={trade.action === "BUY" ? tr("tradeBuy") : tr("tradeSell")}
                                variant={trade.action === "BUY" ? "buy" : "sell"}
                              />
                            </td>
                            <td className="num">{formatPrice(trade.price)}</td>
                            <td>{translateBackendText(language, trade.reason)}</td>
                            <td className="num">{trade.position_after}</td>
                          </tr>
                        ))}
                      </tbody>
                    </DataTable>
                  </>
                )}
              </div>
            </details>

            <p className="section-meta">
              {backtestResult.ticker} · {translateStrategyName(language, backtestResult.strategy)} ·{" "}
              {tr("actualDataRange")}: {formatDateSeriesRange(backtestResult.data, tr("na"))}
              {" · "}
              {tr("rows")}: {backtestResult.data.length}
              {" · "}
              {tr("dataSource")}: {translateDataSource(language, backtestResult.data_source)}
            </p>

            <BacktestChart data={backtestResult.data} labels={chartLabels} />
          </>
        )}
      </SectionCard>
    </AppShell>
  );
}
