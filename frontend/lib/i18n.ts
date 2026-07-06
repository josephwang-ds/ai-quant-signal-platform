export type Language = "en" | "zh";

export const LANGUAGE_STORAGE_KEY = "ai-quant-language";

export const translations = {
  en: {
    appTitle: "AI Quant Signal Platform",
    appSubtitle:
      "Learning-stage quant research dashboard for signal scoring, backtesting, and robustness checks.",
    educationalDemo: "Educational Demo",
    dailyMarketData: "Daily Market Data",
    notFinancialAdvice: "Not Financial Advice",
    navBacktesting: "Backtesting",
    navSensitivity: "Parameter Sensitivity",
    navOos: "OOS Validation",
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
    downloadStartDate: "Download Start Date",
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
    chartRange: "Chart Range",
    rows: "Rows",
    closeMaTitle: "{ticker} — Close, MA20, MA60",
    closeMaCaption:
      "Close is the daily closing price. MA20 and MA60 smooth the price to show short-term and medium-term trend.",
    compareChartTitle: "Normalized Close Comparison (Day 1 = 100)",
    compareChartCaption:
      "Normalized means every ticker starts at 100, making relative performance easier to compare even when prices are different.",

    strategyResearch: "Strategy Research",
    strategyResearchDesc:
      "After signal inspection, the professional question is whether the rule beats a simple benchmark and survives robustness checks.",

    backtesting: "Backtesting",
    backtestingDesc:
      "Core read order: compare strategy return with benchmark, then check Sharpe, drawdown, volatility, and trade count.",
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
      "Rule-based educational interpretation. Not financial advice.",
    backtestFailed: "Failed to run backtest.",

    sensitivityAnalysis: "Parameter Sensitivity Analysis",
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
      "This sensitivity analysis is for educational research only. It is not parameter optimization and not financial advice.",
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
      "Out-of-sample validation is for educational research only. It is not parameter optimization and not financial advice.",
    split: "Split",
    oosFailed: "Failed to run OOS validation.",

    footerLine1: "For educational and portfolio demonstration purposes only.",
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
    demoBacktestingCard: "Backtesting",
    demoBacktestingDesc:
      "Evaluate strategy return, benchmark return, drawdown, Sharpe ratio, and transaction costs.",
    demoRobustness: "Robustness Checks",
    demoRobustnessDesc:
      "Use parameter sensitivity and out-of-sample validation to reduce overclaiming.",
    aboutThisDemo: "About This Demo",
    aboutThisDemoText:
      "This is a learning-stage quant research dashboard for educational and portfolio demonstration purposes. It uses daily historical market data and simplified backtesting assumptions. It is not financial advice and is not intended for live trading.",
  },
  zh: {
    appTitle: "AI 量化信号平台",
    appSubtitle: "用于信号评分、回测和稳健性验证的学习型量化研究看板。",
    educationalDemo: "学习演示",
    dailyMarketData: "日线市场数据",
    notFinancialAdvice: "非投资建议",
    navBacktesting: "回测",
    navSensitivity: "参数敏感性",
    navOos: "样本外验证",
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
    downloadStartDate: "下载起始日期",
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
    chartRange: "图表区间",
    rows: "行数",
    closeMaTitle: "{ticker} — 收盘价、MA20、MA60",
    closeMaCaption:
      "收盘价为每日收盘价格，MA20 与 MA60 用于平滑价格并展示短中期趋势。",
    compareChartTitle: "归一化收盘价对比（首日 = 100）",
    compareChartCaption:
      "归一化表示每个标的从 100 起步，便于在价格不同的情况下比较相对表现。",

    strategyResearch: "策略研究",
    strategyResearchDesc:
      "完成信号检查后，核心问题是：该规则能否跑赢简单基准，并通过稳健性检验。",

    backtesting: "回测",
    backtestingDesc:
      "核心阅读顺序：先对比策略与基准收益，再看 Sharpe、回撤、波动率与交易次数。",
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
    backtestInterpretationNote: "基于规则的教育性解读，非投资建议。",
    backtestFailed: "回测运行失败。",

    sensitivityAnalysis: "参数敏感性分析",
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
      "本敏感性分析仅供学习研究，不是参数优化，也不是投资建议。",
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
      "样本外验证仅供学习研究，不是参数优化，也不是投资建议。",
    split: "切分",
    oosFailed: "样本外验证运行失败。",

    footerLine1: "仅供学习与作品集演示。",
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
    demoBacktestingCard: "回测",
    demoBacktestingDesc: "评估策略收益、基准收益、回撤、Sharpe 比率和交易成本。",
    demoRobustness: "稳健性检验",
    demoRobustnessDesc: "通过参数敏感性和样本外验证，避免只看单一历史最优结果。",
    aboutThisDemo: "关于本演示",
    aboutThisDemoText:
      "这是一个学习阶段的量化研究看板，用于教育、作品集和研究演示。项目使用历史日线数据和简化回测假设，不构成投资建议，也不用于实盘交易。",
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
};

export function translateBackendText(lang: Language, text: string): string {
  if (lang === "en") {
    return text;
  }
  return BACKEND_TEXT_ZH[text] ?? text;
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
