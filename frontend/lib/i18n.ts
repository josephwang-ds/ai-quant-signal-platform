export type Language = "en" | "zh";

export const LANGUAGE_STORAGE_KEY = "ai-quant-language";

export const translations = {
  en: {
    appTitle: "AI Quant Research Workspace",
    appSubtitle:
      "Modular quant research workspace for signals, rule-based strategies, experiments, and AI-assisted explanation.",
    educationalDemo: "Portfolio Showcase",
    dailyMarketData: "Daily Market Data",
    notFinancialAdvice: "Not Financial Advice",
    navBacktesting: "Backtesting",
    navSensitivity: "Parameter Sensitivity",
    navOos: "OOS Validation",
    navOverview: "Overview",
    navDataCenter: "Data Center",
    navMarketWatch: "Market Watch",
    navStrategyLab: "Strategy Lab",
    navComparison: "Comparison",
    navRobustness: "Robustness",
    navModelLab: "Model Lab",
    navExperiments: "Experiments",
    navResearchNotes: "Research Notes",
    navAiAgent: "AI Agent",
    langEnglish: "English",
    langChinese: "中文",

    backendHealth: "Backend Health",
    backendHealthHint: "Checks whether the data API is alive.",
    status: "Status",
    service: "Service",
    checkBackend: "Check Backend",
    checking: "Checking...",
    backendUnreachable:
      "Backend is not reachable. Make sure FastAPI is running on port 8000.",

    marketWatch: "Market Watch",
    marketWatchDesc:
      "First pass: compare tickers with the same rules, then inspect the score, trend, risk, and rule components before looking at charts.",
    marketWatchPageDesc:
      "Rank tickers by rule-based signal scores and inspect the underlying indicators, reasons, and charts.",
    marketWatchSignalNote:
      "Signal scores are rule-based research indicators. They are not buy or sell recommendations.",
    tickers: "Tickers",
    tickersPlaceholder: "AAPL, MSFT, NVDA",
    tickersHelper: "Ticker = stock symbol. Separate multiple tickers with commas or spaces.",
    signalLookbackWindow: "Signal Lookback Window",
    signalLookbackHelper:
      "Used only to compute latest signal snapshots. Chart and backtest dates are controlled separately.",
    tradingDays: "{days} trading days",
    runMarketWatch: "Run Market Watch",
    running: "Running...",
    enterOneTicker: "Please enter at least one ticker.",
    marketWatchFailed: "Failed to run market watch.",
    marketWatchError: "Market Watch Error",

    dataFreshness: "Data Freshness",
    dataFreshnessDesc:
      "A quant workflow starts here: stale or partial data can make every downstream signal misleading.",
    dataSource: "Data Source",
    downloadStartDate: "Data Download Start (Calendar Date)",
    latestAvailableDate: "Latest Available Date",
    dataNote: "Data Note",
    dataNoteDefault:
      "Latest date is based on the most recent available daily bar from Yahoo Finance via yfinance. Data may be delayed depending on exchange and provider.",

    signalRanking: "Signal Ranking",
    signalRankingDesc:
      "Professional read order: check Score, confirm Label and Trend, then look at Risk before opening a ticker.",
    fieldGuideScore:
      "Score: 0-100 signal score. Higher means more bullish signals passed.",
    fieldGuideLabel:
      "Label: quick signal summary, such as Bullish, Neutral, or Bearish.",
    fieldGuideTrend: "Trend: simplified read of the score for fast scanning.",
    fieldGuideRisk:
      "Risk: volatility bucket. High risk means price has moved around more.",
    rank: "Rank",
    ticker: "Ticker",
    date: "Date",
    lastPrice: "Last Price",
    price: "Price",
    signalScore: "Signal Score",
    score: "Score",
    label: "Label",
    trend: "Trend",
    risk: "Risk",
    dailyReturn: "Daily Return",
    return20d: "20D Return",
    return60d: "60D Return",
    rsi14: "RSI 14",
    rsi: "RSI",
    volatility: "Volatility",
    volatility20d: "20D Volatility",
    volumeChange: "Volume Change",
    distanceToMa20Label: "Distance to MA20",
    distanceToMa60Label: "Distance to MA60",
    tickerErrors: "Ticker Errors",

    tickerDetail: "{ticker} Detail",
    select: "Select",
    metrics: "Metrics",
    signalComponents: "Signal Components",
    signalComponentsDesc:
      "Each component is one rule inside the total score. Pass adds points; Fail adds none.",
    reasons: "Reasons",
    reasonsDesc:
      "Plain-language explanation of why the selected ticker received its current label.",
    component: "Component",
    points: "Points",
    description: "Description",
    whatItMeans: "What it means",

    chartSettings: "Chart Settings",
    chartSettingsDesc:
      "Choose the date range and whether to view one ticker or compare all ranked tickers.",
    chartStartDate: "Chart Start Date",
    chartEndDate: "Chart End Date",
    chartEndDateOptional: "Chart End Date (optional)",
    chartMode: "Chart Mode",
    chartModeSelected: "Selected Ticker Only",
    chartModeCompare: "Compare All Ranked Tickers",
    refreshChart: "Refresh Chart",
    loadingChart: "Loading chart...",
    chartZoomHint: "Use the bottom range selector to zoom into a specific date range.",
    chartManyTickers: "Showing many tickers may make the chart harder to read.",
    chartLoadFailed: "Failed to load chart data.",
    actualDataRange: "Actual data",
    rows: "Rows",
    closeMaTitle: "{ticker} — Close, MA20, MA60",
    closeMaCaption:
      "Close is the daily closing price. MA20 and MA60 smooth the price to show short-term and medium-term trend.",
    compareChartTitle: "Normalized Close Comparison (Day 1 = 100)",
    compareChartCaption:
      "Normalized means every ticker starts at 100, making relative performance easier to compare even when prices are different.",

    strategyLab: "Strategy Lab",
    strategyLabDesc:
      "Select a decision method and compare how each rule triggers simulated buy/sell events in backtest.",
    strategyLabSimulatedNote:
      "These are simulated backtest results only. The system does not place real trades.",
    combinedSignal: "MA + Momentum Combined",
    momentumStrategy: "Momentum",
    combinedMode: "Combined Mode",
    conservative: "Conservative",
    aggressive: "Aggressive",
    strategySelectHint:
      "Switch methods in the Strategy dropdown. The parameter fields below update for each strategy.",
    strategyGuideWhat: "What it is",
    strategyGuideParams: "What to set",
    strategyGuideRead: "How to read results",
    strategyMaWhat:
      "A trend-following rule: hold the asset when the short moving average is above the long moving average; otherwise stay in cash.",
    strategyMaParams:
      "Short Window (default 20) and Long Window (default 60); long must be greater than short. Also choose ticker, date range, and transaction cost.",
    strategyMaRead:
      "After Run Backtest: compare the strategy vs buy-and-hold chart, Sharpe, and drawdown; open Trade Log for BUY/SELL dates and MA trigger reasons.",
    strategyMomentumWhat:
      "A trend-following rule: hold when the past N-day return is positive; exit when momentum is zero or negative.",
    strategyMomentumParams:
      "Momentum Window (default 60, range 5–252): number of trading days used to compute past return.",
    strategyMomentumRead:
      "After Run Backtest: check whether momentum timing beat buy-and-hold; Trade Log reasons mention positive vs non-positive past return.",
    strategyCombinedWhat:
      "Uses both MA crossover and momentum. Conservative holds only when both agree; Aggressive holds when either is positive.",
    strategyCombinedParams:
      "Short/Long windows (MA), Momentum Window, and Combined Mode dropdown: Conservative (both positive) or Aggressive (either positive).",
    strategyCombinedRead:
      "After Run Backtest: compare trade count vs single-rule strategies; conservative usually trades less, aggressive may trade more.",
    combinedModeHelper:
      "Conservative: both MA and momentum must be positive to hold. Aggressive: hold if either MA or momentum is positive.",
    strategyMaCard:
      "MA Crossover holds the asset when the short moving average is above the long moving average. It is a simple trend-following rule.",
    strategyMomentumCard:
      "Momentum holds the asset when the past N-day return is positive, and exits when momentum turns non-positive.",
    strategyCombinedCard:
      "Combined Signal uses both MA crossover and momentum. Conservative mode requires both signals to be positive. Aggressive mode requires either signal to be positive.",
    backtestCombinedExplain:
      "Combined Signal merges MA crossover and momentum. Conservative mode holds only when both agree; aggressive mode holds when either is positive.",
    startDate: "Start Date",
    endDate: "End Date",
    backtestStartDate: "Backtest Start Date",
    backtestEndDate: "Backtest End Date (optional)",
    strategy: "Strategy",
    maCrossover: "MA Crossover",
    momentum: "Momentum",
    shortWindow: "Short Window",
    longWindow: "Long Window",
    momentumWindow: "Momentum Window",
    transactionCost: "Transaction Cost",
    transactionCostHelper: "0.001 means 0.10% cost per position change.",
    runBacktest: "Run Backtest",
    backtestMaExplain:
      "Backtesting checks how a trading rule would have performed historically. This demo uses a moving average crossover rule: when the short moving average is above the long moving average, the strategy holds the stock; otherwise it stays in cash.",
    backtestMomentumExplain:
      "Backtesting checks how a trading rule would have performed historically. This demo uses a momentum rule: when the past N-day return is positive, the strategy holds the stock; otherwise it stays in cash.",
    backtestBiasNote:
      "Position is shifted by one period to avoid look-ahead bias. Transaction cost is applied whenever the position changes.",
    backtestWarmupNote:
      "Because indicators need a warm-up window, the first backtest bar may be later than the requested start date.",
    strategyComparison: "Strategy Comparison",
    strategyComparisonDesc:
      "Compare MA crossover, momentum, combined signal, and buy-and-hold under the same ticker, date range, and transaction cost.",
    strategyComparisonReuses: "Reuses Strategy Lab inputs",
    compareStrategies: "Compare Strategies",
    bestTotalReturn: "Best Total Return",
    bestSharpe: "Best Sharpe",
    lowestDrawdown: "Lowest Drawdown",
    fewestTrades: "Fewest Trades",
    buyAndHold: "Buy & Hold",
    strategyComparisonExplain:
      "This comparison does not tell which strategy will work in the future. It only shows how different rules performed historically under the same assumptions.",
    strategyComparisonDisclaimer1:
      "This comparison shows historical performance under the same assumptions.",
    strategyComparisonDisclaimer2: "It does not predict future performance.",
    strategyComparisonDisclaimer3: "It is not financial advice.",
    strategyComparisonFailed: "Failed to compare strategies.",
    comparisonColStrategy: "Strategy",
    comparisonColBenchmark: "Benchmark Return",
    comparisonColMaxDrawdown: "Max Drawdown",
    comparisonColTrades: "Trades",
    totalReturn: "Total Return",
    benchmarkReturn: "Benchmark Return",
    cagr: "CAGR",
    sharpeRatio: "Sharpe Ratio",
    sharpe: "Sharpe",
    strategyMaxDrawdown: "Strategy Max Drawdown",
    strategyMaxDd: "Strategy Max DD",
    benchmarkMaxDrawdown: "Benchmark Max Drawdown",
    benchmarkMaxDd: "Benchmark Max DD",
    winRate: "Win Rate",
    numberOfTrades: "Number of Trades",
    trades: "Trades",
    transactionCostTotal: "Transaction Cost Total",
    backtestInterpretation: "Backtest Interpretation",
    backtestInterpretationNote:
      "Rule-based research interpretation. Not financial advice.",
    backtestFailed: "Failed to run backtest.",

    sensitivityAnalysis: "MA Parameter Sensitivity",
    sensitivityDesc:
      "Robustness read: similar results across parameter pairs are more credible than one isolated winner.",
    sensitivityExplain:
      "This is not optimization. It checks whether the strategy is robust across reasonable parameter choices.",
    sensitivityReuses: "Reuses Backtesting inputs",
    defaultParameterPairs: "Default parameter pairs",
    runSensitivityAnalysis: "Run Sensitivity Analysis",
    shortMa: "Short MA",
    longMa: "Long MA",
    sensitivityInterpretation: "Sensitivity Interpretation",
    sensitivityInterpretationNote:
      "This sensitivity analysis is for research demonstration only. It is not parameter optimization and not financial advice.",
    parameterSetErrors: "Parameter Set Errors",
    sensitivityFailed: "Failed to run sensitivity analysis.",

    oosValidation: "Out-of-Sample Validation",
    oosDesc:
      "Split the backtest into in-sample and out-of-sample periods to check whether the strategy generalizes beyond the initial research window.",
    splitDate: "Split Date",
    tickerFromBacktest: "Ticker (from Backtesting)",
    startDateFromBacktest: "Start Date (from Backtesting)",
    endDateFromBacktest: "End Date (from Backtesting, optional)",
    shortLongWindow: "Short / Long Window",
    runOosValidation: "Run OOS Validation",
    fullPeriod: "Full Period",
    inSample: "In-Sample",
    outOfSample: "Out-of-Sample",
    metric: "Metric",
    oosInterpretation: "OOS Interpretation",
    oosInterpretationNote:
      "Out-of-sample validation is for research demonstration only. It is not parameter optimization and not financial advice.",
    split: "Split",
    oosFailed: "Failed to run OOS validation.",

    overviewTitle: "Workspace Overview",
    overviewDesc:
      "A modular quant research environment. Each module owns one responsibility: data, signals, strategies, experiments, notes, and AI explanation — not trading.",
    categoryCoreResearch: "Core Research",
    categoryDataStorage: "Data & Storage",
    categoryModelAi: "Model & AI",
    categorySystemNotes: "System Notes",
    statusActive: "Active",
    statusBasicSupport: "Basic Support",
    statusPlanned: "Planned",
    statusComingLater: "Coming Later",
    openModule: "Open Module",
    openLegacyDemo: "Open full demo",
    legacyDemoHint:
      "Full functionality is temporarily on the legacy dashboard while this module is being migrated.",
    modulePlannedStatus: "Planned module",
    moduleMigratingStatus:
      "This module will be separated from the original dashboard.",

    dataCenter: "Data Center",
    dataCenterPageDesc:
      "Manage data source coverage, symbol formats, asset classes, and future provider integration.",
    dataCenterDesc:
      "Documents current Yahoo/yfinance coverage, asset classes, symbol formats, and the planned multi-source roadmap.",
    dcCurrentActiveProvider: "Current Active Provider",
    dcLiveProviderStatus: "Live Provider Status",
    dcActiveProvider: "Active Provider",
    dcProvidersList: "Providers",
    dcLoadingProviderStatus: "Loading provider status...",
    dcProviderStatusError: "Could not load provider status.",
    dcStaticDocsFallback: "Static documentation is still available below.",
    dcAssetClassCoverage: "Asset Class Coverage",
    dcPlannedProviders: "Planned Providers",
    dcSymbolFormatGuide: "Symbol Format Guide",
    dcFutureDataArchitecture: "Future Data Architecture",
    dcColAssetClass: "Asset Class",
    dcColMarket: "Market",
    dcColExamples: "Example Symbols",
    dcColCurrentSource: "Current Source",
    dcColStatus: "Status",
    dcColNotes: "Notes",
    dcColFormatType: "Format",
    dcColSymbolExample: "Example",
    dcProviderYahoo: "Yahoo / yfinance",
    dcYahooNote:
      "Yahoo/yfinance is used for research and demo purposes. It is not treated as trading-grade data.",
    dcYahooUseUsStocks: "US stocks",
    dcYahooUseEtfs: "ETFs",
    dcYahooUseHkStocks: "HK stocks",
    dcYahooUseCnBasic: "Basic China A-share through Yahoo symbols",
    dcYahooUseCryptoBasic: "Basic crypto tickers",
    dcYahooUseIndicesFxFutures: "Indices / FX / futures examples",
    dcSourceYahoo: "Yahoo / yfinance",
    dcSourcePlanned: "Planned",
    dcMarketUs: "US",
    dcMarketHk: "HK",
    dcMarketCn: "CN",
    dcMarketCrypto: "Crypto",
    dcMarketGlobal: "Global",
    dcMarketFx: "FX",
    dcMarketFutures: "Futures",
    dcMarketCustom: "Custom",
    dcAssetUsStocks: "US Stocks",
    dcAssetEtfs: "ETFs",
    dcAssetHkStocks: "HK Stocks",
    dcAssetCnYahoo: "China A-share via Yahoo",
    dcAssetCryptoYahoo: "Crypto via Yahoo",
    dcAssetIndices: "Indices",
    dcAssetFx: "FX",
    dcAssetFutures: "Commodities / Futures",
    dcAssetCsvUpload: "CSV Upload",
    dcNoteCnAkShare: "AKShare planned for more China-specific coverage.",
    dcNoteCryptoCoinGecko: "CoinGecko planned for richer crypto market data.",
    dcNoteCsvUpload: "For custom research datasets and model lab experiments.",
    dcAkShareTitle: "AKShare",
    dcAkShareDesc:
      "Planned for China A-share. Future use: historical prices, adjustment mode, and Chinese market metadata.",
    dcCoinGeckoTitle: "CoinGecko",
    dcCoinGeckoDesc:
      "Planned for crypto. Future use: market cap, volume, and historical crypto market data.",
    dcCsvUploadTitle: "CSV Upload",
    dcCsvUploadDesc:
      "Planned for custom datasets. Future use: local experiments and Model Lab.",
    dcTushareTitle: "Tushare / BaoStock",
    dcTushareDesc: "Optional later. Future use: alternative China market data.",
    dcSymbolUsStock: "US stock",
    dcSymbolEtf: "ETF",
    dcSymbolHkStock: "HK stock",
    dcSymbolCnShanghai: "China Shanghai via Yahoo",
    dcSymbolCnShenzhen: "China Shenzhen via Yahoo",
    dcSymbolCrypto: "Crypto via Yahoo",
    dcSymbolFx: "FX",
    dcSymbolFutures: "Futures",
    dcArchDataSource:
      "Data Source is where data comes from. Cache is temporary and rebuildable. Database stores durable research assets.",
    dcArchNormalize:
      "Future providers should normalize data into a common OHLCV schema before strategy or model code consumes it.",
    dcArchSchema:
      "Target normalized fields: date, open, high, low, close, volume, symbol, market, data_source, adjustment, currency.",
    dcCachePlanned: "Cache layer: planned, not implemented.",
    dcDatabasePlanned: "Database persistence: planned for research assets, not raw OHLCV in v1.",
    robustnessChecks: "Robustness Checks",
    robustnessChecksDesc:
      "Parameter sensitivity, out-of-sample validation, and future walk-forward and model robustness checks.",
    robustnessPageDesc:
      "Test whether strategy behavior is sensitive to parameters or unstable out of sample.",
    robustnessEducationalNote:
      "Robustness checks help reduce overclaiming. A strategy that works only for one parameter set or only in-sample may not be reliable.",
    modelLab: "Model Lab",
    modelLabDesc:
      "ML dataset builder, feature engineering, logistic regression, gradient boosting models, and future deep learning signal research.",
    experiments: "Experiments",
    experimentsDesc:
      "Saved backtest runs, trade logs, strategy comparisons, model runs, and experiment history backed by the database.",
    researchNotes: "Research Notes",
    researchNotesDesc:
      "Watchlist, ticker, and strategy notes linked to backtests and model runs — human-written and AI-generated.",
    aiResearchAgent: "AI Research Agent",
    aiResearchAgentDesc:
      "LLM explanations of backtest results, trade logs, and strategy comparisons. Research note drafting — no trading or financial advice.",

    moduleDataCenterOverviewDesc:
      "Documents current Yahoo/yfinance coverage and planned AKShare, CoinGecko, and CSV data sources.",
    moduleMarketWatchOverviewDesc:
      "Rank tickers, inspect signal components, and view indicator charts.",
    moduleStrategyLabOverviewDesc:
      "Run rule-based backtests: MA crossover, momentum, and combined signals.",
    moduleComparisonOverviewDesc:
      "Compare MA, momentum, combined, and buy-and-hold on the same inputs.",
    moduleRobustnessOverviewDesc:
      "Parameter sensitivity and out-of-sample validation checks.",
    moduleModelLabOverviewDesc:
      "ML dataset building, feature engineering, and signal model experiments.",
    moduleExperimentsOverviewDesc:
      "Review saved backtests, trade logs, comparisons, and model runs.",
    moduleResearchNotesOverviewDesc:
      "Human and AI research notes linked to tickers, strategies, and runs.",
    moduleAiAgentOverviewDesc:
      "LLM explanations of results and research note drafting — no trading.",

    systemCurrentDataSource: "Current data source: Yahoo Finance via yfinance",
    systemFutureDatabase: "Future database: Supabase / Postgres",
    systemFutureCache: "Future cache: Redis / Upstash or equivalent",
    systemNotAdvice: "For research demonstration only — not financial advice.",

    footerLine1: "For portfolio and research demonstration only.",
    footerLine2: "Not financial advice.",
    footerLine3: "Not for live trading.",

    chartStrategyVsHold: "Strategy vs Buy & Hold",
    chartDrawdown: "Drawdown",
    chartStrategyVsHoldDrawdown: "Strategy vs Buy & Hold Drawdown",
    chartStrategy: "Strategy",
    chartBuyHold: "Buy & Hold",
    chartStrategyDrawdown: "Strategy Drawdown",
    chartBenchmarkDrawdown: "Benchmark Drawdown",
    chartClose: "Close",
    chartBacktestZoomHint:
      "Use the bottom range selector to zoom and pan across the backtest period.",
    noBacktestData: "No backtest data available.",
    noChartData: "No chart data available for the selected date range.",
    noCompareData: "No compare chart data available.",

    latest: "latest",
    na: "N/A",
    pass: "Pass",
    fail: "Fail",
    trendPositive: "Positive",
    trendMixed: "Mixed",
    trendWeak: "Weak",
    riskLow: "Low",
    riskMedium: "Medium",
    riskHigh: "High",

    tickerEmpty: "Ticker cannot be empty.",
    shortLongInvalid: "Short window and long window must be valid numbers.",
    shortLessThanLong: "Short window must be less than long window.",
    momentumInvalid: "Momentum window must be a valid number.",
    momentumRange: "Momentum window must be between 5 and 252.",
    transactionCostInvalid: "Transaction cost must be zero or greater.",
    splitAfterStart: "Split date must be after backtest start date.",
    endAfterSplit: "Backtest end date must be after split date.",

    helpLastPrice: "Most recent close price in the downloaded data.",
    helpMa20: "Average price over the last 20 trading days.",
    helpMa60: "Average price over the last 60 trading days.",
    helpDistanceMa20: "How far price is above or below MA20.",
    helpDistanceMa60: "How far price is above or below MA60.",
    helpDailyReturn: "One-day price change.",
    helpReturn20d: "Price change over roughly one trading month.",
    helpReturn60d: "Price change over roughly one trading quarter.",
    helpRsi14: "Momentum gauge from 0 to 100; high can mean overheated.",
    helpVolatility20d: "Recent price choppiness. Higher means less stable.",
    helpVolumeChange: "Recent trading volume versus its normal level.",
    helpTotalReturn: "Strategy gain or loss over the tested period.",
    helpBenchmarkReturn: "Buy-and-hold result for the same ticker.",
    helpCagr: "Annualized return, useful for comparing different date ranges.",
    helpSharpe: "Return adjusted by volatility. Higher is generally better.",
    helpStrategyMaxDd: "Worst peak-to-trough drop for the strategy.",
    helpBenchmarkMaxDd: "Worst peak-to-trough drop for buy-and-hold.",
    helpVolatility: "How much the strategy return fluctuated.",
    helpWinRate: "Share of profitable trading days or periods.",
    helpTrades: "How often the strategy changed position.",
    helpTransactionCost: "Total drag from simulated trading costs.",

    whatThisDemoShows: "What This Demo Shows",
    demoDataPipeline: "Data Pipeline",
    demoDataPipelineDesc:
      "Retrieve daily market data and calculate technical indicators.",
    demoSignalScoring: "Signal Scoring",
    demoSignalScoringDesc:
      "Rank tickers using trend, momentum, RSI, and volatility conditions.",
    demoBacktestingCard: "Strategy Lab",
    demoBacktestingDesc:
      "Backtest MA crossover, momentum, or MA + momentum combined (conservative / aggressive). Includes trade log and benchmark charts.",
    demoRobustness: "Robustness Checks",
    demoRobustnessDesc:
      "Use parameter sensitivity and out-of-sample validation to reduce overclaiming.",
    aboutThisDemo: "About This Project",
    aboutThisDemoText:
      "A quant research dashboard built for portfolio showcase and research demonstration. It uses daily historical market data and simplified backtesting assumptions. It is not financial advice and is not intended for live trading.",

    tradeLog: "Trade Log",
    tradeLogDesc:
      "Shows simulated buy and sell events generated by the selected strategy. These are backtest events only, not real orders.",
    tradeLogDateNote:
      "The trade date is the trading day when the position changes (daily bars; no intraday time). Buy and sell rows each include this date.",
    tradeLogAction: "Action",
    tradeLogReason: "Reason",
    tradeDate: "Trade Date",
    positionAfter: "Position After",
    tradeBuy: "BUY",
    tradeSell: "SELL",
    tradeLogEmpty: "No trades were triggered for this period and strategy.",
    tradeLogScrollHint: "More than 15 trades — scroll down to see all rows.",
  },
  zh: {
    appTitle: "AI 量化研究工作区",
    appSubtitle:
      "模块化量化研究工作区，覆盖信号、规则策略、实验存档与 AI 辅助解读。",
    educationalDemo: "作品展示",
    dailyMarketData: "日线市场数据",
    notFinancialAdvice: "非投资建议",
    navBacktesting: "回测",
    navSensitivity: "参数敏感性",
    navOos: "样本外验证",
    navOverview: "总览",
    navDataCenter: "数据中心",
    navMarketWatch: "市场观察",
    navStrategyLab: "策略实验室",
    navComparison: "策略对比",
    navRobustness: "稳健性",
    navModelLab: "模型实验室",
    navExperiments: "实验存档",
    navResearchNotes: "研究笔记",
    navAiAgent: "AI 研究助手",
    langEnglish: "English",
    langChinese: "中文",

    backendHealth: "后端健康检查",
    backendHealthHint: "检查数据 API 是否正常运行。",
    status: "状态",
    service: "服务",
    checkBackend: "检查后端",
    checking: "检查中...",
    backendUnreachable: "无法连接后端，请确认 FastAPI 已在 8000 端口运行。",

    marketWatch: "市场观察",
    marketWatchDesc:
      "第一步：用相同规则对比多个标的，查看分数、趋势、风险与规则组成，再进入图表分析。",
    marketWatchPageDesc:
      "根据规则型信号评分对股票进行排序，并查看底层指标、触发原因和图表。",
    marketWatchSignalNote: "信号评分是规则型研究指标，不是买入或卖出建议。",
    tickers: "标的代码",
    tickersPlaceholder: "AAPL, MSFT, NVDA",
    tickersHelper: "Ticker 即股票代码，多个标的可用逗号或空格分隔。",
    signalLookbackWindow: "信号回看窗口",
    signalLookbackHelper:
      "仅用于计算最新信号快照。图表与回测日期在下方单独控制。",
    tradingDays: "{days} 个交易日",
    runMarketWatch: "运行市场观察",
    running: "运行中...",
    enterOneTicker: "请至少输入一个标的代码。",
    marketWatchFailed: "市场观察运行失败。",
    marketWatchError: "市场观察错误",

    dataFreshness: "数据新鲜度",
    dataFreshnessDesc: "量化流程从这里开始：陈旧或不完整的数据会让后续信号产生误导。",
    dataSource: "数据来源",
    downloadStartDate: "数据下载起始（日历日）",
    latestAvailableDate: "最新可用日期",
    dataNote: "数据说明",
    dataNoteDefault:
      "最新日期基于 Yahoo Finance（yfinance）最近可用的日线数据，实际数据可能因交易所与数据源而延迟。",

    signalRanking: "信号排名",
    signalRankingDesc:
      "建议阅读顺序：先看分数，再确认标签与趋势，最后查看风险后再点开详情。",
    fieldGuideScore: "分数：0–100 信号分，越高表示通过的偏多规则越多。",
    fieldGuideLabel: "标签：信号摘要，如偏多、中性或偏空。",
    fieldGuideTrend: "趋势：分数的简化解读，便于快速浏览。",
    fieldGuideRisk: "风险：波动率分档，高风险表示价格起伏更大。",
    rank: "排名",
    ticker: "标的",
    date: "日期",
    lastPrice: "最新价",
    price: "价格",
    signalScore: "信号分数",
    score: "分数",
    label: "标签",
    trend: "趋势",
    risk: "风险",
    dailyReturn: "日收益",
    return20d: "20 日收益",
    return60d: "60 日收益",
    rsi14: "RSI 14",
    rsi: "RSI",
    volatility: "波动率",
    volatility20d: "20 日波动率",
    volumeChange: "成交量变化",
    distanceToMa20Label: "相对 MA20",
    distanceToMa60Label: "相对 MA60",
    tickerErrors: "标的数据错误",

    tickerDetail: "{ticker} 详情",
    select: "选择",
    metrics: "指标",
    signalComponents: "信号组成",
    signalComponentsDesc: "每个组成项对应总分中的一条规则，通过则加分，未通过则不加分。",
    reasons: "原因说明",
    reasonsDesc: "用通俗语言解释当前标签的形成原因。",
    component: "组成项",
    points: "得分",
    description: "说明",
    whatItMeans: "含义",

    chartSettings: "图表设置",
    chartSettingsDesc: "选择日期范围，并决定查看单个标的还是对比全部排名标的。",
    chartStartDate: "图表起始日期",
    chartEndDate: "图表结束日期",
    chartEndDateOptional: "图表结束日期（可选）",
    chartMode: "图表模式",
    chartModeSelected: "仅选中标的",
    chartModeCompare: "对比全部排名标的",
    refreshChart: "刷新图表",
    loadingChart: "加载图表中...",
    chartZoomHint: "使用底部范围选择器可缩放至特定日期区间。",
    chartManyTickers: "标的过多可能使图表难以阅读。",
    chartLoadFailed: "图表数据加载失败。",
    actualDataRange: "实际数据",
    rows: "行数",
    closeMaTitle: "{ticker} — 收盘价、MA20、MA60",
    closeMaCaption:
      "收盘价为每日收盘价格，MA20 与 MA60 用于平滑价格并展示短中期趋势。",
    compareChartTitle: "归一化收盘价对比（首日 = 100）",
    compareChartCaption:
      "归一化表示每个标的从 100 起步，便于在价格不同的情况下比较相对表现。",

    strategyLab: "策略实验室",
    strategyLabDesc:
      "选择不同决策方法，比较各规则在回测中如何触发模拟买卖事件。",
    strategyLabSimulatedNote: "这些仅为模拟回测结果，系统不会执行真实交易。",
    combinedSignal: "均线 + 动量组合",
    momentumStrategy: "动量策略",
    combinedMode: "组合模式",
    conservative: "保守模式",
    aggressive: "进取模式",
    strategySelectHint: "在「策略」下拉框中切换方法，下方参数区会随策略自动变化。",
    strategyGuideWhat: "是什么",
    strategyGuideParams: "需要设置什么",
    strategyGuideRead: "结果怎么看",
    strategyMaWhat:
      "趋势跟踪规则：短期均线高于长期均线时持有资产，否则保持空仓。",
    strategyMaParams:
      "短期窗口（默认 20）、长期窗口（默认 60），长期须大于短期；另选标的、日期区间与交易成本。",
    strategyMaRead:
      "运行回测后：看策略 vs 买入持有曲线、Sharpe 与回撤；展开交易记录查看买卖日期与均线触发原因。",
    strategyMomentumWhat:
      "趋势跟踪规则：过去 N 日收益为正时持有，动量为零或负时退出。",
    strategyMomentumParams:
      "动量窗口（默认 60，范围 5–252）：用于计算过去收益正负的交易日数。",
    strategyMomentumRead:
      "运行回测后：看动量择时是否跑赢买入持有；交易记录原因会说明过去收益为正或非正。",
    strategyCombinedWhat:
      "同时使用均线交叉与动量。保守模式两者都为正才持有；进取模式任一为正即持有。",
    strategyCombinedParams:
      "短/长均线窗口、动量窗口，以及组合模式下拉：保守（两者都为正）或进取（任一为正）。",
    strategyCombinedRead:
      "运行回测后：对比交易次数与单策略差异；保守通常换仓更少，进取可能更频繁。",
    combinedModeHelper:
      "保守：均线与动量都为正才持有。进取：均线或动量任一为正即持有。",
    strategyMaCard:
      "均线交叉策略在短期均线高于长期均线时持有资产，是一种简单的趋势跟踪规则。",
    strategyMomentumCard:
      "动量策略在过去 N 日收益为正时持有资产，在动量转弱时退出。",
    strategyCombinedCard:
      "组合信号同时使用均线和动量。保守模式要求两个信号都为正，进取模式只要求任一信号为正。",
    backtestCombinedExplain:
      "组合信号合并均线交叉与动量。保守模式需两者同时为正才持有；进取模式任一为正即持有。",
    startDate: "起始日期",
    endDate: "结束日期",
    backtestStartDate: "回测起始日期",
    backtestEndDate: "回测结束日期（可选）",
    strategy: "策略",
    maCrossover: "均线交叉",
    momentum: "动量",
    shortWindow: "短期窗口",
    longWindow: "长期窗口",
    momentumWindow: "动量窗口",
    transactionCost: "交易成本",
    transactionCostHelper: "0.001 表示每次换仓成本 0.10%。",
    runBacktest: "运行回测",
    backtestMaExplain:
      "回测用于检查一个交易规则在历史上会如何表现。本策略使用均线交叉规则：当短期均线高于长期均线时持有股票，否则保持空仓。",
    backtestMomentumExplain:
      "回测用于检查一个交易规则在历史上会如何表现。本策略使用动量规则：当过去 N 天收益为正时持有股票，否则保持空仓。",
    backtestBiasNote:
      "持仓信号会向后移动一个周期，以避免使用未来信息。每次仓位变化时都会计入交易成本。",
    backtestWarmupNote: "因指标预热，首条回测日晚于起始日。",
    strategyComparison: "策略对比",
    strategyComparisonDesc:
      "在同一股票、时间区间和交易成本下，对比均线交叉、动量、组合信号和买入持有。",
    strategyComparisonReuses: "复用策略实验室输入",
    compareStrategies: "对比策略",
    bestTotalReturn: "最高总收益",
    bestSharpe: "最高 Sharpe",
    lowestDrawdown: "最低回撤",
    fewestTrades: "最少交易",
    buyAndHold: "买入并持有",
    strategyComparisonExplain:
      "该对比不能说明哪种策略未来一定有效，只展示不同规则在相同假设下的历史表现。",
    strategyComparisonDisclaimer1: "本对比展示在相同假设下的历史表现。",
    strategyComparisonDisclaimer2: "不能预测未来表现。",
    strategyComparisonDisclaimer3: "不构成投资建议。",
    strategyComparisonFailed: "策略对比运行失败。",
    comparisonColStrategy: "策略",
    comparisonColBenchmark: "基准收益",
    comparisonColMaxDrawdown: "最大回撤",
    comparisonColTrades: "交易次数",
    totalReturn: "总收益",
    benchmarkReturn: "基准收益",
    cagr: "年化复合收益",
    sharpeRatio: "Sharpe 比率",
    sharpe: "Sharpe",
    strategyMaxDrawdown: "策略最大回撤",
    strategyMaxDd: "策略最大回撤",
    benchmarkMaxDrawdown: "基准最大回撤",
    benchmarkMaxDd: "基准最大回撤",
    winRate: "胜率",
    numberOfTrades: "交易次数",
    trades: "交易次数",
    transactionCostTotal: "交易成本合计",
    backtestInterpretation: "回测解读",
    backtestInterpretationNote: "基于规则的研究解读，非投资建议。",
    backtestFailed: "回测运行失败。",

    sensitivityAnalysis: "均线参数敏感性分析",
    sensitivityDesc:
      "稳健性视角：多组参数结果相近，比单一参数表现更好更值得信任。",
    sensitivityExplain:
      "这不是参数优化，而是检查策略在合理参数范围内是否稳健。",
    sensitivityReuses: "复用回测输入",
    defaultParameterPairs: "默认参数组合",
    runSensitivityAnalysis: "运行敏感性分析",
    shortMa: "短期均线",
    longMa: "长期均线",
    sensitivityInterpretation: "敏感性解读",
    sensitivityInterpretationNote:
      "本敏感性分析仅供研究演示，不是参数优化，也不是投资建议。",
    parameterSetErrors: "参数组合错误",
    sensitivityFailed: "敏感性分析运行失败。",

    oosValidation: "样本外验证",
    oosDesc:
      "将回测切分为样本内与样本外区间，检验策略是否能超出初始研究窗口泛化。",
    splitDate: "切分日期",
    tickerFromBacktest: "标的（来自回测）",
    startDateFromBacktest: "起始日期（来自回测）",
    endDateFromBacktest: "结束日期（来自回测，可选）",
    shortLongWindow: "短 / 长窗口",
    runOosValidation: "运行样本外验证",
    fullPeriod: "全样本",
    inSample: "样本内",
    outOfSample: "样本外",
    metric: "指标",
    oosInterpretation: "样本外解读",
    oosInterpretationNote:
      "样本外验证仅供研究演示，不是参数优化，也不是投资建议。",
    split: "切分",
    oosFailed: "样本外验证运行失败。",

    overviewTitle: "工作区总览",
    overviewDesc:
      "模块化量化研究环境。各模块各司其职：数据、信号、策略、实验、笔记与 AI 解读——不涉及交易执行。",
    categoryCoreResearch: "核心研究",
    categoryDataStorage: "数据与存储",
    categoryModelAi: "模型与 AI",
    categorySystemNotes: "系统说明",
    statusActive: "已启用",
    statusBasicSupport: "基础支持",
    statusPlanned: "规划中",
    statusComingLater: "后续上线",
    openModule: "进入模块",
    openLegacyDemo: "打开完整演示",
    legacyDemoHint: "本模块迁移完成前，完整功能请暂时使用旧版演示页。",
    modulePlannedStatus: "规划中的模块",
    moduleMigratingStatus: "本模块将从原仪表盘拆分独立。",

    dataCenter: "数据中心",
    dataCenterPageDesc:
      "管理数据源覆盖范围、代码格式、资产类别和未来数据提供方集成。",
    dataCenterDesc:
      "记录当前 Yahoo/yfinance 覆盖范围、资产类别、代码格式与多数据源规划路线图。",
    dcCurrentActiveProvider: "当前启用数据源",
    dcLiveProviderStatus: "实时数据源状态",
    dcActiveProvider: "当前启用数据源",
    dcProvidersList: "数据源列表",
    dcLoadingProviderStatus: "正在加载数据源状态...",
    dcProviderStatusError: "无法加载数据源状态。",
    dcStaticDocsFallback: "下方静态文档仍可查看。",
    dcAssetClassCoverage: "资产类别覆盖",
    dcPlannedProviders: "规划中的数据源",
    dcSymbolFormatGuide: "代码格式指南",
    dcFutureDataArchitecture: "未来数据架构",
    dcColAssetClass: "资产类别",
    dcColMarket: "市场",
    dcColExamples: "示例代码",
    dcColCurrentSource: "当前数据源",
    dcColStatus: "状态",
    dcColNotes: "说明",
    dcColFormatType: "格式类型",
    dcColSymbolExample: "示例",
    dcProviderYahoo: "Yahoo / yfinance",
    dcYahooNote:
      "Yahoo/yfinance 用于研究和演示目的，不作为交易级数据源。",
    dcYahooUseUsStocks: "美股",
    dcYahooUseEtfs: "ETF",
    dcYahooUseHkStocks: "港股",
    dcYahooUseCnBasic: "通过 Yahoo 代码的基础 A 股支持",
    dcYahooUseCryptoBasic: "基础加密货币代码",
    dcYahooUseIndicesFxFutures: "指数 / 外汇 / 期货示例",
    dcSourceYahoo: "Yahoo / yfinance",
    dcSourcePlanned: "规划中",
    dcMarketUs: "美国",
    dcMarketHk: "香港",
    dcMarketCn: "中国",
    dcMarketCrypto: "加密",
    dcMarketGlobal: "全球",
    dcMarketFx: "外汇",
    dcMarketFutures: "期货",
    dcMarketCustom: "自定义",
    dcAssetUsStocks: "美股",
    dcAssetEtfs: "ETF",
    dcAssetHkStocks: "港股",
    dcAssetCnYahoo: "通过 Yahoo 的 A 股",
    dcAssetCryptoYahoo: "通过 Yahoo 的加密货币",
    dcAssetIndices: "指数",
    dcAssetFx: "外汇",
    dcAssetFutures: "商品 / 期货",
    dcAssetCsvUpload: "CSV 上传",
    dcNoteCnAkShare: "计划使用 AKShare 提供更完整的中国市场覆盖。",
    dcNoteCryptoCoinGecko: "计划使用 CoinGecko 提供更丰富的加密市场数据。",
    dcNoteCsvUpload: "用于自定义研究数据集与模型实验室实验。",
    dcAkShareTitle: "AKShare",
    dcAkShareDesc:
      "规划用于中国 A 股。未来用途：历史价格、复权方式与中国市场元数据。",
    dcCoinGeckoTitle: "CoinGecko",
    dcCoinGeckoDesc:
      "规划用于加密货币。未来用途：市值、成交量与历史加密市场数据。",
    dcCsvUploadTitle: "CSV 上传",
    dcCsvUploadDesc: "规划用于自定义数据集。未来用途：本地实验与模型实验室。",
    dcTushareTitle: "Tushare / BaoStock",
    dcTushareDesc: "可选后续方案。未来用途：替代性中国市场数据。",
    dcSymbolUsStock: "美股",
    dcSymbolEtf: "ETF",
    dcSymbolHkStock: "港股",
    dcSymbolCnShanghai: "Yahoo 上海 A 股",
    dcSymbolCnShenzhen: "Yahoo 深圳 A 股",
    dcSymbolCrypto: "Yahoo 加密货币",
    dcSymbolFx: "外汇",
    dcSymbolFutures: "期货",
    dcArchDataSource:
      "数据源是数据的来源。缓存是临时且可重建的。数据库保存持久研究资产。",
    dcArchNormalize:
      "未来所有数据提供方都应先标准化为统一 OHLCV 结构，再供策略和模型模块使用。",
    dcArchSchema:
      "目标标准化字段：date, open, high, low, close, volume, symbol, market, data_source, adjustment, currency。",
    dcCachePlanned: "缓存层：已规划，尚未实现。",
    dcDatabasePlanned: "数据库持久化：已规划用于研究资产，v1 不存储全量 OHLCV。",
    robustnessChecks: "稳健性检查",
    robustnessChecksDesc:
      "参数敏感性、样本外验证，以及后续的滚动窗口与模型稳健性检查。",
    robustnessPageDesc: "检查策略是否对参数过度敏感，或在样本外表现不稳定。",
    robustnessEducationalNote:
      "稳健性检查用于减少过度解读。如果一个策略只在某一组参数或样本内有效，可靠性可能不足。",
    modelLab: "模型实验室",
    modelLabDesc:
      "机器学习数据集构建、特征工程、逻辑回归、梯度提升模型，以及后续深度学习信号研究。",
    experiments: "实验存档",
    experimentsDesc:
      "保存的回测、交易日志、策略对比、模型运行记录与实验历史，由数据库持久化。",
    researchNotes: "研究笔记",
    researchNotesDesc:
      "与自选、标的、策略及回测/模型运行关联的研究笔记，支持人工撰写与 AI 生成。",
    aiResearchAgent: "AI 研究助手",
    aiResearchAgentDesc:
      "用大模型解读回测结果、交易日志与策略对比，辅助撰写研究笔记——不执行交易，不构成投资建议。",

    moduleDataCenterOverviewDesc:
      "记录当前 Yahoo/yfinance 覆盖范围，以及规划中的 AKShare、CoinGecko 与 CSV 数据源。",
    moduleMarketWatchOverviewDesc:
      "对标的进行信号排名，查看规则组成与指标图表。",
    moduleStrategyLabOverviewDesc:
      "运行规则策略回测：均线交叉、动量与组合信号。",
    moduleComparisonOverviewDesc:
      "在相同输入下对比均线、动量、组合与买入并持有。",
    moduleRobustnessOverviewDesc:
      "参数敏感性与样本外验证检查。",
    moduleModelLabOverviewDesc:
      "机器学习数据集构建、特征工程与信号模型实验。",
    moduleExperimentsOverviewDesc:
      "查看已保存的回测、交易日志、对比结果与模型运行。",
    moduleResearchNotesOverviewDesc:
      "与标的、策略及运行关联的人工与 AI 研究笔记。",
    moduleAiAgentOverviewDesc:
      "用大模型解读结果并辅助撰写研究笔记——不涉及交易。",

    systemCurrentDataSource: "当前数据源：Yahoo Finance（yfinance）",
    systemFutureDatabase: "未来数据库：Supabase / Postgres",
    systemFutureCache: "未来缓存：Redis / Upstash 或同类方案",
    systemNotAdvice: "仅供研究演示——不构成投资建议。",

    footerLine1: "仅供作品集与研究演示。",
    footerLine2: "非投资建议。",
    footerLine3: "不用于实盘交易。",

    chartStrategyVsHold: "策略 vs 买入并持有",
    chartDrawdown: "回撤",
    chartStrategyVsHoldDrawdown: "策略 vs 买入并持有回撤",
    chartStrategy: "策略",
    chartBuyHold: "买入并持有",
    chartStrategyDrawdown: "策略回撤",
    chartBenchmarkDrawdown: "基准回撤",
    chartClose: "收盘价",
    chartBacktestZoomHint: "使用底部范围选择器可在回测区间内缩放与平移。",
    noBacktestData: "暂无回测数据。",
    noChartData: "所选日期区间暂无图表数据。",
    noCompareData: "暂无对比图表数据。",

    latest: "最新",
    na: "无",
    pass: "通过",
    fail: "未通过",
    trendPositive: "正向",
    trendMixed: "中性",
    trendWeak: "负向",
    riskLow: "低",
    riskMedium: "中",
    riskHigh: "高",

    tickerEmpty: "标的代码不能为空。",
    shortLongInvalid: "短期窗口与长期窗口必须是有效数字。",
    shortLessThanLong: "短期窗口必须小于长期窗口。",
    momentumInvalid: "动量窗口必须是有效数字。",
    momentumRange: "动量窗口必须在 5 到 252 之间。",
    transactionCostInvalid: "交易成本必须大于等于 0。",
    splitAfterStart: "切分日期必须晚于回测起始日期。",
    endAfterSplit: "回测结束日期必须晚于切分日期。",

    helpLastPrice: "下载数据中最近的收盘价。",
    helpMa20: "过去 20 个交易日的平均价格。",
    helpMa60: "过去 60 个交易日的平均价格。",
    helpDistanceMa20: "价格相对 MA20 的偏离程度。",
    helpDistanceMa60: "价格相对 MA60 的偏离程度。",
    helpDailyReturn: "单日价格变化。",
    helpReturn20d: "约一个交易月的价格变化。",
    helpReturn60d: "约一个交易季度的价格变化。",
    helpRsi14: "0–100 的动量指标，过高可能表示过热。",
    helpVolatility20d: "近期价格波动程度，越高越不稳定。",
    helpVolumeChange: "近期成交量相对正常水平的偏离。",
    helpTotalReturn: "策略在测试区间内的盈亏。",
    helpBenchmarkReturn: "同一标的买入并持有的结果。",
    helpCagr: "年化收益，便于比较不同日期区间。",
    helpSharpe: "经波动率调整后的收益，通常越高越好。",
    helpStrategyMaxDd: "策略从峰值到谷底的最大跌幅。",
    helpBenchmarkMaxDd: "买入并持有从峰值到谷底的最大跌幅。",
    helpVolatility: "策略收益的波动程度。",
    helpWinRate: "盈利交易日或区间的占比。",
    helpTrades: "策略换仓的次数。",
    helpTransactionCost: "模拟交易成本带来的总拖累。",

    whatThisDemoShows: "本演示展示什么",
    demoDataPipeline: "数据流程",
    demoDataPipelineDesc: "获取日线市场数据，并计算技术指标。",
    demoSignalScoring: "信号评分",
    demoSignalScoringDesc: "结合趋势、动量、RSI 和波动率条件，对标的进行信号评分。",
    demoBacktestingCard: "策略实验室",
    demoBacktestingDesc:
      "回测均线交叉、动量策略，或均线+动量组合（保守 / 进取），含交易记录与基准对比图。",
    demoRobustness: "稳健性检验",
    demoRobustnessDesc: "通过参数敏感性和样本外验证，避免只看单一历史最优结果。",
    aboutThisDemo: "关于本项目",
    aboutThisDemoText:
      "这是一个面向作品集与研究演示的量化研究看板。项目使用历史日线数据和简化回测假设，不构成投资建议，也不用于实盘交易。",

    tradeLog: "交易记录",
    tradeLogDesc:
      "显示由所选策略生成的模拟买卖事件。这些仅为回测事件，不是真实订单。",
    tradeLogDateNote:
      "交易日期为仓位发生变更的交易日（日线回测，不含盘中时点）；买入与卖出行均记录该日期。",
    tradeLogAction: "动作",
    tradeLogReason: "触发原因",
    tradeDate: "交易日期",
    positionAfter: "交易后仓位",
    tradeBuy: "买入",
    tradeSell: "卖出",
    tradeLogEmpty: "该区间与策略下未触发任何交易。",
    tradeLogScrollHint: "超过 15 条记录时可向下滚动查看全部。",
  },
} as const;

