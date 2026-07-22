"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import Button from "@/components/ui/Button";
import DataTable from "@/components/ui/DataTable";
import EmptyState from "@/components/ui/EmptyState";
import ErrorAlert from "@/components/ui/ErrorAlert";
import LoadingState from "@/components/ui/LoadingState";
import MetricCard from "@/components/ui/MetricCard";
import SectionCard from "@/components/ui/SectionCard";
import SectionHeader from "@/components/ui/SectionHeader";
import StatusBadge, {
  passFailVariant,
  riskVariant,
  signalLabelVariant,
  trendVariant,
} from "@/components/ui/StatusBadge";
import { getIndicators, runCompareChart, runMarketWatch } from "@/lib/api";
import { getApiDisplayMessage } from "@/lib/apiRequest";
import {
  formatDateSeriesRange,
  formatPercent,
  formatPrice,
  formatRsi,
  formatScore,
  getReturnTone,
} from "@/lib/formatters";
import {
  formatMessage,
  getChartLabels,
  t,
  translateBackendText,
  translateComponentName,
  translateDataSource,
  translatePassFail,
  translateRisk,
  translateSignalLabel,
  translateTrend,
  type Language,
} from "@/lib/i18n";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";
import type {
  ChartMode,
  CompareChartResponse,
  IndicatorsResponse,
  MarketWatchResponse,
  SignalResult,
} from "@/types/market";

const PriceChart = dynamic(() => import("@/components/PriceChart"), {
  ssr: false,
  loading: () => <LoadingState message="Loading chart..." />,
});

const CompareChart = dynamic(() => import("@/components/CompareChart"), {
  ssr: false,
  loading: () => <LoadingState message="Loading chart..." />,
});

const DEFAULT_TICKERS = "AAPL, MSFT, NVDA, TSLA, SPY";
const DEFAULT_LOOKBACK_DAYS = 120;
const DEFAULT_CHART_START_DATE = "2022-01-01";
const LOOKBACK_OPTIONS = [90, 120, 252, 500];

function parseTickers(input: string): string[] {
  return input
    .split(/[,\s\n]+/)
    .map((ticker) => ticker.trim())
    .filter(Boolean);
}

function getSignalFieldGuide(lang: Language): string[] {
  return [
    t(lang, "fieldGuideScore"),
    t(lang, "fieldGuideLabel"),
    t(lang, "fieldGuideTrend"),
    t(lang, "fieldGuideRisk"),
  ];
}

function getDetailMetricHelp(lang: Language) {
  return {
    lastPrice: t(lang, "helpLastPrice"),
    ma20: t(lang, "helpMa20"),
    ma60: t(lang, "helpMa60"),
    distanceToMa20: t(lang, "helpDistanceMa20"),
    distanceToMa60: t(lang, "helpDistanceMa60"),
    dailyReturn: t(lang, "helpDailyReturn"),
    return20d: t(lang, "helpReturn20d"),
    return60d: t(lang, "helpReturn60d"),
    rsi14: t(lang, "helpRsi14"),
    volatility20d: t(lang, "helpVolatility20d"),
    volumeChange: t(lang, "helpVolumeChange"),
  };
}

function getChartModeOptions(lang: Language): { value: ChartMode; label: string }[] {
  return [
    { value: "selected", label: t(lang, "chartModeSelected") },
    { value: "compare", label: t(lang, "chartModeCompare") },
  ];
}

function getTrendStatus(signalScore: number): "Positive" | "Mixed" | "Weak" {
  if (signalScore >= 60) {
    return "Positive";
  }
  if (signalScore >= 40) {
    return "Mixed";
  }
  return "Weak";
}

function getRiskLevel(volatility20d: number): "High" | "Medium" | "Low" {
  if (volatility20d >= 0.6) {
    return "High";
  }
  if (volatility20d >= 0.35) {
    return "Medium";
  }
  return "Low";
}

