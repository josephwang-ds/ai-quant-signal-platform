"use client";

import { useState } from "react";
import AppShell from "@/components/layout/AppShell";
import Button from "@/components/ui/Button";
import DataTable from "@/components/ui/DataTable";
import ErrorAlert from "@/components/ui/ErrorAlert";
import InterpretationPanel from "@/components/ui/InterpretationPanel";
import MetricCard from "@/components/ui/MetricCard";
import SectionCard from "@/components/ui/SectionCard";
import SectionHeader from "@/components/ui/SectionHeader";
import { runStrategyComparison } from "@/lib/api";
import {
  formatMetricPercent,
  formatMetricSharpe,
  formatMetricTrades,
} from "@/lib/formatters";
import {
  translateComparisonInterpretation,
  translateComparisonLabel,
} from "@/lib/i18n";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";
import type {
  StrategyComparisonResponse,
  StrategyComparisonResult,
  StrategyComparisonSummary,
} from "@/types/market";

const DEFAULT_CHART_START_DATE = "2022-01-01";
const DEFAULT_COMPARISON_TICKER = "AAPL";
const DEFAULT_SHORT_WINDOW = 20;
const DEFAULT_LONG_WINDOW = 60;
const DEFAULT_MOMENTUM_WINDOW = 60;
const DEFAULT_TRANSACTION_COST = 0.001;

function isComparisonRowHighlighted(
  row: StrategyComparisonResult,
  summary: StrategyComparisonSummary
): boolean {
  return (
    row.label === summary.best_total_return ||
    row.label === summary.best_sharpe ||
    row.label === summary.lowest_drawdown
  );
}