export type TranslationKey = keyof typeof translations.en;

export function t(lang: Language, key: TranslationKey): string {
  return translations[lang][key] ?? translations.en[key] ?? key;
}

export function formatMessage(
  template: string,
  vars: Record<string, string | number>
): string {
  return template.replace(/\{(\w+)\}/g, (_, name: string) =>
    vars[name] != null ? String(vars[name]) : ""
  );
}

export function loadStoredLanguage(): Language {
  if (typeof window === "undefined") {
    return "en";
  }
  const stored = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
  return stored === "zh" ? "zh" : "en";
}

export function saveLanguage(lang: Language): void {
  if (typeof window !== "undefined") {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, lang);
  }
}

const SIGNAL_LABEL_TEXT: Record<Language, Record<string, string>> = {
  en: {
    "Strong Bullish Watchlist": "Strong Bullish Watchlist",
    "Bullish Watchlist": "Bullish Watchlist",
    Neutral: "Neutral",
    "Bearish Watchlist": "Bearish Watchlist",
    "High Risk / Avoid": "High Risk / Avoid",
  },
  zh: {
    "Strong Bullish Watchlist": "强势观察",
    "Bullish Watchlist": "偏多观察",
    Neutral: "中性",
    "Bearish Watchlist": "偏弱观察",
    "High Risk / Avoid": "高风险 / 谨慎",
  },
};