export default function MarketWatchPage() {
  const { language, setLanguage, tr } = useWorkspaceLanguage();
  const marketWatchRequestIdRef = useRef(0);

  const [tickersInput, setTickersInput] = useState(DEFAULT_TICKERS);
  const [lookbackDays, setLookbackDays] = useState(DEFAULT_LOOKBACK_DAYS);
  const [chartStartDate, setChartStartDate] = useState(DEFAULT_CHART_START_DATE);
  const [chartEndDate, setChartEndDate] = useState("");
  const [chartMode, setChartMode] = useState<ChartMode>("selected");
  const [marketWatchResult, setMarketWatchResult] = useState<MarketWatchResponse | null>(null);
  const [marketWatchError, setMarketWatchError] = useState<string | null>(null);
  const [isMarketWatchLoading, setIsMarketWatchLoading] = useState(false);
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [indicatorData, setIndicatorData] = useState<IndicatorsResponse | null>(null);
  const [compareChartData, setCompareChartData] = useState<CompareChartResponse | null>(null);
  const [chartLoading, setChartLoading] = useState(false);
  const [indicatorError, setIndicatorError] = useState<string | null>(null);

  const chartLabels = getChartLabels(language);
  const detailMetricHelp = getDetailMetricHelp(language);
  const chartModeOptions = getChartModeOptions(language);
  const signalFieldGuide = getSignalFieldGuide(language);

  const selectedResult: SignalResult | undefined = marketWatchResult?.results.find(
    (item) => item.ticker === selectedTicker
  );

  async function handleRunMarketWatch() {
    const parsedTickers = parseTickers(tickersInput);
    const requestId = ++marketWatchRequestIdRef.current;

    setIsMarketWatchLoading(true);
    setMarketWatchError(null);
    setMarketWatchResult(null);
    setSelectedTicker(null);
    setIndicatorData(null);
    setCompareChartData(null);
    setIndicatorError(null);

    if (parsedTickers.length === 0) {
      setMarketWatchError(tr("enterOneTicker"));
      setIsMarketWatchLoading(false);
      return;
    }

    try {
      const response = await runMarketWatch(parsedTickers, lookbackDays);
      if (requestId !== marketWatchRequestIdRef.current) {
        return;
      }
      setMarketWatchResult(response);
      setSelectedTicker(response.results[0]?.ticker ?? null);
    } catch (error) {
      if (requestId !== marketWatchRequestIdRef.current) {
        return;
      }
      const message = getApiDisplayMessage(error, tr("marketWatchFailed"));
      setMarketWatchError(message);
      setMarketWatchResult(null);
      setSelectedTicker(null);
      setIndicatorData(null);
      setCompareChartData(null);
      setIndicatorError(null);
    } finally {
      if (requestId === marketWatchRequestIdRef.current) {
        setIsMarketWatchLoading(false);
      }
    }
  }

  async function fetchChartData() {
    if (!marketWatchResult) {
      return;
    }

    if (chartMode === "selected" && !selectedTicker) {
      return;
    }

    setChartLoading(true);
    setIndicatorError(null);
    setIndicatorData(null);
    setCompareChartData(null);

    try {
      if (chartMode === "selected" && selectedTicker) {
        const data = await getIndicators(
          selectedTicker,
          chartStartDate,
          chartEndDate || undefined
        );
        setIndicatorData(data);
      } else {
        const tickers = marketWatchResult.results.map((item) => item.ticker);
        const data = await runCompareChart(
          tickers,
          chartStartDate,
          chartEndDate || undefined
        );
        setCompareChartData(data);
      }
    } catch (err) {
      setIndicatorError(getApiDisplayMessage(err, tr("chartLoadFailed")));
    } finally {
      setChartLoading(false);
    }
  }

  useEffect(() => {
    if (!marketWatchResult) {
      setIndicatorData(null);
      setCompareChartData(null);
      setIndicatorError(null);
      setChartLoading(false);
      return;
    }

    if (chartMode === "selected" && !selectedTicker) {
      return;
    }

    void fetchChartData();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- 与 LegacyDashboard 一致：仅在选中标的/结果/模式变化时自动拉取图表
  }, [selectedTicker, marketWatchResult, chartMode]);

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <SectionCard>
        <SectionHeader title={tr("marketWatch")} description={tr("marketWatchPageDesc")} />
        <p className="section-meta">{tr("marketWatchSignalNote")}</p>
      </SectionCard>

      <SectionCard id="market-watch">
        <SectionHeader title={tr("marketWatch")} description={tr("marketWatchDesc")} />

        <div className="form-grid">
          <label className="form-field">
            <span className="form-label">{tr("tickers")}</span>
            <textarea
              className="form-textarea"
              value={tickersInput}
              onChange={(event) => setTickersInput(event.target.value)}
              rows={2}
              placeholder={tr("tickersPlaceholder")}
            />
            <span className="helper-text">{tr("tickersHelper")}</span>
          </label>

          <label className="form-field">
            <span className="form-label">{tr("signalLookbackWindow")}</span>
            <select
              className="form-select"
              value={lookbackDays}
              onChange={(e) => setLookbackDays(Number(e.target.value))}
            >
              {LOOKBACK_OPTIONS.map((days) => (
                <option key={days} value={days}>
                  {formatMessage(tr("tradingDays"), { days })}
                </option>
              ))}
            </select>
            <span className="helper-text">{tr("signalLookbackHelper")}</span>
          </label>
        </div>

        <Button primary onClick={handleRunMarketWatch} disabled={isMarketWatchLoading}>
          {isMarketWatchLoading ? tr("running") : tr("runMarketWatch")}
        </Button>
        {isMarketWatchLoading && <LoadingState message={tr("toolResultsLoading")} />}
        {!isMarketWatchLoading && !marketWatchResult && !marketWatchError && (
          <EmptyState
            title={tr("toolResultsEmptyTitle")}
            description={tr("toolResultsEmptyDescription")}
          />
        )}
      </SectionCard>

      <SectionCard>
        <SectionHeader title={tr("dataFreshness")} description={tr("dataFreshnessDesc")} />
        <dl className="info-grid info-grid--4">
          <div className="info-grid__item">
            <dt>{tr("dataSource")}</dt>
            <dd>{translateDataSource(language, marketWatchResult?.data_source ?? tr("na"))}</dd>
          </div>
          <div className="info-grid__item">
            <dt>{tr("signalLookbackWindow")}</dt>
            <dd>
              {marketWatchResult
                ? formatMessage(tr("tradingDays"), {
                    days: marketWatchResult.lookback_days,
                  })
                : formatMessage(tr("tradingDays"), { days: lookbackDays })}
            </dd>
          </div>
          <div className="info-grid__item">
            <dt>{tr("downloadStartDate")}</dt>
            <dd>{marketWatchResult?.download_start_date ?? tr("na")}</dd>
          </div>
          <div className="info-grid__item">
            <dt>{tr("latestAvailableDate")}</dt>
            <dd>{marketWatchResult?.latest_date ?? tr("na")}</dd>
          </div>
          <div className="info-grid__item info-grid__item--full">
            <dt>{tr("dataNote")}</dt>
            <dd>
              {translateBackendText(
                language,
                marketWatchResult?.data_note ?? tr("dataNoteDefault")
              )}
            </dd>
          </div>
        </dl>
      </SectionCard>

      {marketWatchError && (
        <SectionCard error>
          <SectionHeader title={tr("marketWatchError")} />
          <ErrorAlert message={marketWatchError} />
        </SectionCard>
      )}

      {!isMarketWatchLoading &&
        !marketWatchError &&
        marketWatchResult &&
        marketWatchResult.results.length > 0 && (
          <SectionCard>
            <SectionHeader title={tr("signalRanking")} description={tr("signalRankingDesc")} />

            <div className="reader-guide">
              {signalFieldGuide.map((item) => (
                <span key={item}>{item}</span>
              ))}
            </div>

            <DataTable className="table-scroll">
              <thead>
                <tr>
                  <th>{tr("rank")}</th>
                  <th>{tr("ticker")}</th>
                  <th>{tr("date")}</th>
                  <th className="num">{tr("price")}</th>
                  <th className="num">{tr("score")}</th>
                  <th>{tr("label")}</th>
                  <th>{tr("trend")}</th>
                  <th>{tr("risk")}</th>
                  <th className="num">{tr("return20d")}</th>
                  <th className="num">{tr("rsi")}</th>
                  <th className="num">{tr("volatility")}</th>
                </tr>
              </thead>
              <tbody>
                {marketWatchResult.results.map((row, index) => {
                  const isSelected = row.ticker === selectedTicker;
                  const trendStatus = getTrendStatus(row.signal_score);
                  const riskLevel = getRiskLevel(row.features.volatility_20d);
                  return (
                    <tr
                      key={row.ticker}
                      className={`is-clickable${isSelected ? " is-selected" : ""}`}
                      onClick={() => setSelectedTicker(row.ticker)}
                    >
                      <td className="num">{index + 1}</td>
                      <td className="cell-ticker">{row.ticker}</td>
                      <td>{row.date}</td>
                      <td className="num">{formatPrice(row.last_price)}</td>
                      <td className="num">{formatScore(row.signal_score)}</td>
                      <td>
                        <StatusBadge
                          label={translateSignalLabel(language, row.signal_label)}
                          variant={signalLabelVariant(row.signal_label)}
                        />
                      </td>
                      <td>
                        <StatusBadge
                          label={translateTrend(language, trendStatus)}
                          variant={trendVariant(trendStatus)}
                        />
                      </td>
                      <td>
                        <StatusBadge
                          label={translateRisk(language, riskLevel)}
                          variant={riskVariant(riskLevel)}
                        />
                      </td>
                      <td className="num">{formatPercent(row.features.return_20d)}</td>
                      <td className="num">{formatRsi(row.features.rsi_14)}</td>
                      <td className="num">{formatPercent(row.features.volatility_20d)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </DataTable>
          </SectionCard>
        )}

      {!marketWatchError && marketWatchResult && marketWatchResult.errors.length > 0 && (
        <SectionCard>
          <SectionHeader title={tr("tickerErrors")} />
          <ul className="interpretation-panel__list">
            {marketWatchResult.errors.map((item) => (
              <li key={item.ticker}>
                {item.ticker}: {item.error}
              </li>
            ))}
          </ul>
        </SectionCard>
      )}

      {!marketWatchError &&
        selectedResult &&
        marketWatchResult &&
        marketWatchResult.results.length > 0 && (
          <SectionCard>
            <div className="detail-header">
              <h2 className="detail-header__title">
                {formatMessage(tr("tickerDetail"), { ticker: selectedResult.ticker })}
              </h2>
              <div className="detail-badges">
                <StatusBadge
                  label={translateSignalLabel(language, selectedResult.signal_label)}
                  variant={signalLabelVariant(selectedResult.signal_label)}
                />
                <StatusBadge
                  label={translateTrend(
                    language,
                    getTrendStatus(selectedResult.signal_score)
                  )}
                  variant={trendVariant(getTrendStatus(selectedResult.signal_score))}
                />
                <StatusBadge
                  label={translateRisk(
                    language,
                    getRiskLevel(selectedResult.features.volatility_20d)
                  )}
                  variant={riskVariant(
                    getRiskLevel(selectedResult.features.volatility_20d)
                  )}
                />
              </div>
              <label className="form-field">
                <span className="form-label">{tr("select")}</span>
                <select
                  className="form-select"
                  value={selectedTicker ?? ""}
                  onChange={(event) => setSelectedTicker(event.target.value)}
                >
                  {marketWatchResult.results.map((item) => (
                    <option key={item.ticker} value={item.ticker}>
                      {item.ticker}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <p className="section-meta">
              {tr("signalScore")}: {formatScore(selectedResult.signal_score)}
            </p>

            <SectionHeader title={tr("metrics")} />
            <div className="metric-grid">
              <MetricCard
                label={tr("lastPrice")}
                value={formatPrice(selectedResult.last_price)}
                description={detailMetricHelp.lastPrice}
              />
              <MetricCard
                label="MA20"
                value={formatPrice(selectedResult.features.ma20)}
                description={detailMetricHelp.ma20}
              />
              <MetricCard
                label="MA60"
                value={formatPrice(selectedResult.features.ma60)}
                description={detailMetricHelp.ma60}
              />
              <MetricCard
                label={tr("distanceToMa20Label")}
                value={formatPercent(selectedResult.features.distance_to_ma20)}
                description={detailMetricHelp.distanceToMa20}
                featured
              />
              <MetricCard
                label={tr("distanceToMa60Label")}
                value={formatPercent(selectedResult.features.distance_to_ma60)}
                description={detailMetricHelp.distanceToMa60}
              />
              <MetricCard
                label={tr("dailyReturn")}
                value={formatPercent(selectedResult.features.daily_return)}
                description={detailMetricHelp.dailyReturn}
                tone={getReturnTone(selectedResult.features.daily_return)}
              />
              <MetricCard
                label={tr("return20d")}
                value={formatPercent(selectedResult.features.return_20d)}
                description={detailMetricHelp.return20d}
                featured
                tone={getReturnTone(selectedResult.features.return_20d)}
              />
              <MetricCard
                label={tr("return60d")}
                value={formatPercent(selectedResult.features.return_60d)}
                description={detailMetricHelp.return60d}
                tone={getReturnTone(selectedResult.features.return_60d)}
              />
              <MetricCard
                label={tr("rsi14")}
                value={formatRsi(selectedResult.features.rsi_14)}
                description={detailMetricHelp.rsi14}
                featured
              />
              <MetricCard
                label={tr("volatility20d")}
                value={formatPercent(selectedResult.features.volatility_20d)}
                description={detailMetricHelp.volatility20d}
                featured
              />
              <MetricCard
                label={tr("volumeChange")}
                value={formatPercent(selectedResult.features.volume_change)}
                description={detailMetricHelp.volumeChange}
                tone={getReturnTone(selectedResult.features.volume_change)}
              />
            </div>

            <SectionHeader
              title={tr("signalComponents")}
              description={tr("signalComponentsDesc")}
            />
            <DataTable className="table-scroll">
              <thead>
                <tr>
                  <th>{tr("component")}</th>
                  <th>{tr("status")}</th>
                  <th className="num">{tr("points")}</th>
                  <th>{tr("description")}</th>
                </tr>
              </thead>
              <tbody>
                {(selectedResult.signal_components ?? []).map((component) => (
                  <tr key={component.name}>
                    <td>{translateComponentName(language, component.name)}</td>
                    <td>
                      <StatusBadge
                        label={translatePassFail(language, component.passed)}
                        variant={passFailVariant(component.passed)}
                      />
                    </td>
                    <td className="num">{component.points}</td>
                    <td>{translateBackendText(language, component.description)}</td>
                  </tr>
                ))}
              </tbody>
            </DataTable>

            <SectionHeader title={tr("reasons")} description={tr("reasonsDesc")} />
            <ul className="interpretation-panel__list">
              {selectedResult.reasons.map((reason) => (
                <li key={reason}>{translateBackendText(language, reason)}</li>
              ))}
            </ul>
          </SectionCard>
        )}

      {!marketWatchError && marketWatchResult && marketWatchResult.results.length > 0 && (
        <SectionCard>
          <SectionHeader title={tr("chartSettings")} description={tr("chartSettingsDesc")} />

          <div className="form-grid form-grid--2">
            <label className="form-field">
              <span className="form-label">{tr("chartStartDate")}</span>
              <input
                className="form-input"
                type="date"
                value={chartStartDate}
                onChange={(e) => setChartStartDate(e.target.value)}
              />
            </label>
            <label className="form-field">
              <span className="form-label">{tr("chartEndDateOptional")}</span>
              <input
                className="form-input"
                type="date"
                value={chartEndDate}
                onChange={(e) => setChartEndDate(e.target.value)}
              />
            </label>
            <label className="form-field">
              <span className="form-label">{tr("chartMode")}</span>
              <select
                className="form-select"
                value={chartMode}
                onChange={(e) => setChartMode(e.target.value as ChartMode)}
              >
                {chartModeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <Button onClick={fetchChartData} disabled={chartLoading}>
            {chartLoading ? tr("loadingChart") : tr("refreshChart")}
          </Button>

          {chartMode === "compare" && marketWatchResult.results.length > 10 && (
            <p className="section-meta">{tr("chartManyTickers")}</p>
          )}

          {chartLoading && <LoadingState message={tr("loadingChart")} />}
          {indicatorError && <ErrorAlert message={indicatorError} />}

          {!chartLoading &&
            !indicatorError &&
            chartMode === "selected" &&
            selectedTicker &&
            indicatorData && (
              <div className="chart-panel">
                <h3 className="chart-panel__title">
                  {formatMessage(tr("closeMaTitle"), { ticker: selectedTicker })}
                </h3>
                <p className="chart-caption">{tr("closeMaCaption")}</p>
                <p className="section-meta">
                  {tr("actualDataRange")}:{" "}
                  {formatDateSeriesRange(indicatorData.data, tr("na"))}
                  {" · "}
                  {tr("rows")}: {indicatorData.rows}
                  {" · "}
                  {tr("dataSource")}: {translateDataSource(language, indicatorData.data_source)}
                </p>
                <PriceChart
                  key={`${selectedTicker}-${indicatorData.start_date}-${indicatorData.end_date ?? "latest"}`}
                  data={indicatorData.data}
                  labels={chartLabels}
                />
              </div>
            )}

          {!chartLoading &&
            !indicatorError &&
            chartMode === "compare" &&
            compareChartData && (
              <div className="chart-panel">
                <h3 className="chart-panel__title">{tr("compareChartTitle")}</h3>
                <p className="chart-caption">{tr("compareChartCaption")}</p>
                <p className="section-meta">
                  {tr("actualDataRange")}:{" "}
                  {formatDateSeriesRange(compareChartData.data, tr("na"))}
                  {" · "}
                  {tr("rows")}: {compareChartData.data.length}
                  {" · "}
                  {tr("dataSource")}: {translateDataSource(language, compareChartData.data_source)}
                </p>
                <CompareChart
                  key={`compare-${compareChartData.start_date}-${compareChartData.end_date ?? "latest"}`}
                  tickers={compareChartData.tickers}
                  data={compareChartData.data}
                  labels={chartLabels}
                />
                {compareChartData.errors.length > 0 && (
                  <ul className="interpretation-panel__list">
                    {compareChartData.errors.map((item) => (
                      <li key={item.ticker}>
                        {item.ticker}: {item.error}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
        </SectionCard>
      )}
    </AppShell>
  );
}
