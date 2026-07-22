"use client";

import { useState } from "react";
import Button from "@/components/ui/Button";
import DataTable from "@/components/ui/DataTable";
import EmptyState from "@/components/ui/EmptyState";
import ErrorAlert from "@/components/ui/ErrorAlert";
import InterpretationPanel from "@/components/ui/InterpretationPanel";
import LoadingState from "@/components/ui/LoadingState";
import MetricSummaryCard from "@/components/ui/MetricSummaryCard";
import SectionCard from "@/components/ui/SectionCard";
import SectionHeader from "@/components/ui/SectionHeader";
import ModelComparisonCharts from "@/components/features/comparison/ModelComparisonCharts";
import {
  runModelComparison,
  type ModelComparisonResponse,
  type ModelComparisonResult,
  type ModelComparisonSummary,
} from "@/lib/api";
import { getApiDisplayMessage } from "@/lib/apiRequest";
import {
  formatMetricPercent,
  formatMetricSharpe,
  formatMetricTrades,
} from "@/lib/formatters";
import {
  translateComparisonLabel,
  translateModelComparisonInterpretation,
  type TranslationKey,
} from "@/lib/i18n";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

const DEFAULT_TICKER = "SPY";
const DEFAULT_START_DATE = "2020-01-01";
const DEFAULT_SPLIT_DATE = "2022-01-01";
const DEFAULT_SHORT_WINDOW = 20;
const DEFAULT_LONG_WINDOW = 60;
const DEFAULT_MOMENTUM_WINDOW = 60;
const DEFAULT_TRANSACTION_COST = 0.001;

const MODEL_OPTIONS: Array<{ id: string; labelKey: TranslationKey }> = [
  { id: "logistic", labelKey: "modelOptionLogistic" },
  { id: "random_forest", labelKey: "modelOptionRandomForest" },
  { id: "xgboost", labelKey: "modelOptionXgboost" },
  { id: "lightgbm", labelKey: "modelOptionLightgbm" },
];

function isRowHighlighted(
  row: ModelComparisonResult,
  summary: ModelComparisonSummary
): boolean {
  return (
    row.label === summary.best_total_return ||
    row.label === summary.best_sharpe ||
    row.label === summary.lowest_drawdown ||
    row.label === summary.fewest_trades
  );
}

function summaryMark(
  row: ModelComparisonResult,
  summary: ModelComparisonSummary,
  field: keyof ModelComparisonSummary
): string {
  return row.label === summary[field] ? " ★" : "";
}