export function translateSignalLabel(lang: Language, label: string): string {
  return SIGNAL_LABEL_TEXT[lang][label] ?? label;
}

export function translateTrend(
  lang: Language,
  trend: "Positive" | "Mixed" | "Weak"
): string {
  const keyMap: Record<typeof trend, TranslationKey> = {
    Positive: "trendPositive",
    Mixed: "trendMixed",
    Weak: "trendWeak",
  };
  return t(lang, keyMap[trend]);
}

export function translateRisk(
  lang: Language,
  risk: "High" | "Medium" | "Low"
): string {
  const keyMap: Record<typeof risk, TranslationKey> = {
    High: "riskHigh",
    Medium: "riskMedium",
    Low: "riskLow",
  };
  return t(lang, keyMap[risk]);
}

export function translatePassFail(lang: Language, passed: boolean): string {
  return passed ? t(lang, "pass") : t(lang, "fail");
}

const COMPONENT_NAME_ZH: Record<string, string> = {
  "Short-term trend": "短期趋势",
  "Medium-term trend": "中期趋势",
  Momentum: "动量",
  "RSI health": "RSI 健康度",
  "Volatility control": "波动率控制",
};

export function translateComponentName(lang: Language, name: string): string {
  if (lang === "en") {
    return name;
  }
  return COMPONENT_NAME_ZH[name] ?? name;
}

