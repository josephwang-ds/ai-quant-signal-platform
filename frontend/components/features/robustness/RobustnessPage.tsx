"use client";

import { useState } from "react";
import AppShell from "@/components/layout/AppShell";
import Button from "@/components/ui/Button";
import DataTable from "@/components/ui/DataTable";
import ErrorAlert from "@/components/ui/ErrorAlert";
import InterpretationPanel from "@/components/ui/InterpretationPanel";
import SectionCard from "@/components/ui/SectionCard";
import SectionHeader from "@/components/ui/SectionHeader";
import { runBacktestSensitivity, runOOSValidation } from "@/lib/api";
import {
  formatMetricPercent,
  formatMetricSharpe,
  formatMetricTrades,
} from "@/lib/formatters";
import {
  getOOSMetricRows,
  getOOSSegmentLabels,
  translateDataSource,
  translateOOSInterpretation,
  translateStrategyName,
} from "@/lib/i18n";
import {
  generateSensitivityInterpretation,
  sortSensitivityResults,
} from "@/lib/sensitivityInterpretation";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";
import type { OOSResponse, OOSSegmentMetrics, SensitivityResponse } from "@/types/market";

const DEFAULT_START_DATE = "2022-01-01";
const DEFAULT_TICKER = "AAPL";
const DEFAULT_SHORT_WINDOW = 20;
const DEFAULT_LONG_WINDOW = 60;
const DEFAULT_TRANSACTION_COST = 0.001;
const DEFAULT_SPLIT_DATE = "2025-01-01";
const DEFAULT_SENSITIVITY_PAIRS = [
  { short: 10, long: 30 },
  { short: 20, long: 60 },
  { short: 50, long: 120 },
  { short: 50, long: 200 },
];

type OOSSegmentKey = "full_period" | "in_sample" | "out_of_sample";

function getOOSMetricValue(metrics: OOSSegmentMetrics, key: string): number | null {
  switch (key) {
    case "total_return":
      return metrics.total_return;
    case "benchmark_return":
      return metrics.benchmark_return;
    case "cagr":
      return metrics.cagr;
    case "sharpe_ratio":
      return metrics.sharpe_ratio;
    case "strategy_max_drawdown":
      return metrics.strategy_max_drawdown ?? metrics.max_drawdown;
    case "benchmark_max_drawdown":
      return metrics.benchmark_max_drawdown;
    case "volatility":
      return metrics.volatility;
    case "number_of_trades":
      return metrics.number_of_trades;
    default:
      return null;
  }
}

