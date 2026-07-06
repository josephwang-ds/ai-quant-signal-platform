"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";
import Button from "@/components/ui/Button";
import DataTable from "@/components/ui/DataTable";
import ErrorAlert from "@/components/ui/ErrorAlert";
import InterpretationPanel from "@/components/ui/InterpretationPanel";
import LoadingState from "@/components/ui/LoadingState";
import MetricCard from "@/components/ui/MetricCard";
import SectionCard from "@/components/ui/SectionCard";
import SectionHeader from "@/components/ui/SectionHeader";
import StatusBadge, {
  healthVariant,
  passFailVariant,
  riskVariant,
  signalLabelVariant,
  trendVariant,
} from "@/components/ui/StatusBadge";
import {
  getBackendHealth,
  getIndicators,
  runBacktest,
  runBacktestSensitivity,
  runCompareChart,
  runMarketWatch,
  runOOSValidation,
  type HealthResponse,
} from "@/lib/api";
import {
  formatMessage,
  getChartLabels,
  getOOSMetricRows,
  getOOSSegmentLabels,
  loadStoredLanguage,
  saveLanguage,
  t,
  translateBackendText,
  translateComponentName,
  translateOOSInterpretation,
  translatePassFail,
  translateRisk,
  translateSignalLabel,
  translateTrend,
  type Language,
  type TranslationKey,
} from "@/lib/i18n";
import { generateBacktestInterpretation } from "@/lib/backtestInterpretation";
import {
  formatMetricPercent,
  formatMetricSharpe,
  formatMetricTrades,
  formatPercent,
  formatPrice,
  formatRsi,
  formatScore,
  getDrawdownTone,
  getReturnTone,
  getSharpeTone,
} from "@/lib/formatters";
import {
  generateSensitivityInterpretation,
  sortSensitivityResults,
} from "@/lib/sensitivityInterpretation";
import type {
  BacktestResponse,
  BacktestStrategy,
  ChartMode,
  CompareChartResponse,
  IndicatorsResponse,
  MarketWatchResponse,
  OOSResponse,
  OOSSegmentMetrics,
  SensitivityResponse,
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

const BacktestChart = dynamic(() => import("@/components/BacktestChart"), {
  ssr: false,
  loading: () => <LoadingState message="Loading chart..." />,
});

const DEFAULT_TICKERS = "AAPL, MSFT, NVDA, TSLA, SPY";
const DEFAULT_LOOKBACK_DAYS = 120;
const DEFAULT_CHART_START_DATE = "2022-01-01";
const DEFAULT_BACKTEST_TICKER = "AAPL";
const DEFAULT_SHORT_WINDOW = 20;
const DEFAULT_LONG_WINDOW = 60;
const DEFAULT_MOMENTUM_WINDOW = 60;
const DEFAULT_TRANSACTION_COST = 0.001;
const DEFAULT_SPLIT_DATE = "2025-01-01";
const DEFAULT_SENSITIVITY_PAIRS = [
  { short: 10, long: 30 },
  { short: 20, long: 60 },
  { short: 50, long: 120 },
  { short: 50, long: 200 },
];
const LOOKBACK_OPTIONS = [90, 120, 252, 500];

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

function getChartModeOptions(lang: Language): { value: ChartMode; label: string }[] {
  return [
    { value: "selected", label: t(lang, "chartModeSelected") },
    { value: "compare", label: t(lang, "chartModeCompare") },
  ];
}

const DEMO_PILLAR_KEYS = [
  { title: "demoDataPipeline", desc: "demoDataPipelineDesc" },
  { title: "demoSignalScoring", desc: "demoSignalScoringDesc" },
  { title: "demoBacktestingCard", desc: "demoBacktestingDesc" },
  { title: "demoRobustness", desc: "demoRobustnessDesc" },
] as const satisfies ReadonlyArray<{ title: TranslationKey; desc: TranslationKey }>;

// 将输入文本解析为 ticker 数组
function parseTickers(input: string): string[] {
  return input
    .split(/[,\s\n]+/)
    .map((ticker) => ticker.trim())
    .filter(Boolean);
}

type OOSSegmentKey = "full_period" | "in_sample" | "out_of_sample";

function getOOSMetricValue(
  metrics: OOSSegmentMetrics,
  key: string
): number | null {
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

// 根据信号分数返回趋势状态（表格紧凑展示）
function getTrendStatus(signalScore: number): "Positive" | "Mixed" | "Weak" {
  if (signalScore >= 60) {
    return "Positive";
  }
  if (signalScore >= 40) {
    return "Mixed";
  }
  return "Weak";
}

// 根据 20 日波动率返回风险等级
function getRiskLevel(volatility20d: number): "High" | "Medium" | "Low" {
  if (volatility20d >= 0.6) {
    return "High";
  }
  if (volatility20d >= 0.35) {
    return "Medium";
  }
  return "Low";
}

// 首页：健康检查 + Market Watch 信号排名
export default function HomePage() {
  const [language, setLanguage] = useState<Language>("en");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);

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
  const [backtestTicker, setBacktestTicker] = useState(DEFAULT_BACKTEST_TICKER);
  const [backtestStartDate, setBacktestStartDate] = useState(DEFAULT_CHART_START_DATE);
  const [backtestEndDate, setBacktestEndDate] = useState("");
  const [shortWindow, setShortWindow] = useState(DEFAULT_SHORT_WINDOW);
  const [longWindow, setLongWindow] = useState(DEFAULT_LONG_WINDOW);
  const [backtestStrategy, setBacktestStrategy] = useState<BacktestStrategy>("ma_crossover");
  const [momentumWindow, setMomentumWindow] = useState(DEFAULT_MOMENTUM_WINDOW);
  const [transactionCost, setTransactionCost] = useState(String(DEFAULT_TRANSACTION_COST));
  const [backtestResult, setBacktestResult] = useState<BacktestResponse | null>(null);
  const [backtestLoading, setBacktestLoading] = useState(false);
  const [backtestError, setBacktestError] = useState<string | null>(null);
  const [sensitivityResult, setSensitivityResult] = useState<SensitivityResponse | null>(null);
  const [sensitivityLoading, setSensitivityLoading] = useState(false);
  const [sensitivityError, setSensitivityError] = useState<string | null>(null);
  const [oosSplitDate, setOosSplitDate] = useState(DEFAULT_SPLIT_DATE);
  const [oosResult, setOosResult] = useState<OOSResponse | null>(null);
  const [oosLoading, setOosLoading] = useState(false);
  const [oosError, setOosError] = useState<string | null>(null);
  const marketWatchRequestIdRef = useRef(0);

  const tr = (key: TranslationKey) => t(language, key);
  const chartLabels = getChartLabels(language);
  const detailMetricHelp = getDetailMetricHelp(language);
  const backtestMetricHelp = getBacktestMetricHelp(language);
  const oosSegmentLabels = getOOSSegmentLabels(language);
  const oosMetricRows = getOOSMetricRows(language);
  const chartModeOptions = getChartModeOptions(language);
  const signalFieldGuide = getSignalFieldGuide(language);

  useEffect(() => {
    setLanguage(loadStoredLanguage());
  }, []);

  function handleLanguageChange(next: Language) {
    setLanguage(next);
    saveLanguage(next);
  }

  async function handleCheckBackend() {
    setHealthLoading(true);
    setHealthError(null);
    setHealth(null);

    try {
      const data = await getBackendHealth();
      setHealth(data);
    } catch {
      setHealthError(tr("backendUnreachable"));
    } finally {
      setHealthLoading(false);
    }
  }

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
      const message =
        error instanceof Error ? error.message : tr("marketWatchFailed");
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

  const selectedResult: SignalResult | undefined = marketWatchResult?.results.find(
    (item) => item.ticker === selectedTicker
  );

  useEffect(() => {
    if (selectedTicker) {
      setBacktestTicker(selectedTicker);
    }
  }, [selectedTicker]);

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

    if (backtestStrategy === "ma_crossover") {
      if (!Number.isFinite(parsedShortWindow) || !Number.isFinite(parsedLongWindow)) {
        setBacktestError(tr("shortLongInvalid"));
        return;
      }

      if (parsedShortWindow >= parsedLongWindow) {
        setBacktestError(tr("shortLessThanLong"));
        return;
      }
    } else if (!Number.isFinite(parsedMomentumWindow)) {
      setBacktestError(tr("momentumInvalid"));
      return;
    } else if (parsedMomentumWindow < 5 || parsedMomentumWindow > 252) {
      setBacktestError(tr("momentumRange"));
      return;
    }

    if (!Number.isFinite(parsedTransactionCost) || parsedTransactionCost < 0) {
      setBacktestError(tr("transactionCostInvalid"));
      return;
    }

    setBacktestLoading(true);
    setBacktestError(null);
    setBacktestResult(null);

    try {
      const response = await runBacktest(
        backtestStrategy === "ma_crossover"
          ? {
              ticker: normalizedTicker,
              start_date: backtestStartDate,
              end_date: backtestEndDate || undefined,
              strategy: "ma_crossover",
              short_window: parsedShortWindow,
              long_window: parsedLongWindow,
              transaction_cost: parsedTransactionCost,
            }
          : {
              ticker: normalizedTicker,
              start_date: backtestStartDate,
              end_date: backtestEndDate || undefined,
              strategy: "momentum",
              momentum_window: parsedMomentumWindow,
              transaction_cost: parsedTransactionCost,
            }
      );
      setBacktestResult(response);
    } catch (error) {
      setBacktestError(
        error instanceof Error ? error.message : tr("backtestFailed")
      );
    } finally {
      setBacktestLoading(false);
    }
  }

  async function handleRunSensitivityAnalysis() {
    const normalizedTicker = backtestTicker.trim().toUpperCase();
    const parsedTransactionCost = Number(transactionCost);

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
        start_date: backtestStartDate,
        end_date: backtestEndDate || undefined,
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
    const normalizedTicker = backtestTicker.trim().toUpperCase();
    const parsedShortWindow = Number(shortWindow);
    const parsedLongWindow = Number(longWindow);
    const parsedTransactionCost = Number(transactionCost);

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

    if (oosSplitDate <= backtestStartDate) {
      setOosError(tr("splitAfterStart"));
      return;
    }

    if (backtestEndDate && backtestEndDate <= oosSplitDate) {
      setOosError(tr("endAfterSplit"));
      return;
    }

    setOosLoading(true);
    setOosError(null);
    setOosResult(null);

    try {
      const response = await runOOSValidation({
        ticker: normalizedTicker,
        start_date: backtestStartDate,
        split_date: oosSplitDate,
        end_date: backtestEndDate || undefined,
        short_window: parsedShortWindow,
        long_window: parsedLongWindow,
        transaction_cost: parsedTransactionCost,
      });
      setOosResult(response);
    } catch (error) {
      setOosError(
        error instanceof Error ? error.message : tr("oosFailed")
      );
    } finally {
      setOosLoading(false);
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
      setIndicatorError(
        err instanceof Error ? err.message : tr("chartLoadFailed")
      );
    } finally {
      setChartLoading(false);
    }
  }

  // market watch 成功后自动加载图表；日期/模式变更需点击 Refresh Chart
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

    fetchChartData();
  }, [selectedTicker, marketWatchResult, chartMode]);

  return (
    <main className="dashboard-page">
      <div className="dashboard-container">
        <header className="dashboard-header">
          <div className="language-toggle">
            <button
              type="button"
              className={`language-toggle__btn${language === "en" ? " is-active" : ""}`}
              onClick={() => handleLanguageChange("en")}
            >
              {tr("langEnglish")}
            </button>
            <button
              type="button"
              className={`language-toggle__btn${language === "zh" ? " is-active" : ""}`}
              onClick={() => handleLanguageChange("zh")}
            >
              {tr("langChinese")}
            </button>
          </div>
          <h1 className="dashboard-title">{tr("appTitle")}</h1>
          <p className="dashboard-subtitle">{tr("appSubtitle")}</p>
          <div className="dashboard-badges">
            <StatusBadge label={tr("educationalDemo")} variant="info" />
            <StatusBadge label={tr("dailyMarketData")} variant="neutral" />
            <StatusBadge label={tr("notFinancialAdvice")} variant="warning" />
          </div>
          <p className="dashboard-nav">
            <a href="#backtesting">{tr("navBacktesting")}</a>
            {" · "}
            <a href="#sensitivity-analysis">{tr("navSensitivity")}</a>
            {" · "}
            <a href="#oos-validation">{tr("navOos")}</a>
          </p>
        </header>

        <SectionCard compact>
          <SectionHeader title={tr("whatThisDemoShows")} />
          <div className="demo-showcase">
            {DEMO_PILLAR_KEYS.map((pillar) => (
              <article key={pillar.title} className="demo-pillar">
                <h3 className="demo-pillar__title">{tr(pillar.title)}</h3>
                <p className="demo-pillar__desc">{tr(pillar.desc)}</p>
              </article>
            ))}
          </div>
        </SectionCard>

        {/* 健康检查区域 */}
        <SectionCard compact>
          <div className="health-row">
            <div className="health-row__info">
              <strong>{tr("backendHealth")}</strong>
              <span className="inline-explainer">{tr("backendHealthHint")}</span>
              {health && (
                <>
                  <span>
                    {tr("status")}:{" "}
                    <StatusBadge
                      label={health.status}
                      variant={healthVariant(health.status)}
                    />
                  </span>
                  <span>
                    {tr("service")}: {health.service}
                  </span>
                </>
              )}
            </div>
            <Button onClick={handleCheckBackend} disabled={healthLoading}>
              {healthLoading ? tr("checking") : tr("checkBackend")}
            </Button>
          </div>
          {healthError && <ErrorAlert message={healthError} />}
        </SectionCard>

        {/* Market Watch 区域 */}
        <SectionCard>
          <SectionHeader
            title={tr("marketWatch")}
            description={tr("marketWatchDesc")}
          />

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
        </SectionCard>

        {/* 数据新鲜度面板 */}
        <SectionCard>
          <SectionHeader
            title={tr("dataFreshness")}
            description={tr("dataFreshnessDesc")}
          />
          <dl className="info-grid info-grid--4">
            <div className="info-grid__item">
              <dt>{tr("dataSource")}</dt>
              <dd>{marketWatchResult?.data_source ?? tr("na")}</dd>
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

        {/* 错误提示 */}
        {marketWatchError && (
          <SectionCard error>
            <SectionHeader title={tr("marketWatchError")} />
            <ErrorAlert message={marketWatchError} />
          </SectionCard>
        )}

        {/* 排名表格 */}
        {!isMarketWatchLoading &&
          !marketWatchError &&
          marketWatchResult &&
          marketWatchResult.results.length > 0 && (
          <SectionCard>
            <SectionHeader
              title={tr("signalRanking")}
              description={tr("signalRankingDesc")}
            />

            <div className="reader-guide">
              {signalFieldGuide.map((item) => (
                <span key={item}>{item}</span>
              ))}
            </div>

            <DataTable>
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
        {!marketWatchError &&
          marketWatchResult &&
          marketWatchResult.errors.length > 0 && (
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

        {/* 选中 ticker 详情 */}
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
            <DataTable>
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

        {/* Chart Settings */}
        {!marketWatchError &&
          marketWatchResult &&
          marketWatchResult.results.length > 0 && (
          <SectionCard>
            <SectionHeader
              title={tr("chartSettings")}
              description={tr("chartSettingsDesc")}
            />

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
                <>
                  <h3 className="chart-panel__title">
                    {formatMessage(tr("closeMaTitle"), { ticker: selectedTicker })}
                  </h3>
                  <p className="chart-caption">{tr("closeMaCaption")}</p>
                  <p className="section-meta">
                    {tr("chartRange")}: {indicatorData.start_date} →{" "}
                    {indicatorData.end_date ?? indicatorData.latest.date}
                    {" · "}
                    {tr("rows")}: {indicatorData.rows}
                    {" · "}
                    {tr("dataSource")}: {indicatorData.data_source}
                  </p>
                  <PriceChart
                    key={`${selectedTicker}-${indicatorData.start_date}-${indicatorData.end_date ?? "latest"}`}
                    data={indicatorData.data}
                    labels={chartLabels}
                  />
                </>
              )}

            {!chartLoading &&
              !indicatorError &&
              chartMode === "compare" &&
              compareChartData && (
                <>
                  <h3 className="chart-panel__title">{tr("compareChartTitle")}</h3>
                  <p className="chart-caption">{tr("compareChartCaption")}</p>
                  <p className="section-meta">
                    {tr("chartRange")}: {compareChartData.start_date} →{" "}
                    {compareChartData.end_date ??
                      (compareChartData.data.length > 0
                        ? String(
                            compareChartData.data[compareChartData.data.length - 1].date
                          )
                        : tr("na"))}
                    {" · "}
                    {tr("rows")}: {compareChartData.data.length}
                    {" · "}
                    {tr("dataSource")}: {compareChartData.data_source}
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
                </>
              )}
          </SectionCard>
        )}

        {/* Strategy Research */}
        <SectionCard>
          <SectionHeader
            title={tr("strategyResearch")}
            description={tr("strategyResearchDesc")}
          />
        </SectionCard>

        {/* Backtesting */}
        <SectionCard id="backtesting">
          <SectionHeader
            title={tr("backtesting")}
            description={tr("backtestingDesc")}
          />

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
                <option value="momentum">{tr("momentum")}</option>
              </select>
            </label>

            {backtestStrategy === "ma_crossover" && (
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

            {backtestStrategy === "momentum" && (
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

            <label className="form-field">
              <span className="form-label">{tr("transactionCost")}</span>
              <input
                className="form-input"
                type="number"
                min={0}
                step={0.0001}
                value={transactionCost}
                onChange={(e) => setTransactionCost(e.target.value)}
              />
              <span className="helper-text">{tr("transactionCostHelper")}</span>
            </label>
          </div>

          <Button onClick={handleRunBacktest} disabled={backtestLoading}>
            {backtestLoading ? tr("running") : tr("runBacktest")}
          </Button>

          <p className="section-meta">
            {backtestStrategy === "ma_crossover"
              ? tr("backtestMaExplain")
              : tr("backtestMomentumExplain")}{" "}
            {tr("backtestBiasNote")}
          </p>

          {backtestError && <ErrorAlert message={backtestError} />}

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

              <p className="section-meta">
                {backtestResult.ticker} · {backtestResult.strategy} ·{" "}
                {backtestResult.start_date} →{" "}
                {backtestResult.end_date ??
                  (backtestResult.data.length > 0
                    ? backtestResult.data[backtestResult.data.length - 1].date
                    : tr("na"))}
                {" · "}
                {tr("rows")}: {backtestResult.data.length}
                {" · "}
                {tr("dataSource")}: {backtestResult.data_source}
              </p>

              <BacktestChart data={backtestResult.data} labels={chartLabels} />
            </>
          )}
        </SectionCard>

        {/* Parameter Sensitivity Analysis */}
        <SectionCard id="sensitivity-analysis">
          <SectionHeader
            title={tr("sensitivityAnalysis")}
            description={tr("sensitivityDesc")}
          />

          <p className="section-header__description">{tr("sensitivityExplain")}</p>

          <div className="section-meta">
            <p>
              {tr("sensitivityReuses")}: {backtestTicker.trim().toUpperCase() || "—"} ·{" "}
              {backtestStartDate} → {backtestEndDate || tr("latest")} · {tr("transactionCost")}:{" "}
              {transactionCost || DEFAULT_TRANSACTION_COST}
            </p>
            <p>
              {tr("defaultParameterPairs")}:{" "}
              {DEFAULT_SENSITIVITY_PAIRS.map(
                (pair) => `${pair.short} / ${pair.long}`
              ).join(", ")}
            </p>
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
                  {sensitivityResult.ticker} · {sensitivityResult.strategy} ·{" "}
                  {sensitivityResult.start_date} → {sensitivityResult.end_date ?? tr("latest")}
                  {" · "}
                  {tr("dataSource")}: {sensitivityResult.data_source}
                </p>

                <DataTable>
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
                          className={isBestSharpe ? "is-highlight" : ""}
                        >
                          <td className="num">{row.short_window}</td>
                          <td className="num">{row.long_window}</td>
                          <td className="num">{formatMetricPercent(row.total_return)}</td>
                          <td className="num">
                            {formatMetricPercent(row.benchmark_return)}
                          </td>
                          <td className="num">{formatMetricPercent(row.cagr)}</td>
                          <td className="num">{formatMetricSharpe(row.sharpe_ratio)}</td>
                          <td className="num">
                            {formatMetricPercent(
                              row.strategy_max_drawdown ?? row.max_drawdown
                            )}
                          </td>
                          <td className="num">
                            {formatMetricPercent(row.benchmark_max_drawdown)}
                          </td>
                          <td className="num">{formatMetricPercent(row.volatility)}</td>
                          <td className="num">
                            {formatMetricTrades(row.number_of_trades)}
                          </td>
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

        {/* Out-of-Sample Validation */}
        <SectionCard id="oos-validation">
          <SectionHeader title={tr("oosValidation")} description={tr("oosDesc")} />

          <div className="form-grid">
            <label className="form-field">
              <span className="form-label">{tr("tickerFromBacktest")}</span>
              <input className="form-input" type="text" value={backtestTicker} readOnly />
            </label>

            <label className="form-field">
              <span className="form-label">{tr("startDateFromBacktest")}</span>
              <input
                className="form-input"
                type="date"
                value={backtestStartDate}
                readOnly
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
              <span className="form-label">{tr("endDateFromBacktest")}</span>
              <input
                className="form-input"
                type="date"
                value={backtestEndDate}
                readOnly
              />
            </label>

            <label className="form-field">
              <span className="form-label">{tr("shortLongWindow")}</span>
              <input
                className="form-input"
                type="text"
                value={`${shortWindow} / ${longWindow}`}
                readOnly
              />
            </label>

            <label className="form-field">
              <span className="form-label">{tr("transactionCost")}</span>
              <input className="form-input" type="text" value={transactionCost} readOnly />
            </label>
          </div>

          <Button onClick={handleRunOOSValidation} disabled={oosLoading}>
            {oosLoading ? tr("running") : tr("runOosValidation")}
          </Button>

          {oosError && <ErrorAlert message={oosError} />}

          {oosResult && (
            <>
              <p className="section-meta">
                {oosResult.ticker} · {oosResult.strategy} · {oosResult.start_date} →{" "}
                {oosResult.end_date ?? tr("latest")} · {tr("split")}: {oosResult.split_date}
                {" · "}
                {tr("dataSource")}: {oosResult.data_source}
              </p>

              <DataTable>
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
                      {(Object.keys(oosSegmentLabels) as OOSSegmentKey[]).map(
                        (segmentKey) => {
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
                        }
                      )}
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

        <details className="about-demo">
          <summary>{tr("aboutThisDemo")}</summary>
          <p className="about-demo__text">{tr("aboutThisDemoText")}</p>
        </details>

        <footer className="dashboard-footer">
          {tr("footerLine1")} {tr("footerLine2")} {tr("footerLine3")}
        </footer>
      </div>
    </main>
  );
}