const BACKEND_TEXT_ZH: Record<string, string> = {
  "Price is above MA20, showing short-term trend strength.":
    "价格高于 MA20，短期趋势偏强。",
  "Price is below MA20, suggesting weak short-term trend.":
    "价格低于 MA20，短期趋势偏弱。",
  "MA20 is above MA60, indicating positive medium-term trend.":
    "MA20 高于 MA60，中期趋势偏多。",
  "MA20 is below MA60, indicating weaker trend structure.":
    "MA20 低于 MA60，趋势结构偏弱。",
  "20-day return is positive, suggesting recent momentum.":
    "20 日收益为正，近期动量偏强。",
  "20-day return is negative, suggesting weak recent momentum.":
    "20 日收益为负，近期动量偏弱。",
  "RSI is in a healthy range, not extremely overbought or oversold.":
    "RSI 处于健康区间，未明显超买或超卖。",
  "RSI is above 70, suggesting possible overbought risk.":
    "RSI 高于 70，可能存在超买风险。",
  "RSI is below 40, suggesting weak momentum or oversold conditions.":
    "RSI 低于 40，动量偏弱或处于超卖状态。",
  "20-day annualized volatility is within an acceptable range.":
    "20 日年化波动率处于可接受范围。",
  "20-day annualized volatility is high, increasing risk.":
    "20 日年化波动率偏高，风险上升。",
  "Latest date is based on the most recent available daily bar from Yahoo Finance via yfinance. Data may be delayed depending on exchange and provider.":
    "最新日期基于 Yahoo Finance（yfinance）最近可用的日线数据，实际数据可能因交易所与数据源而延迟。",
  "Short moving average is above long moving average; strategy enters position.":
    "短期均线高于长期均线，策略建仓。",
  "Short moving average is below or equal to long moving average; strategy exits position.":
    "短期均线低于或等于长期均线，策略平仓。",
  "Past momentum return is positive; strategy enters position.":
    "过去动量收益为正，策略建仓。",
  "Past momentum return is non-positive; strategy exits position.":
    "过去动量收益非正，策略平仓。",
  "Both MA crossover and momentum signals are positive; strategy enters position.":
    "均线交叉与动量信号均为正，策略建仓。",
  "At least one of MA crossover or momentum signals is no longer positive; strategy exits position.":
    "均线交叉或动量信号至少有一个不再为正，策略平仓。",
  "At least one of MA crossover or momentum signals is positive; strategy enters position.":
    "均线交叉或动量信号至少有一个为正，策略建仓。",
  "Both MA crossover and momentum signals are non-positive; strategy exits position.":
    "均线交叉与动量信号均为非正，策略平仓。",
  "Yahoo Finance via yfinance": "雅虎财经（yfinance）",
};