export default function RobustnessPage() {
  const { language, setLanguage, tr } = useWorkspaceLanguage();

  const [sensitivityTicker, setSensitivityTicker] = useState(DEFAULT_TICKER);
  const [sensitivityStartDate, setSensitivityStartDate] = useState(DEFAULT_START_DATE);
  const [sensitivityEndDate, setSensitivityEndDate] = useState("");
  const [sensitivityTransactionCost, setSensitivityTransactionCost] = useState(
    String(DEFAULT_TRANSACTION_COST)
  );
  const [sensitivityResult, setSensitivityResult] = useState<SensitivityResponse | null>(null);
  const [sensitivityLoading, setSensitivityLoading] = useState(false);
  const [sensitivityError, setSensitivityError] = useState<string | null>(null);

  const [oosTicker, setOosTicker] = useState(DEFAULT_TICKER);
  const [oosStartDate, setOosStartDate] = useState(DEFAULT_START_DATE);
  const [oosEndDate, setOosEndDate] = useState("");
  const [oosSplitDate, setOosSplitDate] = useState(DEFAULT_SPLIT_DATE);
  const [oosShortWindow, setOosShortWindow] = useState(DEFAULT_SHORT_WINDOW);
  const [oosLongWindow, setOosLongWindow] = useState(DEFAULT_LONG_WINDOW);
  const [oosTransactionCost, setOosTransactionCost] = useState(String(DEFAULT_TRANSACTION_COST));
  const [oosResult, setOosResult] = useState<OOSResponse | null>(null);
  const [oosLoading, setOosLoading] = useState(false);
  const [oosError, setOosError] = useState<string | null>(null);

  const oosSegmentLabels = getOOSSegmentLabels(language);
  const oosMetricRows = getOOSMetricRows(language);

  async function handleRunSensitivityAnalysis() {
    const normalizedTicker = sensitivityTicker.trim().toUpperCase();
    const parsedTransactionCost = Number(sensitivityTransactionCost);

    if (!normalizedTicker) {
      setSensitivityError(tr("tickerEmpty"));
      return;
    }

    if (!Number.isFinite(parsedTransactionCost) || parsedTransactionCost < 0) {
      setSensitivityError(tr("transactionCostInvalid"));
      return;
    }

    setSensitivityLoading(true);
    setSensitivityError(null);
    setSensitivityResult(null);

    try {
      const response = await runBacktestSensitivity({
        ticker: normalizedTicker,
        start_date: sensitivityStartDate,
        end_date: sensitivityEndDate || undefined,
        transaction_cost: parsedTransactionCost,
      });
      setSensitivityResult(response);
    } catch (error) {
      setSensitivityError(
        error instanceof Error ? error.message : tr("sensitivityFailed")
      );
    } finally {
      setSensitivityLoading(false);
    }
  }

  async function handleRunOOSValidation() {
    const normalizedTicker = oosTicker.trim().toUpperCase();
    const parsedShortWindow = Number(oosShortWindow);
    const parsedLongWindow = Number(oosLongWindow);
    const parsedTransactionCost = Number(oosTransactionCost);

    if (!normalizedTicker) {
      setOosError(tr("tickerEmpty"));
      return;
    }

    if (!Number.isFinite(parsedShortWindow) || !Number.isFinite(parsedLongWindow)) {
      setOosError(tr("shortLongInvalid"));
      return;
    }

    if (parsedShortWindow >= parsedLongWindow) {
      setOosError(tr("shortLessThanLong"));
      return;
    }

    if (!Number.isFinite(parsedTransactionCost) || parsedTransactionCost < 0) {
      setOosError(tr("transactionCostInvalid"));
      return;
    }

    if (oosSplitDate <= oosStartDate) {
      setOosError(tr("splitAfterStart"));
      return;
    }

    if (oosEndDate && oosEndDate <= oosSplitDate) {
      setOosError(tr("endAfterSplit"));
      return;
    }

    setOosLoading(true);
    setOosError(null);
    setOosResult(null);

    try {
      const response = await runOOSValidation({
        ticker: normalizedTicker,
        start_date: oosStartDate,
        split_date: oosSplitDate,
        end_date: oosEndDate || undefined,
        short_window: parsedShortWindow,
        long_window: parsedLongWindow,
        transaction_cost: parsedTransactionCost,
      });
      setOosResult(response);
    } catch (error) {
      setOosError(error instanceof Error ? error.message : tr("oosFailed"));
    } finally {
      setOosLoading(false);
    }
  }

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <SectionCard>
        <SectionHeader
          title={tr("robustnessChecks")}
          description={tr("robustnessPageDesc")}
        />
        <p className="section-meta">{tr("robustnessEducationalNote")}</p>
      </SectionCard>

      <SectionCard id="sensitivity-analysis">
        <SectionHeader title={tr("sensitivityAnalysis")} description={tr("sensitivityDesc")} />
        <p className="section-header__description">{tr("sensitivityExplain")}</p>

        <div className="section-meta">
          <p>
            {tr("defaultParameterPairs")}:{" "}
            {DEFAULT_SENSITIVITY_PAIRS.map((pair) => `${pair.short} / ${pair.long}`).join(", ")}
          </p>
        </div>

        <div className="form-grid">
          <label className="form-field">
            <span className="form-label">{tr("ticker")}</span>
            <input
              className="form-input"
              type="text"
              value={sensitivityTicker}
              onChange={(e) => setSensitivityTicker(e.target.value.toUpperCase())}
              placeholder="AAPL"
            />
          </label>

          <label className="form-field">
            <span className="form-label">{tr("backtestStartDate")}</span>
            <input
              className="form-input"
              type="date"
              value={sensitivityStartDate}
              onChange={(e) => setSensitivityStartDate(e.target.value)}
            />
          </label>

          <label className="form-field">
            <span className="form-label">{tr("backtestEndDate")}</span>
            <input
              className="form-input"
              type="date"
              value={sensitivityEndDate}
              onChange={(e) => setSensitivityEndDate(e.target.value)}
            />
          </label>

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
              value={sensitivityTransactionCost}
              onChange={(e) => setSensitivityTransactionCost(e.target.value)}
            />
          </label>
        </div>

        <Button onClick={handleRunSensitivityAnalysis} disabled={sensitivityLoading}>
          {sensitivityLoading ? tr("running") : tr("runSensitivityAnalysis")}
        </Button>

        {sensitivityError && <ErrorAlert message={sensitivityError} />}

        {sensitivityResult && (() => {
          const sortedResults = sortSensitivityResults(sensitivityResult.results);
          const interpretationSentences = generateSensitivityInterpretation(
            sensitivityResult,
            language
          );
          const bestSharpe = sortedResults.reduce<number | null>((best, row) => {
            if (row.sharpe_ratio == null) {
              return best;
            }
            if (best == null || row.sharpe_ratio > best) {
              return row.sharpe_ratio;
            }
            return best;
          }, null);

          return (
            <>
              <p className="section-meta">
                {sensitivityResult.ticker} ·{" "}
                {translateStrategyName(language, sensitivityResult.strategy)} ·{" "}
                {sensitivityResult.start_date} → {sensitivityResult.end_date ?? tr("latest")}
                {" · "}
                {tr("dataSource")}: {translateDataSource(language, sensitivityResult.data_source)}
              </p>

              <DataTable className="table-scroll">
                <thead>
                  <tr>
                    <th className="num">{tr("shortMa")}</th>
                    <th className="num">{tr("longMa")}</th>
                    <th className="num">{tr("totalReturn")}</th>
                    <th className="num">{tr("benchmarkReturn")}</th>
                    <th className="num">{tr("cagr")}</th>
                    <th className="num">{tr("sharpe")}</th>
                    <th className="num">{tr("strategyMaxDd")}</th>
                    <th className="num">{tr("benchmarkMaxDd")}</th>
                    <th className="num">{tr("volatility")}</th>
                    <th className="num">{tr("trades")}</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedResults.map((row) => {
                    const isBestSharpe =
                      bestSharpe != null &&
                      row.sharpe_ratio != null &&
                      row.sharpe_ratio === bestSharpe;
                    return (
                      <tr
                        key={`${row.short_window}-${row.long_window}`}
                        className={isBestSharpe ? "is-highlight" : undefined}
                      >
                        <td className="num">{row.short_window}</td>
                        <td className="num">{row.long_window}</td>
                        <td className="num">{formatMetricPercent(row.total_return)}</td>
                        <td className="num">{formatMetricPercent(row.benchmark_return)}</td>
                        <td className="num">{formatMetricPercent(row.cagr)}</td>
                        <td className="num">{formatMetricSharpe(row.sharpe_ratio)}</td>
                        <td className="num">
                          {formatMetricPercent(row.strategy_max_drawdown ?? row.max_drawdown)}
                        </td>
                        <td className="num">
                          {formatMetricPercent(row.benchmark_max_drawdown)}
                        </td>
                        <td className="num">{formatMetricPercent(row.volatility)}</td>
                        <td className="num">{formatMetricTrades(row.number_of_trades)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </DataTable>

              {sensitivityResult.errors.length > 0 && (
                <>
                  <SectionHeader title={tr("parameterSetErrors")} />
                  <ul className="interpretation-panel__list">
                    {sensitivityResult.errors.map((item) => (
                      <li key={`${item.short_window}-${item.long_window}`}>
                        {item.short_window} / {item.long_window}: {item.error}
                      </li>
                    ))}
                  </ul>
                </>
              )}

              <InterpretationPanel
                title={tr("sensitivityInterpretation")}
                sentences={interpretationSentences}
                note={tr("sensitivityInterpretationNote")}
              />
            </>
          );
        })()}
      </SectionCard>

      <SectionCard id="oos-validation">
        <SectionHeader title={tr("oosValidation")} description={tr("oosDesc")} />

        <div className="form-grid">
          <label className="form-field">
            <span className="form-label">{tr("ticker")}</span>
            <input
              className="form-input"
              type="text"
              value={oosTicker}
              onChange={(e) => setOosTicker(e.target.value.toUpperCase())}
              placeholder="AAPL"
            />
          </label>

          <label className="form-field">
            <span className="form-label">{tr("backtestStartDate")}</span>
            <input
              className="form-input"
              type="date"
              value={oosStartDate}
              onChange={(e) => setOosStartDate(e.target.value)}
            />
          </label>

          <label className="form-field">
            <span className="form-label">{tr("splitDate")}</span>
            <input
              className="form-input"
              type="date"
              value={oosSplitDate}
              onChange={(e) => setOosSplitDate(e.target.value)}
            />
          </label>

          <label className="form-field">
            <span className="form-label">{tr("backtestEndDate")}</span>
            <input
              className="form-input"
              type="date"
              value={oosEndDate}
              onChange={(e) => setOosEndDate(e.target.value)}
            />
          </label>

          <label className="form-field">
            <span className="form-label">{tr("shortWindow")}</span>
            <input
              className="form-input"
              type="number"
              min={2}
              value={oosShortWindow}
              onChange={(e) => setOosShortWindow(Number(e.target.value))}
            />
          </label>

          <label className="form-field">
            <span className="form-label">{tr("longWindow")}</span>
            <input
              className="form-input"
              type="number"
              min={3}
              value={oosLongWindow}
              onChange={(e) => setOosLongWindow(Number(e.target.value))}
            />
          </label>

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
              value={oosTransactionCost}
              onChange={(e) => setOosTransactionCost(e.target.value)}
            />
          </label>
        </div>

        <Button onClick={handleRunOOSValidation} disabled={oosLoading}>
          {oosLoading ? tr("running") : tr("runOosValidation")}
        </Button>

        {oosError && <ErrorAlert message={oosError} />}

        {oosResult && (
          <>
            <p className="section-meta">
              {oosResult.ticker} · {translateStrategyName(language, oosResult.strategy)} ·{" "}
              {oosResult.start_date} → {oosResult.end_date ?? tr("latest")} · {tr("split")}:{" "}
              {oosResult.split_date}
              {" · "}
              {tr("dataSource")}: {translateDataSource(language, oosResult.data_source)}
            </p>

            <DataTable className="table-scroll">
              <thead>
                <tr>
                  <th>{tr("metric")}</th>
                  {(Object.keys(oosSegmentLabels) as OOSSegmentKey[]).map((key) => {
                    const segment = oosResult.segments[key];
                    return (
                      <th key={key} className="num">
                        <span className={key === "out_of_sample" ? "oos-primary-label" : ""}>
                          {oosSegmentLabels[key]}
                        </span>
                        <div className="helper-text">
                          {segment.period_start} → {segment.period_end}
                        </div>
                      </th>
                    );
                  })}
                </tr>
              </thead>
              <tbody>
                {oosMetricRows.map((row) => (
                  <tr key={row.key}>
                    <td>{row.label}</td>
                    {(Object.keys(oosSegmentLabels) as OOSSegmentKey[]).map((segmentKey) => {
                      const value = getOOSMetricValue(
                        oosResult.segments[segmentKey].metrics,
                        row.key
                      );
                      let formatted = tr("na");
                      if (row.format === "percent") {
                        formatted = formatMetricPercent(value);
                      } else if (row.format === "sharpe") {
                        formatted = formatMetricSharpe(value);
                      } else {
                        formatted = formatMetricTrades(value);
                      }
                      return (
                        <td
                          key={segmentKey}
                          className={`num${segmentKey === "out_of_sample" ? " is-primary-check" : ""}`}
                        >
                          {formatted}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </DataTable>

            <InterpretationPanel
              title={tr("oosInterpretation")}
              sentences={translateOOSInterpretation(language, oosResult.interpretation)}
              note={tr("oosInterpretationNote")}
            />
          </>
        )}
      </SectionCard>
    </AppShell>
  );
}