export default function ModelComparisonPage() {
  const { language, tr } = useWorkspaceLanguage();
  const [ticker, setTicker] = useState(DEFAULT_TICKER);
  const [startDate, setStartDate] = useState(DEFAULT_START_DATE);
  const [endDate, setEndDate] = useState("");
  const [splitDate, setSplitDate] = useState(DEFAULT_SPLIT_DATE);
  const [shortWindow, setShortWindow] = useState(DEFAULT_SHORT_WINDOW);
  const [longWindow, setLongWindow] = useState(DEFAULT_LONG_WINDOW);
  const [momentumWindow, setMomentumWindow] = useState(DEFAULT_MOMENTUM_WINDOW);
  const [transactionCost, setTransactionCost] = useState(
    String(DEFAULT_TRANSACTION_COST)
  );
  const [selectedModels, setSelectedModels] = useState<string[]>(
    MODEL_OPTIONS.map((item) => item.id)
  );
  const [result, setResult] = useState<ModelComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resultsView, setResultsView] = useState<"charts" | "table">("charts");

  function toggleModel(id: string) {
    setSelectedModels((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  }

  async function handleCompare() {
    const normalizedTicker = ticker.trim().toUpperCase();
    const parsedShortWindow = Number(shortWindow);
    const parsedLongWindow = Number(longWindow);
    const parsedMomentumWindow = Number(momentumWindow);
    const parsedTransactionCost = Number(transactionCost);

    if (!normalizedTicker) {
      setError(tr("tickerEmpty"));
      return;
    }
    if (!splitDate) {
      setError(tr("modelComparisonSplitRequired"));
      return;
    }
    if (parsedShortWindow >= parsedLongWindow) {
      setError(tr("shortLessThanLong"));
      return;
    }
    if (
      !Number.isFinite(parsedMomentumWindow) ||
      parsedMomentumWindow < 5 ||
      parsedMomentumWindow > 252
    ) {
      setError(tr("momentumRange"));
      return;
    }
    if (!Number.isFinite(parsedTransactionCost) || parsedTransactionCost < 0) {
      setError(tr("transactionCostInvalid"));
      return;
    }
    if (selectedModels.length === 0) {
      setError(tr("modelComparisonModelsRequired"));
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await runModelComparison({
        ticker: normalizedTicker,
        start_date: startDate,
        end_date: endDate || undefined,
        split_date: splitDate,
        transaction_cost: parsedTransactionCost,
        short_window: parsedShortWindow,
        long_window: parsedLongWindow,
        momentum_window: parsedMomentumWindow,
        models: selectedModels,
      });
      setResult(response);
      setResultsView("charts");
    } catch (err) {
      setError(getApiDisplayMessage(err, tr("modelComparisonFailed")));
    } finally {
      setLoading(false);
    }
  }

  return (
    <SectionCard>
      <SectionHeader
        title={tr("modelComparison")}
        description={tr("modelComparisonDesc")}
      />

      <ul className="system-notes-list">
        <li>{tr("modelComparisonDisclaimer1")}</li>
        <li>{tr("modelComparisonDisclaimer2")}</li>
        <li>{tr("modelComparisonDisclaimer3")}</li>
      </ul>

      <div className="form-grid">
        <label className="form-field">
          <span className="form-label">{tr("ticker")}</span>
          <input
            className="form-input"
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            placeholder="SPY"
          />
        </label>

        <label className="form-field">
          <span className="form-label">{tr("backtestStartDate")}</span>
          <input
            className="form-input"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </label>

        <label className="form-field">
          <span className="form-label">{tr("backtestEndDate")}</span>
          <input
            className="form-input"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </label>

        <label className="form-field">
          <span className="form-label">{tr("modelComparisonSplitDate")}</span>
          <input
            className="form-input"
            type="date"
            value={splitDate}
            onChange={(e) => setSplitDate(e.target.value)}
          />
        </label>

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

      <fieldset className="model-comparison-models">
        <legend className="form-label">{tr("modelComparisonModels")}</legend>
        <div className="model-comparison-models__grid">
          {MODEL_OPTIONS.map((option) => (
            <label key={option.id} className="model-comparison-models__item">
              <input
                type="checkbox"
                checked={selectedModels.includes(option.id)}
                onChange={() => toggleModel(option.id)}
              />
              <span>{tr(option.labelKey)}</span>
            </label>
          ))}
        </div>
      </fieldset>

      <Button onClick={handleCompare} disabled={loading}>
        {loading ? tr("running") : tr("modelComparisonRun")}
      </Button>

      {error && <ErrorAlert message={error} />}
      {loading && <LoadingState message={tr("toolResultsLoading")} />}
      {!loading && !result && !error && (
        <EmptyState
          title={tr("toolResultsEmptyTitle")}
          description={tr("toolResultsEmptyDescription")}
        />
      )}

      {result && (
        <>
          <p className="model-comparison-window" role="status">
            <strong>{tr("modelComparisonEvalWindow")}:</strong>{" "}
            {result.test_start} – {result.test_end}
            <span className="model-comparison-window__note">
              {" "}
              · {tr("modelComparisonSameOosNote")}
            </span>
          </p>

          <div className="metric-grid model-comparison-summary-metrics" role="list">
            <MetricSummaryCard
              label={tr("bestTotalReturn")}
              value={translateComparisonLabel(
                language,
                result.summary.best_total_return ?? tr("na")
              )}
              tone="emphasis"
            />
            <MetricSummaryCard
              label={tr("bestSharpe")}
              value={translateComparisonLabel(
                language,
                result.summary.best_sharpe ?? tr("na")
              )}
              tone="emphasis"
            />
            <MetricSummaryCard
              label={tr("lowestDrawdown")}
              value={translateComparisonLabel(
                language,
                result.summary.lowest_drawdown ?? tr("na")
              )}
              tone="emphasis"
            />
            <MetricSummaryCard
              label={tr("fewestTrades")}
              value={translateComparisonLabel(
                language,
                result.summary.fewest_trades ?? tr("na")
              )}
            />
          </div>

          <InterpretationPanel
            title={tr("modelComparisonHowToRead")}
            sentences={translateModelComparisonInterpretation(
              language,
              result.interpretation
            )}
            note={tr("modelComparisonExplain")}
          />

          <div className="model-comparison-results-toolbar">
            <div className="model-comparison-view-toggle" role="group">
              <button
                type="button"
                className={`model-comparison-view-toggle__btn${
                  resultsView === "charts" ? " is-active" : ""
                }`}
                aria-pressed={resultsView === "charts"}
                onClick={() => setResultsView("charts")}
              >
                {tr("modelComparisonViewCharts")}
              </button>
              <button
                type="button"
                className={`model-comparison-view-toggle__btn${
                  resultsView === "table" ? " is-active" : ""
                }`}
                aria-pressed={resultsView === "table"}
                onClick={() => setResultsView("table")}
              >
                {tr("modelComparisonViewTable")}
              </button>
            </div>
          </div>

          {resultsView === "charts" ? (
            <ModelComparisonCharts
              result={result}
              language={language}
              labels={{
                championSharpe: tr("modelComparisonBannerSharpe"),
                championReturn: tr("modelComparisonBannerReturn"),
                championDrawdown: tr("modelComparisonBannerDrawdown"),
                championModel: tr("modelComparisonChampionModel"),
                totalReturn: tr("totalReturn"),
                sharpe: tr("sharpe"),
                maxDrawdown: tr("comparisonColMaxDrawdown"),
                directionalAccuracy: tr("modelComparisonDirectionalAccuracy"),
                equityTitle: tr("modelComparisonEquityTitle"),
                equityEmpty: tr("modelComparisonEquityEmpty"),
                riskReturnTitle: tr("modelComparisonRiskReturnTitle"),
                riskReturnHint: tr("modelComparisonRiskReturnHint"),
                riskReturnX: tr("modelComparisonRiskReturnX"),
                riskReturnY: tr("modelComparisonRiskReturnY"),
                riskReturnEmpty: tr("modelComparisonRiskReturnEmpty"),
                rankTitle: tr("modelComparisonRankTitle"),
                rankSharpe: tr("modelComparisonRankSharpe"),
                rankReturn: tr("modelComparisonRankReturn"),
                rankDrawdown: tr("modelComparisonRankDrawdown"),
                featureFocusTitle: tr("modelComparisonFeatureFocusTitle"),
                featureEmpty: tr("modelComparisonFeatureEmpty"),
                kindMl: tr("modelComparisonKindMl"),
                kindRule: tr("modelComparisonKindRule"),
                na: tr("na"),
              }}
            />
          ) : (
            <DataTable>
              <thead>
                <tr>
                  <th>{tr("comparisonColStrategy")}</th>
                  <th>{tr("modelComparisonKind")}</th>
                  <th className="num">{tr("totalReturn")}</th>
                  <th className="num">{tr("sharpe")}</th>
                  <th className="num">{tr("comparisonColMaxDrawdown")}</th>
                  <th className="num">{tr("comparisonColTrades")}</th>
                  <th className="num">{tr("transactionCostTotal")}</th>
                  <th className="num">{tr("modelComparisonDirectionalAccuracy")}</th>
                </tr>
              </thead>
              <tbody>
                {result.results.map((row) => (
                  <tr
                    key={`${row.kind}-${row.strategy}-${row.label}`}
                    className={
                      isRowHighlighted(row, result.summary)
                        ? "is-highlight"
                        : undefined
                    }
                  >
                    <td>
                      {translateComparisonLabel(language, row.label)}
                      {summaryMark(row, result.summary, "best_total_return")}
                      {summaryMark(row, result.summary, "best_sharpe")}
                      {summaryMark(row, result.summary, "lowest_drawdown")}
                      {summaryMark(row, result.summary, "fewest_trades")}
                    </td>
                    <td>
                      {row.kind === "ml"
                        ? tr("modelComparisonKindMl")
                        : tr("modelComparisonKindRule")}
                    </td>
                    <td className="num">
                      {formatMetricPercent(row.metrics.total_return)}
                    </td>
                    <td className="num">
                      {formatMetricSharpe(row.metrics.sharpe_ratio)}
                    </td>
                    <td className="num">
                      {formatMetricPercent(
                        row.metrics.strategy_max_drawdown ?? row.metrics.max_drawdown
                      )}
                    </td>
                    <td className="num">
                      {formatMetricTrades(row.metrics.number_of_trades)}
                    </td>
                    <td className="num">
                      {formatMetricPercent(row.metrics.transaction_cost_total ?? null)}
                    </td>
                    <td className="num">
                      {row.kind === "ml" && row.directional_accuracy != null
                        ? formatMetricPercent(row.directional_accuracy)
                        : tr("na")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
          )}
        </>
      )}
    </SectionCard>
  );
}