export function translateBackendText(lang: Language, text: string): string {
  if (lang === "en") {
    return text;
  }
  return BACKEND_TEXT_ZH[text] ?? text;
}

export function translateStrategyName(lang: Language, strategy: string): string {
  if (strategy === "ma_crossover") {
    return t(lang, "maCrossover");
  }
  if (strategy === "momentum") {
    return t(lang, "momentumStrategy");
  }
  if (strategy === "combined_signal") {
    return t(lang, "combinedSignal");
  }
  return strategy;
}

export function translateDataSource(lang: Language, dataSource: string): string {
  return translateBackendText(lang, dataSource);
}

const COMPARISON_LABEL_ZH: Record<string, string> = {
  "Buy & Hold": "买入并持有",
  "Combined Conservative": "组合信号（保守）",
  "Combined Aggressive": "组合信号（进取）",
};

export function translateComparisonLabel(lang: Language, label: string): string {
  if (lang === "en") {
    return label;
  }
  if (COMPARISON_LABEL_ZH[label]) {
    return COMPARISON_LABEL_ZH[label];
  }
  if (label.startsWith("MA Crossover ")) {
    return `均线交叉 ${label.replace("MA Crossover ", "")}`;
  }
  if (label.startsWith("Momentum ")) {
    return `动量策略 ${label.replace("Momentum ", "")}`;
  }
  return label;
}