export default function StrategyComparisonPage() {
  const { language, setLanguage, tr } = useWorkspaceLanguage();
  const [comparisonTicker, setComparisonTicker] = useState(DEFAULT_COMPARISON_TICKER);
  const [comparisonStartDate, setComparisonStartDate] = useState(DEFAULT_CHART_START_DATE);
  const [comparisonEndDate, setComparisonEndDate] = useState("");
  const [comparisonShortWindow, setComparisonShortWindow] = useState(DEFAULT_SHORT_WINDOW);
  const [comparisonLongWindow, setComparisonLongWindow] = useState(DEFAULT_LONG_WINDOW);
  const [comparisonMomentumWindow, setComparisonMomentumWindow] = useState(
    DEFAULT_MOMENTUM_WINDOW
  );
  const [comparisonTransactionCost, setComparisonTransactionCost] = useState(
    String(DEFAULT_TRANSACTION_COST)
  );
  const [comparisonResult, setComparisonResult] = useState<StrategyComparisonResponse | null>(
    null
  );
  const [comparisonLoading, setComparisonLoading] = useState(false);
  const [comparisonError, setComparisonError] = useState<string | null>(null);

  async function handleCompareStrategies() {
    const normalizedTicker = comparisonTicker.trim().toUpperCase();
    const parsedShortWindow = Number(comparisonShortWindow);
    const parsedLongWindow = Number(comparisonLongWindow);
    const parsedMomentumWindow = Number(comparisonMomentumWindow);
    const parsedTransactionCost = Number(comparisonTransactionCost);

    if (!normalizedTicker) {
      setComparisonError(tr("tickerEmpty"));
      return;
    }

    if (!Number.isFinite(parsedShortWindow) || !Number.isFinite(parsedLongWindow)) {
      setComparisonError(tr("shortLongInvalid"));
      return;
    }

    if (parsedShortWindow >= parsedLongWindow) {
      setComparisonError(tr("shortLessThanLong"));
      return;
    }

    if (!Number.isFinite(parsedMomentumWindow)) {
      setComparisonError(tr("momentumInvalid"));
      return;
    }

    if (parsedMomentumWindow < 5 || parsedMomentumWindow > 252) {
      setComparisonError(tr("momentumRange"));
      return;
    }

    if (!Number.isFinite(parsedTransactionCost) || parsedTransactionCost < 0) {
      setComparisonError(tr("transactionCostInvalid"));
      return;
    }

    setComparisonLoading(true);
    setComparisonError(null);
    setComparisonResult(null);

    try {
      const response = await runStrategyComparison({
        ticker: normalizedTicker,
        start_date: comparisonStartDate,
        end_date: comparisonEndDate || undefined,
        transaction_cost: parsedTransactionCost,
        short_window: parsedShortWindow,
        long_window: parsedLongWindow,
        momentum_window: parsedMomentumWindow,
      });
      setComparisonResult(response);
    } catch (error) {
      setComparisonError(
        error instanceof Error ? error.message : tr("strategyComparisonFailed")
      );
    } finally {
      setComparisonLoading(false);
    }
  }

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <SectionCard>
        <SectionHeader
          title={tr("strategyComparison")}
          description={tr("strategyComparisonDesc")}
        />

        <ul className="system-notes-list">
          <li>{tr("strategyComparisonDisclaimer1")}</li>
          <li>{tr("strategyComparisonDisclaimer2")}</li>
          <li>{tr("strategyComparisonDisclaimer3")}</li>
        </ul>

        <div className="form-grid">
          <label className="form-field">
            <span className="form-label">{tr("ticker")}</span>
            <input
              className="form-input"
              type="text"
              value={comparisonTicker}
              onChange={(e) => setComparisonTicker(e.target.value.toUpperCase())}
              placeholder="AAPL"
            />
          </label>

          <label className="form-field">
            <span className="form-label">{tr("backtestStartDate")}</span>
            <input
              className="form-input"
              type="date"
              value={comparisonStartDate}
              onChange={(e) => setComparisonStartDate(e.target.value)}
            />
          </label>

          <label className="form-field">
            <span className="form-label">{tr("backtestEndDate")}</span>
            <input
              className="form-input"
              type="date"
              value={comparisonEndDate}
              onChange={(e) => setComparisonEndDate(e.target.value)}
            />
          </label>

          <label className="form-field">
            <span className="form-label">{tr("shortWindow")}</span>
            <input
              className="form-input"
              type="number"
              min={2}
              value={comparisonShortWindow}
              onChange={(e) => setComparisonShortWindow(Number(e.target.value))}
            />
          </label>

          <label className="form-field">
            <span className="form-label">{tr("longWindow")}</span>
            <input
              className="form-input"
              type="number"
              min={3}
              value={comparisonLongWindow}
              onChange={(e) => setComparisonLongWindow(Number(e.target.value))}
            />
          </label>

          <label className="form-field">
            <span className="form-label">{tr("momentumWindow")}</span>
            <input
              className="form-input"
              type="number"
              min={5}
              max={252}
              value={comparisonMomentumWindow}
              onChange={(e) => setComparisonMomentumWindow(Number(e.target.value))}
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
              value={comparisonTransactionCost}
              onChange={(e) => setComparisonTransactionCost(e.target.value)}
            />
          </label>
        </div>

        <Button onClick={handleCompareStrategies} disabled={comparisonLoading}>
          {comparisonLoading ? tr("running") : tr("compareStrategies")}
        </Button>

        {comparisonError && <ErrorAlert message={comparisonError} />}

        {comparisonResult && (
          <>
            <div className="metric-grid">
              <MetricCard
                label={tr("bestTotalReturn")}
                value={translateComparisonLabel(
                  language,
                  comparisonResult.summary.best_total_return ?? tr("na")
                )}
                featured
              />
              <MetricCard
                label={tr("bestSharpe")}
                value={translateComparisonLabel(
                  language,
                  comparisonResult.summary.best_sharpe ?? tr("na")
                )}
                featured
              />
              <MetricCard
                label={tr("lowestDrawdown")}
                value={translateComparisonLabel(
                  language,
                  comparisonResult.summary.lowest_drawdown ?? tr("na")
                )}
                featured
              />
              <MetricCard
                label={tr("fewestTrades")}
                value={translateComparisonLabel(
                  language,
                  comparisonResult.summary.fewest_trades ?? tr("na")
                )}
              />
            </div>

            <InterpretationPanel
              title={tr("strategyComparison")}
              sentences={translateComparisonInterpretation(
                language,
                comparisonResult.interpretation
              )}
              note={tr("strategyComparisonExplain")}
            />

            <DataTable className="table-scroll">
              <thead>
                <tr>
                  <th>{tr("comparisonColStrategy")}</th>
                  <th className="num">{tr("totalReturn")}</th>
                  <th className="num">{tr("comparisonColBenchmark")}</th>
                  <th className="num">{tr("cagr")}</th>
                  <th className="num">{tr("sharpe")}</th>
                  <th className="num">{tr("comparisonColMaxDrawdown")}</th>
                  <th className="num">{tr("comparisonColTrades")}</th>
                  <th className="num">{tr("transactionCostTotal")}</th>
                </tr>
              </thead>
              <tbody>
                {comparisonResult.results.map((row) => (
                  <tr
                    key={`${row.strategy}-${row.label}`}
                    className={
                      isComparisonRowHighlighted(row, comparisonResult.summary)
                        ? "is-highlight"
                        : undefined
                    }
                  >
                    <td>{translateComparisonLabel(language, row.label)}</td>
                    <td className="num">{formatMetricPercent(row.metrics.total_return)}</td>
                    <td className="num">
                      {formatMetricPercent(row.metrics.benchmark_return)}
                    </td>
                    <td className="num">{formatMetricPercent(row.metrics.cagr)}</td>
                    <td className="num">{formatMetricSharpe(row.metrics.sharpe_ratio)}</td>
                    <td className="num">
                      {formatMetricPercent(
                        row.metrics.strategy_max_drawdown ?? row.metrics.max_drawdown
                      )}
                    </td>
                    <td className="num">
                      {formatMetricTrades(row.metrics.number_of_trades)}
                    </td>
                    <td className="num">
                      {formatMetricPercent(row.metrics.transaction_cost_total)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
          </>
        )}
      </SectionCard>
    </AppShell>
  );
}
