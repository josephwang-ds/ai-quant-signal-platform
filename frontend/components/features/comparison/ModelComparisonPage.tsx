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
import ModelComparisonInsightPanels from "@/components/features/comparison/ModelComparisonInsightPanels";
import ModelComparisonPreprocessingPanel from "@/components/features/comparison/ModelComparisonPreprocessingPanel";
import {
  explainModelComparison,
  runModelComparison,
  type ModelComparisonPreprocessingMethod,
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
  translateModelFeatureName,
  type TranslationKey,
} from "@/lib/i18n";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

const DEFAULT_TICKER = "SPY";
const DEFAULT_START_DATE = "2020-01-01";
const DEFAULT_SPLIT_DATE = "2022-01-01";
const DEFAULT_N_FOLDS = 4;
const DEFAULT_SHORT_WINDOW = 20;
const DEFAULT_LONG_WINDOW = 60;
const DEFAULT_MOMENTUM_WINDOW = 60;
const DEFAULT_TRANSACTION_COST = 0.001;

type ComparisonMode = "single_split" | "walk_forward";

type ModelOption = {
  id: string;
  labelKey: TranslationKey;
  defaultSelected?: boolean;
};

type ModelGroup = {
  id: string;
  labelKey: TranslationKey;
  options: ModelOption[];
};

const MODEL_GROUPS: ModelGroup[] = [
  {
    id: "linear",
    labelKey: "modelGroupLinear",
    options: [
      { id: "logistic_l2", labelKey: "modelOptionLogisticL2", defaultSelected: true },
      { id: "logistic_l1", labelKey: "modelOptionLogisticL1" },
      { id: "logistic_en", labelKey: "modelOptionLogisticEn" },
      { id: "ridge_clf", labelKey: "modelOptionRidgeClf" },
    ],
  },
  {
    id: "trees",
    labelKey: "modelGroupTrees",
    options: [
      { id: "random_forest", labelKey: "modelOptionRandomForest", defaultSelected: true },
      { id: "xgboost", labelKey: "modelOptionXgboost", defaultSelected: true },
      { id: "lightgbm", labelKey: "modelOptionLightgbm", defaultSelected: true },
    ],
  },
  {
    id: "svm",
    labelKey: "modelGroupSvm",
    options: [{ id: "svm", labelKey: "modelOptionSvm" }],
  },
  {
    id: "regression",
    labelKey: "modelGroupRegressionSign",
    options: [
      { id: "ridge_reg", labelKey: "modelOptionRidgeReg", defaultSelected: true },
      { id: "lasso_reg", labelKey: "modelOptionLassoReg" },
      { id: "elasticnet_reg", labelKey: "modelOptionElasticNetReg" },
    ],
  },
  {
    id: "timeseries",
    labelKey: "modelGroupTimeseries",
    options: [{ id: "arima", labelKey: "modelOptionArima" }],
  },
  {
    id: "offline_dl",
    labelKey: "modelGroupOfflineDl",
    options: [
      { id: "cnn", labelKey: "modelOptionCnn" },
      { id: "lstm", labelKey: "modelOptionLstm" },
      { id: "rl", labelKey: "modelOptionRl" },
    ],
  },
];