const COMPARISON_INTERPRETATION_ZH: Record<string, string> = {
  "Strategy comparison helps evaluate whether a rule improves return, reduces drawdown, or simply trades more often.":
    "策略对比用于评估某条规则是否提升收益、降低回撤，或只是更频繁交易。",
  "Higher return is not always better if drawdown and turnover increase significantly.":
    "若回撤与换手显著上升，更高收益未必更好。",
};

export function translateComparisonInterpretation(
  lang: Language,
  sentences: string[]
): string[] {
  if (lang === "en") {
    return sentences;
  }
  return sentences.map((sentence) => COMPARISON_INTERPRETATION_ZH[sentence] ?? sentence);
}

const OOS_INTERPRETATION_ZH: Record<string, string> = {
  "The strategy worked in-sample but failed out-of-sample, which may indicate overfitting or regime change.":
    "策略在样本内有效但在样本外失效，可能存在过拟合或市场状态变化。",
  "The strategy remained positive out-of-sample, which is a better validation sign.":
    "策略在样本外仍保持正收益，这是更好的验证信号。",
  "The strategy underperformed buy-and-hold in the out-of-sample period.":
    "策略在样本外区间跑输买入并持有。",
  "The strategy reduced downside risk versus buy-and-hold out-of-sample.":
    "策略在样本外相较买入并持有降低了下行风险。",
  "Out-of-sample validation helps test whether a strategy generalizes beyond the period used for initial research.":
    "样本外验证有助于检验策略是否能超出初始研究区间泛化。",
};

export function translateOOSInterpretation(
  lang: Language,
  sentences: string[]
): string[] {
  if (lang === "en") {
    return sentences;
  }
  return sentences.map((sentence) => OOS_INTERPRETATION_ZH[sentence] ?? sentence);
}

export function getOOSMetricRows(lang: Language) {
  return [
    { label: t(lang, "totalReturn"), key: "total_return", format: "percent" as const },
    { label: t(lang, "benchmarkReturn"), key: "benchmark_return", format: "percent" as const },
    { label: t(lang, "cagr"), key: "cagr", format: "percent" as const },
    { label: t(lang, "sharpe"), key: "sharpe_ratio", format: "sharpe" as const },
    {
      label: t(lang, "strategyMaxDd"),
      key: "strategy_max_drawdown",
      format: "percent" as const,
    },
    {
      label: t(lang, "benchmarkMaxDd"),
      key: "benchmark_max_drawdown",
      format: "percent" as const,
    },
    { label: t(lang, "volatility"), key: "volatility", format: "percent" as const },
    { label: t(lang, "trades"), key: "number_of_trades", format: "trades" as const },
  ];
}

export function getOOSSegmentLabels(lang: Language): Record<
  "full_period" | "in_sample" | "out_of_sample",
  string
> {
  return {
    full_period: t(lang, "fullPeriod"),
    in_sample: t(lang, "inSample"),
    out_of_sample: t(lang, "outOfSample"),
  };
}

export type ChartLabels = ReturnType<typeof getChartLabels>;

export function getChartLabels(lang: Language) {
  return {
    strategyVsHold: t(lang, "chartStrategyVsHold"),
    strategyVsHoldDrawdown: t(lang, "chartStrategyVsHoldDrawdown"),
    strategy: t(lang, "chartStrategy"),
    buyHold: t(lang, "chartBuyHold"),
    strategyDrawdown: t(lang, "chartStrategyDrawdown"),
    benchmarkDrawdown: t(lang, "chartBenchmarkDrawdown"),
    close: t(lang, "chartClose"),
    backtestZoomHint: t(lang, "chartBacktestZoomHint"),
    chartZoomHint: t(lang, "chartZoomHint"),
    noBacktestData: t(lang, "noBacktestData"),
    noChartData: t(lang, "noChartData"),
    noCompareData: t(lang, "noCompareData"),
  };
}