const DEFAULT_SELECTED_MODELS = MODEL_GROUPS.flatMap((group) =>
  group.options.filter((option) => option.defaultSelected).map((option) => option.id)
);

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
  const [comparisonMode, setComparisonMode] =
    useState<ComparisonMode>("single_split");
  const [splitDate, setSplitDate] = useState(DEFAULT_SPLIT_DATE);
  const [nFolds, setNFolds] = useState(DEFAULT_N_FOLDS);
  const [shortWindow, setShortWindow] = useState(DEFAULT_SHORT_WINDOW);
  const [longWindow, setLongWindow] = useState(DEFAULT_LONG_WINDOW);
  const [momentumWindow, setMomentumWindow] = useState(DEFAULT_MOMENTUM_WINDOW);
  const [transactionCost, setTransactionCost] = useState(
    String(DEFAULT_TRANSACTION_COST)
  );
  const [selectedModels, setSelectedModels] = useState<string[]>(
    DEFAULT_SELECTED_MODELS
  );
  const [preprocessing, setPreprocessing] =
    useState<ModelComparisonPreprocessingMethod>("none");
  const [pcaComponents, setPcaComponents] = useState(5);
  const [selectK, setSelectK] = useState(10);
  const [tune, setTune] = useState(false);
  const [result, setResult] = useState<ModelComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resultsView, setResultsView] = useState<"charts" | "table">("charts");
  const [explaining, setExplaining] = useState(false);
  const [copilotExplanation, setCopilotExplanation] = useState<string | null>(
    null
  );

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
    const parsedNFolds = Number(nFolds);
    const isWalkForward = comparisonMode === "walk_forward";

    if (!normalizedTicker) {
      setError(tr("tickerEmpty"));
      return;
    }
    if (!isWalkForward && !splitDate) {
      setError(tr("modelComparisonSplitRequired"));
      return;
    }
    if (isWalkForward && (!Number.isFinite(parsedNFolds) || parsedNFolds < 2)) {
      setError(tr("modelComparisonNFoldsInvalid"));
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
    setCopilotExplanation(null);

    try {
      const response = await runModelComparison({
        ticker: normalizedTicker,
        start_date: startDate,
        end_date: endDate || undefined,
        transaction_cost: parsedTransactionCost,
        short_window: parsedShortWindow,
        long_window: parsedLongWindow,
        momentum_window: parsedMomentumWindow,
        models: selectedModels,
        include_lstm: selectedModels.includes("lstm"),
        tune,
        preprocessing,
        ...(preprocessing === "pca"
          ? { pca_components: Number(pcaComponents) }
          : {}),
        ...(preprocessing === "select_kbest" ? { select_k: Number(selectK) } : {}),
        ...(isWalkForward
          ? { n_folds: parsedNFolds, scheme: "expanding" as const }
          : { split_date: splitDate }),
      });
      setResult(response);
      setResultsView("charts");
    } catch (err) {
      setError(getApiDisplayMessage(err, tr("modelComparisonFailed")));
    } finally {
      setLoading(false);
    }
  }

  const resultIsWalkForward = result?.mode === "walk_forward";
  const oosStart = result?.oos_start ?? result?.test_start;
  const oosEnd = result?.oos_end ?? result?.test_end;

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

      <div className="model-comparison-mode" role="group" aria-label={tr("modelComparisonMode")}>
        <span className="form-label">{tr("modelComparisonMode")}</span>
        <div className="model-comparison-view-toggle">
          <button
            type="button"
            className={`model-comparison-view-toggle__btn${
              comparisonMode === "single_split" ? " is-active" : ""
            }`}
            aria-pressed={comparisonMode === "single_split"}
            onClick={() => setComparisonMode("single_split")}
          >
            {tr("modelComparisonModeSingleSplit")}
          </button>
          <button
            type="button"
            className={`model-comparison-view-toggle__btn${
              comparisonMode === "walk_forward" ? " is-active" : ""
            }`}
            aria-pressed={comparisonMode === "walk_forward"}
            onClick={() => setComparisonMode("walk_forward")}
          >
            {tr("modelComparisonModeWalkForward")}
          </button>
        </div>
      </div>

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

        {comparisonMode === "single_split" ? (
          <label className="form-field">
            <span className="form-label">{tr("modelComparisonSplitDate")}</span>
            <input
              className="form-input"
              type="date"
              value={splitDate}
              onChange={(e) => setSplitDate(e.target.value)}
            />
          </label>
        ) : (
          <label className="form-field">
            <span className="form-label">{tr("modelComparisonNFolds")}</span>
            <input
              className="form-input"
              type="number"
              min={2}
              max={12}
              value={nFolds}
              onChange={(e) => setNFolds(Number(e.target.value))}
            />
          </label>
        )}

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
        <div className="model-comparison-models__groups">
          {MODEL_GROUPS.map((group) => (
            <div key={group.id} className="model-comparison-models__group">
              <p className="model-comparison-models__group-label">
                {tr(group.labelKey)}
              </p>
              <div className="model-comparison-models__grid">
                {group.options.map((option) => (
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
            </div>
          ))}
        </div>
      </fieldset>

      <div className="form-grid">
        <label className="form-field">
          <span className="form-label">{tr("modelComparisonPreprocessing")}</span>
          <select
            className="form-select"
            value={preprocessing}
            onChange={(e) =>
              setPreprocessing(e.target.value as ModelComparisonPreprocessingMethod)
            }
          >
            <option value="none">{tr("modelComparisonPreprocessingNone")}</option>
            <option value="pca">{tr("modelComparisonPreprocessingPca")}</option>
            <option value="select_kbest">
              {tr("modelComparisonPreprocessingSelectKBest")}
            </option>
            <option value="l1_select">
              {tr("modelComparisonPreprocessingL1")}
            </option>
          </select>
        </label>

        {preprocessing === "pca" ? (
          <label className="form-field">
            <span className="form-label">
              {tr("modelComparisonPcaComponents")}
            </span>
            <input
              className="form-input"
              type="number"
              min={1}
              max={30}
              value={pcaComponents}
              onChange={(e) => setPcaComponents(Number(e.target.value))}
            />
          </label>
        ) : null}

        {preprocessing === "select_kbest" ? (
          <label className="form-field">
            <span className="form-label">{tr("modelComparisonSelectK")}</span>
            <input
              className="form-input"
              type="number"
              min={1}
              max={30}
              value={selectK}
              onChange={(e) => setSelectK(Number(e.target.value))}
            />
          </label>
        ) : null}

        <label className="form-field model-comparison-tune">
          <span className="form-label">{tr("modelComparisonTune")}</span>
          <label className="model-comparison-tune__check">
            <input
              type="checkbox"
              checked={tune}
              onChange={(e) => setTune(e.target.checked)}
            />
            {tr("modelComparisonTuneHint")}
          </label>
        </label>
      </div>

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
            {oosStart} – {oosEnd}
            <span className="model-comparison-window__note">
              {" "}
              ·{" "}
              {resultIsWalkForward
                ? tr("modelComparisonWalkForwardOosNote").replace(
                    "{n}",
                    String(result.n_folds ?? result.folds?.length ?? nFolds)
                  )
                : tr("modelComparisonSameOosNote")}
            </span>
          </p>

          <ModelComparisonInsightPanels
            result={result}
            explaining={explaining}
            copilotExplanation={copilotExplanation}
            onExplain={async () => {
              setExplaining(true);
              try {
                const explained = await explainModelComparison({
                  summary: result.summary,
                  results: result.results,
                  mode: result.mode,
                });
                setCopilotExplanation(explained.explanation);
              } catch (err) {
                setError(
                  getApiDisplayMessage(err, tr("modelComparisonExplainFailed"))
                );
              } finally {
                setExplaining(false);
              }
            }}
          />

          {result.feature_set && result.feature_set.columns.length > 0 ? (
            <details className="model-comparison-feature-set">
              <summary>
                {tr("modelComparisonFeaturesUsed")}
                <span className="model-comparison-feature-set__count">
                  {tr("modelComparisonFeaturesUsedCount").replace(
                    "{n}",
                    String(result.feature_set.count)
                  )}
                </span>
              </summary>
              <p className="model-comparison-feature-set__hint">
                {tr("modelComparisonFeaturesUsedHint")}
              </p>
              <ul className="model-comparison-feature-set__list">
                {result.feature_set.columns.map((column) => (
                  <li key={column}>
                    <code className="model-comparison-feature-set__code">
                      {column}
                    </code>
                    <span className="model-comparison-feature-set__label">
                      {translateModelFeatureName(language, column)}
                    </span>
                  </li>
                ))}
              </ul>
            </details>
          ) : null}

          {result.preprocessing ? (
            <ModelComparisonPreprocessingPanel
              preprocessing={result.preprocessing}
              language={language}
              labels={{
                title: tr("modelComparisonPreprocessingResult"),
                methodNone: tr("modelComparisonPreprocessingNone"),
                methodPca: tr("modelComparisonPreprocessingPca"),
                methodSelectKBest: tr("modelComparisonPreprocessingSelectKBest"),
                methodL1: tr("modelComparisonPreprocessingL1"),
                pcaCaption: tr("modelComparisonPcaCaption"),
                pcaCumulative: tr("modelComparisonPcaCumulative"),
                selectedTitle: tr("modelComparisonSelectedFeatures"),
                droppedTitle: tr("modelComparisonDroppedFeatures"),
                emptySelection: tr("modelComparisonSelectionEmpty"),
              }}
            />
          ) : null}

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
                foldStabilityTitle: tr("modelComparisonFoldStabilityTitle"),
                foldStabilityEmpty: tr("modelComparisonFoldStabilityEmpty"),
                foldStabilityYSharpe: tr("modelComparisonFoldStabilitySharpe"),
                foldStabilityYAccuracy: tr("modelComparisonFoldStabilityAccuracy"),
                foldIndexLabel: tr("modelComparisonFoldIndex"),
                offlineBadge: tr("modelComparisonOfflineBadge"),
                offlineBadgeWithDate: tr("modelComparisonOfflineBadgeWithDate"),
                offlineTooltip: tr("modelComparisonOfflineTooltip"),
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
                      {row.source === "offline_artifact" ||
                      row.strategy === "lstm" ||
                      row.strategy === "cnn" ||
                      row.strategy === "rl" ? (
                        <span
                          className="model-comparison-offline-badge"
                          title={
                            row.strategy === "rl"
                              ? tr("modelComparisonRlTooltip")
                              : tr("modelComparisonOfflineTooltip")
                          }
                        >
                          {row.strategy === "rl"
                            ? tr("modelComparisonRlBadge")
                            : row.trained_at
                              ? tr("modelComparisonOfflineBadgeWithDate").replace(
                                  "{date}",
                                  row.trained_at.slice(0, 10)
                                )
                              : tr("modelComparisonOfflineBadge")}
                        </span>
                      ) : null}
                      {row.tuned && row.best_params ? (
                        <span
                          className="model-comparison-tune-badge"
                          title={JSON.stringify(row.best_params)}
                        >
                          {tr("modelComparisonTunedBadge")}
                        </span>
                      ) : null}
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
