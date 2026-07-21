export type Language = "en" | "zh";

export const LANGUAGE_STORAGE_KEY = "ai-quant-language";

export const translations = {
  en: {
    appTitle: "AI Quant Research Workspace",
    appTitleShort: "Quant Research",
    appSubtitle:
      "A research workspace for experiments, evidence, and decisions — demo only.",
    educationalDemo: "Research Demo",
    dailyMarketData: "Daily Market Data",
    notFinancialAdvice: "Not Financial Advice",
    navOverview: "Overview",
    navResearchWorkspace: "Research",
    navGroupCockpit: "Decision Cockpit",
    navStrategyHealthScore: "Health Score",
    navReturnQualityLens: "Return Lens",
    navRiskGateReview: "Risk Gate",
    navScenarioShockTest: "Shock Test",
    navDecisionLedger: "Decision Ledger",
    navDecisionRoom: "Decision Room",
    navGroupResearch: "Research",
    navGroupTools: "Research Tools",
    navGroupArchive: "Archive",
    navDataCenter: "Data",
    navMarketWatch: "Markets",
    navStrategyLab: "Backtest",
    navComparison: "Compare",
    navRobustness: "Robustness",
    navModelLab: "Model Lab",
    navExperiments: "Runs",
    navPaperTrading: "Paper",
    navResearchNotes: "Notes",
    navAiAgent: "AI Assistant",
    navBacktesting: "Backtesting",
    navSensitivity: "Sensitivity",
    navOos: "OOS Check",
    langEnglish: "English",
    langChinese: "中文",

    backendHealth: "Backend Health",
    backendHealthHint: "Checks whether the data API is alive.",
    status: "Status",
    service: "Service",
    checkBackend: "Check Backend",
    checking: "Checking...",
    backendUnreachable:
      "The research backend is currently unavailable or starting up. Try again shortly.",

    marketWatch: "Markets",
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

    strategyLab: "Backtest",
    strategyLabDesc:
      "Select a decision method and compare how each rule triggers simulated position changes in backtest.",
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
    strategyComparison: "Compare",
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
      "Rule-based research commentary. Not investment advice.",
    backtestReviewTitle: "Backtest Review",
    backtestReviewDesc:
      "Governance-oriented summary of simulated backtest quality, risk level, and paper trading readiness.",
    backtestReviewNote:
      "Rule-based review only. Simulated backtest context — not a trading recommendation.",
    backtestReviewKeyFindings: "Key Findings",
    backtestReviewRiskLevel: "Backtest Risk Level",
    backtestReviewPaperEligibility: "Paper Trading Eligibility",
    backtestReviewManagement: "Management Interpretation",
    backtestReviewEligible: "Eligible for Paper Trading",
    backtestReviewWatch: "Watch Before Paper Trading",
    backtestReviewNotEligible: "Not Eligible Yet",
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

    saveBacktestRun: "Save Run",
    savingBacktestRun: "Saving...",
    experimentNotes: "Notes",
    experimentNotesPlaceholder: "Optional research notes for this run",
    saveBacktestSuccess: "Backtest run saved to Experiments.",
    saveBacktestFailed: "Could not save backtest run.",
    saveRequiresResult: "Run a backtest before saving.",
    openExperiments: "View saved runs",

    experimentsPageTitle: "Saved Runs",
    experimentsPageDesc:
      "Browse saved backtests, open details, and compare results side by side.",
    experimentsListTitle: "Run List",
    experimentsListDesc: "Filter and sort saved runs. Click a row for details, or select rows to compare.",
    experimentsLoading: "Loading saved experiments...",
    experimentsEmpty: "No saved experiments yet. Save a run from Strategy Lab.",
    experimentsLoadFailed: "Could not load experiments.",
    experimentsDetail: "Run Detail",
    experimentsBackToList: "Back to list",
    experimentsCreatedAt: "Saved at",
    experimentsTradeCount: "Trades",
    experimentsSelectHint: "Click a row to view full details.",
    experimentsDelete: "Delete",
    experimentsDeleted: "Experiment deleted.",
    experimentsDeleteFailed: "Could not delete experiment.",
    experimentsNotes: "Notes",
    experimentsConfig: "Strategy Config",
    experimentsNoTrades: "No trades saved for this run.",

    experimentsCompareTitle: "Compare Runs",
    experimentsCompareDesc: "Select 2–4 saved runs to compare key metrics.",
    experimentsCompareSelect: "Compare",
    experimentsCompareClear: "Clear selection",
    experimentsCompareNeedTwo: "Select at least 2 runs to compare.",
    experimentsCompareMax: "You can compare up to 4 runs at once.",
    experimentsCompareSummary: "Comparison Highlights",
    experimentsCompareBestReturn: "Best total return",
    experimentsCompareBestSharpe: "Best Sharpe",
    experimentsCompareLowestDrawdown: "Lowest drawdown",
    experimentsCompareRunLabel: "Run",

    experimentsFilterTicker: "Ticker filter",
    experimentsFilterStrategy: "Strategy filter",
    experimentsFilterAll: "All",
    experimentsSortBy: "Sort by",
    experimentsSortDirection: "Direction",
    experimentsSortCreatedAt: "Created time",
    experimentsSortTotalReturn: "Total return",
    experimentsSortSharpe: "Sharpe ratio",
    experimentsSortDrawdown: "Max drawdown",
    experimentsSortAsc: "Ascending",
    experimentsSortDesc: "Descending",
    experimentsShowingCount: "Showing {shown} of {total} saved runs",
    experimentsFilterEmpty: "No saved runs match the current filters.",
    experimentsFilterReset: "Reset filters",
    experimentsRunId: "Run ID",
    experimentsDeleteConfirm: "Delete this saved experiment? This cannot be undone.",
    experimentsSavedRedirect: "Backtest run saved. Showing experiment detail.",
    experimentsDetailEmpty: "Select a saved run to view metrics, config, and trades.",

    researchListEyebrow: "Research",
    researchListTitle: "Research",
    researchListSubtitle:
      "One research question per thread. Experiments, evidence, and conclusions live inside it.",
    researchListNewResearch: "New Research",
    researchListCreateResearch: "Create Research",
    researchListLoadDemo: "Load Demo Research",
    researchListDemoLoaded: "Demo research restored to the list.",
    researchListCreated: "Research created locally.",
    researchListCreateFailed: "Could not create research. Please retry.",
    researchListKpiResearch: "Total Research",
    researchListSummaryAria: "Research workspace summary",
    researchListKpiDefined: "Draft / Defined",
    researchListKpiEvidenceAvailable: "Running / Evidence Available",
    researchListKpiReviewArchived: "Needs Review / Archived",
    researchListEvidenceStatus: "Evidence status",
    researchListQuestionLabel: "Question",
    researchListLatestEvidence: "Latest Evidence",
    researchListModalName: "Research Title",
    researchListModalNameRequired: "Research title is required.",
    researchListModalQuestion: "Research Question",
    researchListModalHypothesis: "Hypothesis",
    researchListModalHypothesisRequired: "Hypothesis is required.",
    researchListModalLocalNote:
      "Creates a research question in this browser. Experiments are designed inside the research later — metrics come from the backend.",
    researchListModalQuestionRequired: "Research question is required.",
    researchListModalSymbolRequired: "Symbol is required.",
    researchListModalShortInvalid: "Short MA window must be a positive integer.",
    researchListModalLongInvalid:
      "Long MA window must be an integer greater than the short window.",
    researchListModalDateInvalid: "Start date must be before end date.",
    researchListModalCostInvalid: "Transaction cost cannot be negative.",
    researchListModalTagsHint: "Optional — comma-separated tags",
    researchListModalCreate: "Create",
    researchListModalCancel: "Cancel",
    researchListTemplateMa: "Moving Average",
    researchListTemplateMomentum: "Momentum",
    researchListTemplateMeanReversion: "Mean Reversion",
    researchListTemplateCustom: "Custom",
    researchListSearch: "Search",
    researchListSearchPlaceholder: "Search by title or question…",
    researchListFilterStatus: "Status",
    researchListFilterOwner: "Owner",
    researchListFilterTag: "Tag",
    researchListFilterAll: "All",
    researchListSort: "Sort",
    researchListSortUpdated: "Recently updated",
    researchListSortCreated: "Recently created",
    researchListSortName: "Name (A–Z)",
    researchListSortConfidence: "Confidence (high first)",
    researchListLoading: "Loading research…",
    researchListErrorTitle: "Research list unavailable",
    researchListRetry: "Retry",
    researchListResultCount: "research items shown",
    researchListEmptyFilterTitle: "No research matches these filters",
    researchListEmptyFilterDescription:
      "Try clearing filters or broadening your search terms.",
    researchListClearFilters: "Clear filters",
    researchListEmptyTitle: "No research yet",
    researchListEmptyDescription:
      "Start with a research question, or load the Trend Following demo to explore the workspace.",
    researchListOpenWorkspace: "Open Workspace",
    researchListDuplicate: "Duplicate",
    researchListArchive: "Archive",
    researchListMore: "More",
    researchListMoreTodo: "More actions coming soon",
    researchListDuplicated: "Project duplicated locally (mock).",
    researchListArchived: "Research archived locally.",
    researchListExperimentCount: "Experiments",
    researchListLastValidation: "Last validation",
    researchListRecommendation: "Recommendation",
    researchListUpdated: "Updated",
    researchListOwner: "Owner",
    researchListConfidence: "Confidence",
    researchListEvaluationArea: "Evaluation",
    researchListSymbol: "Symbol",
    researchListBenchmark: "Benchmark",
    researchListStrategy: "Strategy",
    researchListDataStatus: "Data status",
    researchListMetricsStatus: "Metrics status",
    researchListValidationStatus: "Validation status",
    researchListEvaluationStatus: "Evaluation status",

    researchWsBackToList: "Back to Research",
    researchWsMoreActions: "More actions",
    researchWsMoreActionsHint:
      "Rename, share, and destructive actions are deferred. No changes are applied in this mock.",
    researchWsCreated: "Created",
    researchWsTags: "Tags",
    researchWsLoading: "Loading research workspace…",
    researchWsErrorTitle: "Research workspace unavailable",
    researchWsRetry: "Retry",
    researchWsNotFoundTitle: "Research not found",
    researchWsNotFoundDescription:
      "No research matches this ID. Return to the Research list to pick a valid item.",
    researchWsNavOverview: "Overview",
    researchWsNavNotebook: "Notes",
    researchWsNavExperiments: "Experiments",
    researchWsNavValidation: "Evidence",
    researchWsNavEvaluation: "Review",
    researchWsNavCopilot: "Copilot",
    researchWsNavTimeline: "Timeline",
    researchWsNavFiles: "Files",
    researchWsNavSettings: "Settings",
    researchWsNavTools: "Supporting tools",
    researchWsProgressTitle: "Research Progress",
    researchWsProgressResearch: "Research",
    researchWsProgressExperiments: "Experiments",
    researchWsProgressEvidence: "Evidence",
    researchWsProgressDecision: "Decision",
    researchWsQuickActionsTitle: "Quick Actions",
    researchWsQuickRunExperiment: "Run Experiment",
    researchWsQuickOpenValidation: "Open Validation",
    researchWsQuickGenerateReview: "Generate Review",
    researchWsRecentExperiments: "Recent Experiments",
    researchWsLatestEvidence: "Latest Evidence",
    researchWsCurrentDecision: "Current Decision",
    researchWsNoExperiments: "No experiments yet — define the first protocol.",
    researchWsNoEvidence: "No evidence packages yet.",
    researchWsDecisionPending: "Decision pending evidence and review.",
    researchWsKeyResultsUnavailable:
      "Run the research to calculate historical evidence.",
    researchWsOosSharpeUnavailable:
      "Run validation to calculate out-of-sample Sharpe ratio.",
    researchWsGuidedWorkflowTitle: "Steps",
    researchWsStepRunResearch: "Run Research",
    researchWsStepValidateEvidence: "Stress-test",
    researchWsStepReviewEvaluation: "Evidence check",
    researchWsStepAskCopilot: "Ask Copilot",
    researchWsGuidedLoading: "In progress…",
    researchWsGuidedFailed: "Needs attention",
    researchWsGuidedUnavailableAfterExecution:
      "Complete historical execution first.",
    researchWsGuidedUnavailableAfterValidation:
      "Run validation before requesting evaluation.",
    researchWsGuidedUnavailableAfterEvaluation:
      "Request evaluation before asking Copilot.",
    researchWsNextStepTitle: "Next step",
    researchWsNextStepRunResearchTitle: "Run Research",
    researchWsNextStepRunResearchDescription:
      "Calculate historical evidence using the configured protocol.",
    researchWsNextStepRunResearchCta: "Run Research",
    researchWsNextStepRunResearchLoadingCta: "Running research…",
    researchWsNextStepRunResearchRetryCta: "Retry research",
    researchWsNextStepValidateTitle: "Validate Evidence",
    researchWsNextStepValidateDescription:
      "Run deterministic OOS, parameter, cost, and data-quality checks.",
    researchWsNextStepValidateCta: "Run Validation",
    researchWsNextStepEvaluateTitle: "Review Evaluation",
    researchWsNextStepEvaluateDescription:
      "Summarize evidence coverage and outstanding requirements.",
    researchWsNextStepEvaluateCta: "Request Evaluation",
    researchWsNextStepCopilotTitle: "Ask Copilot",
    researchWsNextStepCopilotDescription:
      "Ask questions grounded in the existing evidence.",
    researchWsNextStepCopilotCta: "Open Copilot",
    researchWsConclusionNotRequested: "Evaluation has not been requested.",
    researchWsConclusionIncomplete:
      "Current evidence does not support a final research decision.",
    researchWsConclusionBlocked:
      "Evaluation is blocked by required evidence.",
    researchWsEvidencePreview: "Evidence preview",
    researchListNextStep: "Next step",
    researchListNextStepRunResearch: "Run research",
    researchListNextStepValidate: "Validate evidence",
    researchListNextStepEvaluate: "Request evaluation",
    researchListNextStepReview: "Review evaluation",
    researchWsQuestion: "Research question",
    researchWsHypothesis: "Hypothesis",
    researchWsObjective: "Research objective",
    researchWsCurrentStage: "Current stage",
    researchWsConfidence: "Research confidence",
    researchWsSummary: "Research summary",
    researchWsEvidenceNarrative: "Evidence summary",
    researchWsValidationSummary: "Validation summary",
    researchWsKeyStrengths: "Key strengths",
    researchWsKnownWeaknesses: "Known weaknesses",
    researchWsOpenQuestions: "Open questions",
    researchWsNextActions: "Next actions",
    researchWsLifecycleTitle: "Research lifecycle",
    researchWsLifecycleDescription:
      "Authoritative progress stages from Architecture Bible Chapter 3. Completed, current, and upcoming stages are labeled explicitly.",
    researchWsEvidenceTitle: "Evidence checklist",
    researchWsEvidenceDescription:
      "Deterministic evidence packages only. Status and concise results — not trading signals.",
    researchWsEvidencePreviewTitle: "Linked evidence (preview)",
    researchWsEvidencePreviewDescription:
      "A subset of evidence from Overview, shown here for context while this section is still a placeholder.",
    researchWsActionsTitle: "Workspace actions",
    researchWsActionsDescription:
      "Use the available research workflows and navigate between evidence stages.",
    researchWsActionNotebook: "Add Notebook Entry",
    researchWsActionExperiment: "Create Experiment",
    researchWsActionValidation: "Run Validation",
    researchWsActionValidationRunning: "Running Validation…",
    researchWsActionEvaluation: "Request Evaluation",
    researchWsActionCopilot: "Open Research Copilot",
    researchWsActionExport: "Export Research",
    researchWsActionHintNotebook: "Open research notes.",
    researchWsActionHintExperiment: "Open planned experiments.",
    researchWsActionHintValidation:
      "Run deterministic validation on the current execution evidence.",
    researchWsActionHintEvaluation:
      "Review governance conclusions derived from validation evidence.",
    researchWsActionHintEvaluationDisabled: "Run Validation first.",
    researchWsActionHintCopilot:
      "Ask questions grounded in current research evidence.",
    researchWsActionHintCopilotDisabled: "Run Validation first.",
    researchWsActionHintExport: "Export is not available in this release.",
    researchWsComingLater: "Coming in a later PR",
    researchWsDeferredNote:
      "Deferred to a later PR. No workflows are executable in this definition-only state.",
    researchWsExecutionPendingNote:
      "Market-derived evidence will be populated by the Research Execution Engine. Invented pass/fail outcomes and scores are not shown.",
    researchWsStrategyConfig: "Strategy configuration",
    researchWsDataRequirements: "Data requirements",
    researchWsNotebookTitle: "Notebook",
    researchWsNotebookSummary:
      "The notebook will hold dated research notes, assumption changes, and interpretation clearly separated from quantitative facts.",
    researchWsNotebookCap1: "Append-only entries with author and timestamp",
    researchWsNotebookCap2: "Links from notes to Evidence and Experiment IDs",
    researchWsNotebookCap3: "Distinction between fact, calculation, and interpretation",
    researchWsExperimentsTitle: "Experiments",
    researchWsExperimentsSummary:
      "Experiments will list designed, approved, running, and terminal runs bound to this research plan.",
    researchWsExperimentsCap1: "Experiment registry with protocol versions",
    researchWsExperimentsCap2: "Start/stop is Application-owned — not UI-side execution",
    researchWsExperimentsCap3: "Terminal outcomes feed Evidence candidates",
    researchWsValidationTitle: "Validation",
    researchWsValidationSectionSummary:
      "Validation stages for MA Crossover on SPY. Outcomes remain Not Started or Awaiting Data until real historical series are calculated.",
    researchWsValidationCap1: "Historical backtest and benchmark comparison from real prices",
    researchWsValidationCap2: "Chronological OOS and bounded sensitivity (no shuffled series)",
    researchWsValidationCap3: "Transaction-cost and data-quality reviews before Evaluation",
    researchWsValidationNotStarted: "Not Started",
    researchWsValidationAwaitingData: "Awaiting Data",
    researchWsValidationCompleted: "Completed",
    researchValSummary:
      "Backend-derived validation evidence. Statuses and metrics are displayed as returned and are not recalculated in the browser.",
    researchValLoading: "Loading validation evidence from backend…",
    researchValUnavailableTitle: "Validation evidence unavailable",
    researchValUnavailableDescription:
      "The backend did not return validation evidence. Mock outcomes are not shown.",
    researchValRetry: "Retry validation",
    researchValStatus: "Status",
    researchValEvidenceComplete: "Evidence complete",
    researchValYes: "Yes",
    researchValNo: "No",
    researchValIncomplete: "Incomplete",
    researchValFailed: "Failed",
    researchValUnavailable: "Unavailable",
    researchValSource: "Source",
    researchValGenerated: "Generated",
    researchValRules: "Rules",
    researchValWarnings: "Review items",
    researchValDataNotes: "Data notes",
    researchValBlockers: "Blockers",
    researchValEvidence: "Evidence",
    researchValOosTitle: "Out-of-sample validation",
    researchValSplitDate: "Exact split date",
    researchValInSampleRatio: "In-sample ratio",
    researchValMinimumOos: "Minimum OOS observations",
    researchValBoundary: "Boundary convention",
    researchValInSample: "In sample",
    researchValOutOfSample: "Out of sample",
    researchValBenchmark: "OOS benchmark",
    researchValObservations: "observations",
    researchValMetric: "Metric",
    researchValTotalReturn: "Total return",
    researchValCagr: "CAGR",
    researchValSharpe: "Sharpe ratio",
    researchValMaxDrawdown: "Maximum drawdown",
    researchValVolatility: "Annualized volatility",
    researchValTrades: "Trade count",
    researchValTotalCosts: "Total transaction costs",
    researchValParameterTitle: "Parameter sensitivity",
    researchValValidCombinations: "Valid combinations",
    researchValProfitableCombinations: "Profitable combinations",
    researchValPositiveSharpe: "Positive Sharpe combinations",
    researchValMedianSharpe: "Median Sharpe",
    researchValSharpeRange: "Sharpe range",
    researchValMedianDrawdown: "Median maximum drawdown",
    researchValCanonicalPercentile: "Canonical Sharpe percentile",
    researchValShortWindow: "Short window",
    researchValLongWindow: "Long window",
    researchValCanonical: "Canonical",
    researchValCostTitle: "Transaction-cost sensitivity",
    researchValTransactionCost: "Transaction cost",
    researchValReturnDegradation: "Return degradation from zero",
    researchValSharpeDegradation: "Sharpe degradation from zero",
    researchValMathematicallyValid: "Mathematically valid",
    researchValCanonicalCost: "Canonical cost",
    researchValDataQualityTitle: "Data quality",
    researchValProvider: "Provider",
    researchValDateRange: "Actual date range",
    researchValCache: "Cache",
    researchValCacheHit: "Cache hit",
    researchValCacheMiss: "Cache miss",
    researchValFatalIssues: "Fatal issues",
    researchValChecks: "Data-quality checks",
    researchValCheck: "Check",
    researchValSeverity: "Severity",
    researchValDetails: "Details",
    researchValNotAvailable: "n/a",
    researchWsCalculatedMetrics: "Results",
    researchWsMetricTotalReturn: "Total return",
    researchWsMetricBenchReturn: "Benchmark total return",
    researchExecRealData: "Real Historical Data",
    researchExecCached: "Cached",
    researchExecStale: "Stale cache",
    researchExecProvider: "Provider",
    researchExecAssetClass: "Asset class",
    researchExecAdjustment: "Adjustment",
    researchExecSymbol: "Symbol",
    researchExecRange: "Actual date range",
    researchExecRetrieved: "Retrieved",
    researchExecDisclaimer:
      "Historical research result — not investment advice and not a forecast of future performance.",
    researchExecLoading: "Loading research execution from backend…",
    researchExecUnavailableTitle: "Research execution unavailable",
    researchExecUnavailableDescription:
      "The backend did not return calculated evidence. Invented metrics are not shown.",
    researchExecRetry: "Retry execution",
    researchWsEvaluationTitle: "Evaluation",
    researchEvalSummary:
      "Evaluation summarizes calculated PR-009 validation evidence only. It performs no new calculations, no scoring, and no investment recommendation.",
    researchEvalStatus: "Evaluation status",
    researchEvalCompleted: "Completed",
    researchEvalIncomplete: "Incomplete",
    researchEvalBlocked: "Blocked",
    researchEvalSource: "Source",
    researchEvalGenerated: "Generated",
    researchEvalCoverageTitle: "Evidence coverage",
    researchEvalImplementedStages: "Implemented stages",
    researchEvalCompletedStagesCount: "Completed stages",
    researchEvalCoveragePercentage: "Coverage",
    researchEvalCoverageDisclaimer:
      "Coverage measures implementation completeness only. It is not a confidence, quality, or robustness score.",
    researchEvalEvidenceSummaryTitle: "Evidence summary",
    researchEvalStageColumn: "Stage",
    researchEvalStatusColumn: "Status",
    researchEvalSummaryColumn: "Summary",
    researchEvalCompletedEvidenceTitle: "Completed evidence",
    researchEvalIncompleteEvidenceTitle: "Incomplete evidence",
    researchEvalOutstandingEvidenceTitle: "Still missing",
    researchEvalLimitationsTitle: "Limitations",
    researchEvalBlockersTitle: "Blockers",
    researchEvalDecisionReadiness: "Ready to decide?",
    researchEvalKeyFindings: "Key findings",
    researchEvalNextGovernanceAction: "What to do next",
    researchEvalDetailsTitle: "Evaluation details",
    researchEvalNone: "None",
    researchEvalNotAvailable: "n/a",
    researchEvalLoading: "Loading evaluation evidence from backend…",
    researchEvalUnavailableTitle: "Evaluation unavailable",
    researchEvalUnavailableDescription:
      "The backend did not return an evaluation summary. Invented evidence is not shown.",
    researchEvalRetry: "Retry evaluation",
    researchEvalAwaitingValidationTitle: "Validation evidence required",
    researchEvalAwaitingValidationDescription:
      "Run or load Validation evidence before Evaluation can be generated.",
    researchEvalGoToValidation: "Go to Validation",
    researchCopilotTitle: "Evidence-Grounded Research Copilot",
    researchCopilotSubtitle:
      "Explains existing workspace evidence. It does not calculate metrics, rerun backtests, or recommend trades.",
    researchCopilotDisclaimer:
      "Answers are interpretation only. Execution, Validation, and Evaluation remain authoritative.",
    researchCopilotSampleQuestionsTitle: "Sample questions",
    researchCopilotSample1: "Why is the current evaluation incomplete?",
    researchCopilotSample2: "What does the OOS evidence show?",
    researchCopilotSample3: "How sensitive is this strategy to transaction costs?",
    researchCopilotSample4: "What research evidence is still missing?",
    researchCopilotSample5: "How does the system prevent look-ahead bias?",
    researchCopilotQuestionPlaceholder: "Ask about evidence, validation, or governance",
    researchCopilotAskButton: "Ask Copilot",
    researchCopilotAskingButton: "Generating grounded answer…",
    researchCopilotAnswerTitle: "Answer",
    researchCopilotCitationsTitle: "Evidence citations",
    researchCopilotWarningsTitle: "Warnings",
    researchCopilotGroundingTitle: "Grounding status",
    researchCopilotGeneratedAt: "Generated at",
    researchCopilotGrounded: "Grounded",
    researchCopilotPartiallyGrounded: "Partially grounded",
    researchCopilotUnavailable: "Unavailable",
    researchCopilotAwaitingValidationTitle: "Validation evidence required",
    researchCopilotAwaitingValidationDescription:
      "Run or load Validation evidence before asking evidence-specific questions.",
    researchCopilotGoToValidation: "Go to Validation",
    researchCopilotNotConfigured:
      "Research Copilot is not configured for this deployment.",
    researchCopilotLimitations:
      "The Copilot cannot approve strategies, predict returns, or replace deterministic validation.",
    researchCopilotUnavailableTitle: "Research Copilot unavailable",
    researchCopilotUnavailableDescription:
      "This workspace section is only available for the canonical MA Crossover research.",
    researchWsTimelineTitle: "Timeline",
    researchWsTimelineSummary:
      "Timeline will show immutable domain events for this research aggregate.",
    researchWsTimelineCap1: "State transitions with actor and reason",
    researchWsTimelineCap2: "Experiment and Validation milestones",
    researchWsTimelineCap3: "Reopen and redesign events when applicable",
    researchWsFilesTitle: "Files",
    researchWsFilesSummary:
      "Files will reference versioned artifacts (configs, reports, notebooks) without becoming a generic drive.",
    researchWsFilesCap1: "Artifact metadata and checksums",
    researchWsFilesCap2: "Links to Evidence packages",
    researchWsFilesCap3: "No unrestricted upload in this PR",
    researchWsSettingsTitle: "Settings",
    researchWsSettingsSummary:
      "Settings will cover ownership, visibility, and research metadata — not trading account configuration.",
    researchWsSettingsCap1: "Owner and collaborator roles",
    researchWsSettingsCap2: "Tag and naming conventions",
    researchWsSettingsCap3: "Archive / reopen policies (governed)",

    researchNbTitle: "Notebook",
    researchNbDesignNotesTitle: "Research Design Notes",
    researchNbEntryCount: "entries",
    researchNbLastUpdated: "Last updated",
    researchNbNewEntry: "New Entry",
    researchNbLoading: "Loading notebook entries…",
    researchNbErrorTitle: "Notebook unavailable",
    researchNbRetry: "Retry",
    researchNbEmptyTitle: "No research notes yet",
    researchNbEmptyDescription:
      "Capture the first observation, hypothesis, or decision.",
    researchNbFilterEmptyTitle: "No entries match this filter",
    researchNbFilterEmptyDescription: "Try another entry type or show all entries.",
    researchNbFilterType: "Entry type",
    researchNbFilterAll: "All",
    researchNbSort: "Sort",
    researchNbSortNewest: "Newest first",
    researchNbSortOldest: "Oldest first",
    researchNbCardAuthor: "Author",
    researchNbCardCreated: "Created",
    researchNbCardEdited: "Edited",
    researchNbCardRelated: "Related artifact",
    researchNbComposerTitle: "New notebook entry",
    researchNbComposerType: "Entry type",
    researchNbComposerEntryTitle: "Title",
    researchNbComposerContent: "Content",
    researchNbComposerTags: "Tags",
    researchNbComposerTagsHint: "Comma-separated tags (optional)",
    researchNbComposerArtifact: "Related artifact (optional)",
    researchNbComposerArtifactNone: "None",
    researchNbComposerSave: "Save Entry",
    researchNbComposerCancel: "Cancel",
    researchNbValidationType: "Entry type is required.",
    researchNbValidationTitle: "Title is required.",
    researchNbValidationBody: "Content is required.",
    researchTlTitle: "Timeline",
    researchTlDescription:
      "Immutable-style activity for this research aggregate. Session notebook saves append local events only.",
    researchTlSessionNote:
      "TODO(api): replace with domain event stream from Research context.",
    researchTlEmpty: "No timeline events yet for this research project.",

    researchExpTitle: "Experiments",
    researchExpTotalCount: "experiments",
    researchExpActiveCount: "active",
    researchExpNew: "New Experiment",
    researchExpLoading: "Loading experiments…",
    researchExpErrorTitle: "Experiments unavailable",
    researchExpRetry: "Retry",
    researchExpEmptyTitle: "No experiments yet",
    researchExpEmptyDescription:
      "Design the first controlled test of this research hypothesis.",
    researchExpFilterEmptyTitle: "No experiments match these filters",
    researchExpFilterEmptyDescription: "Clear filters or broaden your search.",
    researchExpNotFoundTitle: "Experiment not found",
    researchExpNotFoundDescription:
      "No experiment matches this ID in the current research mock catalog.",
    researchExpBackToList: "Back to experiments",
    researchExpSearch: "Search",
    researchExpSearchPlaceholder: "Name, hypothesis, dataset, parameters…",
    researchExpFilterStatus: "Status",
    researchExpFilterType: "Type",
    researchExpSort: "Sort",
    researchExpFilterAll: "All",
    researchExpSortUpdated: "Recently updated",
    researchExpSortCreated: "Recently created",
    researchExpSortResult: "Result (Sharpe)",
    researchExpCardHypothesis: "Hypothesis",
    researchExpCardDataset: "Dataset / symbol",
    researchExpCardWindow: "Date range",
    researchExpCardBenchmark: "Benchmark",
    researchExpCardResult: "Result summary",
    researchExpCardReadiness: "Validation readiness",
    researchExpCardParameters: "Key parameters",
    researchExpCardLinkedNotes: "Linked notes",
    researchExpOpenDetail: "Open detail",
    researchExpComposerTitle: "New experiment (Designed)",
    researchExpComposerName: "Experiment name",
    researchExpComposerHypothesis: "Hypothesis",
    researchExpComposerType: "Experiment type",
    researchExpComposerDataset: "Dataset or symbol",
    researchExpComposerStart: "Start date",
    researchExpComposerEnd: "End date",
    researchExpComposerBenchmark: "Benchmark",
    researchExpComposerParameters: "Parameters",
    researchExpComposerParametersHint: "One per line as key=value (optional)",
    researchExpComposerSuccess: "Success criteria",
    researchExpComposerFalsify: "Falsification condition",
    researchExpComposerNotes: "Notes",
    researchExpComposerSave: "Save as Designed",
    researchExpComposerCancel: "Cancel",
    researchExpValidationName: "Experiment name is required.",
    researchExpValidationHypothesis: "Hypothesis is required.",
    researchExpValidationType: "Experiment type is required.",
    researchExpValidationDataset: "Dataset or symbol is required.",
    researchExpValidationStart: "Start date is required.",
    researchExpValidationEnd: "End date is required.",
    researchExpValidationDateRange: "Date range is invalid.",
    researchExpValidationSuccess: "Success criteria are required.",
    researchExpValidationFalsify: "Falsification condition is required.",
    researchExpDetailTitle: "Experiment detail",
    researchExpDetailClose: "Close detail",
    researchExpDetailOverview: "Overview",
    researchExpDetailConfig: "Configuration",
    researchExpDetailEvidence: "Related evidence",
    researchExpDetailNotebook: "Linked notebook entries",
    researchExpNone: "None",
    researchExpLifecycleTitle: "Experiment lifecycle",
    researchExpLifecycleDescription:
      "Designed → Approved → Running → Completed (Architecture Bible Ch3). Failed and Invalidated are terminal side states.",
    researchExpLifecycleCompleted: "Completed",
    researchExpLifecycleCurrent: "Current",
    researchExpLifecycleUpcoming: "Upcoming",
    researchExpLifecycleTerminal: "Terminal status",
    researchExpLifecycleGoverned:
      "Approve / start / complete actions are deferred. UI cannot silently violate the frozen state machine.",
    researchExpMetricsTitle: "Primary metrics",
    researchExpMetricsDisclaimer:
      "Metrics appear only after calculation by the Research Execution Engine. Historical research — not investment advice.",
    researchExpMetricSharpe: "Sharpe",
    researchExpMetricCagr: "CAGR",
    researchExpMetricMaxDD: "Max Drawdown",
    researchExpMetricVol: "Volatility",
    researchExpMetricTrades: "Trade Count",
    researchExpMetricWinRate: "Win Rate",
    researchExpMetricCost: "Total Transaction Cost",

    overviewTitle: "Workspace Overview",
    overviewDesc:
      "A directory of research workspace modules grouped by area, each labeled with an honest availability status — available, in progress, or not started.",
    executiveCockpit: "Executive Cockpit",
    executiveCockpitDesc:
      "Leadership view of simulated portfolio posture, risk gates, and decision traceability. For governance review only.",
    executiveCockpitTileDesc:
      "Six-panel entry to simulated decision support: health, return quality, risk gates, shocks, and audit trail.",
    cockpitGridTitle: "Decision Cockpit Modules",
    cockpitGridDesc:
      "Each panel supports simulated review workflows. No live orders or investment advice.",
    cockpitDisclaimer:
      "Simulated decision support only. Not financial advice. No live trading.",
    cockpitNav: "Simulated NAV",
    cockpitYtdReturn: "YTD Return (Simulated)",
    cockpitMaxDrawdown: "Max Drawdown",
    cockpitSharpe: "Sharpe Ratio",
    cockpitRiskLevel: "Risk Level",
    categoryDecisionCockpit: "Decision Cockpit",
    strategyHealthScore: "Strategy Health Score",
    strategyHealthScoreDesc:
      "Composite simulated health score from drawdown, Sharpe drift, cost drag, and risk-governance signals.",
    returnQualityLens: "Return Quality Lens",
    returnQualityLensDesc:
      "Simulated return attribution and quality lens for leadership review — not a performance guarantee.",
    returnQualityLensModuleNote:
      "Return Quality Lens is designed to evaluate whether simulated returns are supported by acceptable drawdown, cost efficiency, and risk-adjusted performance.",
    returnQualityLensSimulatedNote:
      "Simulated return and risk-adjusted metrics for governance review only. Not financial advice.",
    returnQualityExcessReturn: "Excess Return",
    returnQualityMaxDrawdown: "Max Drawdown",
    returnQualityCostDrag: "Cost Drag",
    returnQualityHitRate: "Hit Rate",
    returnQualityProfitFactor: "Profit Factor",
    returnQualityCapitalAtRisk: "Capital at Risk",
    returnQualityDrawdownBuffer: "Drawdown Buffer to Red Level",
    riskGateReview: "Risk Gate Review",
    riskGateReviewDesc:
      "Five-level risk governance panel: signal intake, gate checks, and allowed simulated actions.",
    riskGateReviewModuleNote:
      "Strategy signals do not flow directly into simulated actions. The risk gate reviews drawdown, volatility, consecutive losses, and signal conflicts before allowing paper trading, limiting adds, or placing the session on watch.",
    riskGateSimulatedNote:
      "Simulated paper-trading governance flow only. No real orders or live execution.",
    riskGateStepStrategySignal: "Strategy Signal",
    riskGateStepGateReview: "Risk Gate Review",
    riskGateStepFinalAction: "Final Paper Action",
    riskGateRawSignal: "Raw Signal",
    riskGateRiskLevel: "Risk Level",
    riskGateDecision: "Gate Decision",
    riskGateReasons: "Reasons",
    scenarioShockTest: "Scenario Shock Test",
    scenarioShockTestDesc:
      "This module simulates how strategy NAV, drawdown, and risk level may react under predefined market shock scenarios. It is not a market prediction.",
    scenarioShockTestNote:
      "Simulated shock scenarios for risk contingency planning only. Not financial advice and not a forecast.",
    scenarioShockNavImpact: "NAV Impact",
    scenarioShockRiskAfter: "Risk Level After Shock",
    scenarioShockTriggeredRules: "Triggered Rules",
    scenarioShockSystemAction: "System Action",
    scenarioShockInterpretation: "Management Interpretation",
    decisionLedger: "Decision Ledger",
    decisionLedgerDesc:
      "A traceable ledger of strategy signals, risk gate decisions, paper actions, human notes, and follow-up outcomes.",
    decisionLedgerNote:
      "Governance audit trail with human-in-the-loop review. Not a trade blotter — every row documents accountability and follow-up.",
    ledgerDate: "Date",
    ledgerSymbol: "Symbol",
    ledgerStrategy: "Strategy",
    ledgerRawSignal: "Raw Signal",
    ledgerRiskLevel: "Risk Level",
    ledgerGateDecision: "Gate Decision",
    ledgerFinalPaperAction: "Final Paper Action",
    ledgerExplanation: "Explanation",
    ledgerHumanNote: "Human Note",
    ledgerOutcome: "Outcome",
    decisionRoom: "Decision Room",
    decisionRoomDesc:
      "This module explains how a raw strategy signal is reviewed by the risk gate and translated into a simulated paper action. It does not provide investment advice.",
    decisionRoomNote:
      "Mock AI decision explanations for governance demo only. No live LLM. No real trading.",
    decisionRoomSignalSnapshot: "Signal Snapshot",
    decisionRoomRolesTitle: "Decision Room — Three Perspectives",
    decisionRoomRetrievedContext: "Retrieved Risk Context",
    decisionRoomRagNote:
      "Simulated RAG snippets from risk_knowledge docs. Not live retrieval in this demo.",
    decisionRoomReviewQuestions: "Review Questions",
    moduleDecisionRoomOverviewDesc:
      "AI-style explanations of signal → gate → paper action with mock retrieved policy context.",
    moduleStrategyHealthScoreOverviewDesc:
      "Weighted simulated health score for strategy governance checkpoints.",
    moduleReturnQualityLensOverviewDesc:
      "Return quality and attribution lens for simulated leadership review.",
    moduleRiskGateReviewOverviewDesc:
      "Risk gate workflow: signal → gate review → allowed simulated action.",
    moduleScenarioShockTestOverviewDesc:
      "Predefined shock library for simulated NAV, drawdown, and risk-level contingency review.",
    moduleDecisionLedgerOverviewDesc:
      "Traceable audit ledger for signals, gate decisions, human notes, and review outcomes.",
    strategyHealthScorePlaceholderSummary:
      "Strategy Health Score is planned as a composite score built only from real Validation and Evaluation evidence. No scoring methodology exists yet, so no score is shown.",
    strategyHealthScorePlaceholderCap1:
      "Composite score derived from real Sharpe, drawdown, and cost-drag evidence",
    strategyHealthScorePlaceholderCap2:
      "Backed by completed Validation and Evaluation results, not simulated pillars",
    strategyHealthScorePlaceholderCap3:
      "Published only after a scoring methodology is defined and reviewed",
    returnQualityLensPlaceholderSummary:
      "Return Quality Lens is planned to show real return attribution, cost drag, and hit-rate evidence once produced by the Research Execution and Validation engines. No simulated figures are shown.",
    returnQualityLensPlaceholderCap1:
      "Return, benchmark, and excess-return figures sourced from real execution evidence",
    returnQualityLensPlaceholderCap2:
      "Cost drag and hit rate derived from real validation stage results",
    returnQualityLensPlaceholderCap3:
      "Available once a strategy completes Execution and Validation",
    riskGateReviewPlaceholderSummary:
      "Risk Gate Review is planned to apply deterministic governance rules to real strategy evidence. No simulated signal, gate decision, or paper action is shown until those rules and evidence exist.",
    riskGateReviewPlaceholderCap1:
      "Deterministic risk-gate rules applied to real Evaluation evidence",
    riskGateReviewPlaceholderCap2:
      "Signal, gate decision, and action traced to source, never simulated",
    riskGateReviewPlaceholderCap3:
      "Governed by explicit guardrails reviewed before publication",
    scenarioShockTestPlaceholderSummary:
      "Scenario Shock Test is planned to run stress and regime scenarios against real strategy history. No simulated NAV, drawdown, or risk-level outcome is shown until that capability exists.",
    scenarioShockTestPlaceholderCap1:
      "Stress testing and regime analysis against real validated evidence",
    scenarioShockTestPlaceholderCap2:
      "NAV, drawdown, and risk-level impact computed, never simulated",
    scenarioShockTestPlaceholderCap3:
      "Delivered as part of the Robustness capability roadmap",
    decisionLedgerPlaceholderSummary:
      "Decision Ledger is planned to record real governance decisions with human accountability once Risk Gate Review and Decision Room are backed by real evidence. No simulated entries are shown.",
    decisionLedgerPlaceholderCap1:
      "Ledger entries backed by real signal, gate decision, and outcome evidence",
    decisionLedgerPlaceholderCap2:
      "Human review notes tied to an auditable decision record",
    decisionLedgerPlaceholderCap3:
      "Populated once governance decisions are made on real strategies",
    decisionRoomPlaceholderSummary:
      "Decision Room is planned to explain how a real signal moves through risk governance into a paper-trading action, with AI interpretation clearly labeled and traceable to evidence. No simulated roles or retrieval snippets are shown.",
    decisionRoomPlaceholderCap1:
      "AI interpretation of real signal, gate, and action evidence, clearly labeled",
    decisionRoomPlaceholderCap2:
      "Retrieved context traced to real policy and evidence sources",
    decisionRoomPlaceholderCap3:
      "Available once governed AI review is implemented",
    publicPreviewDeferredNote:
      "Deferred until real research evidence exists. Fabricated demo data has been removed from this preview.",
    overviewStatusLegend:
      "Module tags: Available = ready to use now · In progress = placeholder page · Not started = on the roadmap.",
    categoryCoreResearch: "Core Research",
    categoryDataStorage: "Data & Storage",
    categoryModelAi: "Model & AI",
    categorySystemNotes: "System Notes",
    statusActive: "Available",
    statusBasicSupport: "Partial",
    statusPlanned: "In progress",
    statusComingLater: "Not started",
    comingSoonTitle: "Coming soon",
    openModule: "Open",
    openLegacyDemo: "Open full demo",
    legacyDemoHint:
      "Full functionality is temporarily on the legacy dashboard while this module is being migrated.",
    modulePlannedStatus: "This module is not ready yet. The page is only a placeholder.",
    moduleMigratingStatus: "This module is ready to use.",

    dataCenter: "Data",
    dataCenterPageDesc:
      "Manage data source coverage, symbol formats, asset classes, and future provider integration.",
    dataCenterDesc:
      "Documents current Yahoo/yfinance coverage, asset classes, symbol formats, and the planned multi-source roadmap.",
    dcCurrentActiveProvider: "Current Active Provider",
    dcLiveProviderStatus: "Configured Provider Status",
    dcActiveProvider: "Active Provider",
    dcPreferredSource: "Preferred Data Source",
    dcPreferredSourceDesc:
      "Default is auto (AKShare → Yahoo → Stooq). Lock a source to force it; failed locked sources do not fall back.",
    dcPreferredSourceOptionAuto: "auto (failover)",
    dcPreferredSourceOptionAkshare: "akshare",
    dcPreferredSourceOptionYahoo: "yahoo",
    dcPreferredSourceOptionStooq: "stooq",
    dcProbeSource: "Probe AAPL",
    dcProbeLoading: "Probing...",
    dcProbeSuccess: "Hit source",
    dcProbeError: "Probe failed",
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
    dcSourcePlanned: "Not connected",
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
    dcAssetCnAkShare: "China A-share (mainland)",
    dcAssetCryptoYahoo: "Crypto via Yahoo",
    dcAssetIndices: "Indices",
    dcAssetFx: "FX",
    dcAssetFutures: "Commodities / Futures",
    dcAssetCsvUpload: "CSV Upload",
    dcNoteCnAkShare:
      "Mainland A-shares route to AKShare with qfq-adjusted daily bars.",
    dcNoteCryptoCoinGecko: "CoinGecko planned for richer crypto market data.",
    dcNoteCsvUpload: "For custom research datasets and model lab experiments.",
    dcRoutingMode: "Routing mode",
    dcProviderInstalled: "Installed",
    dcProviderConfigured: "Configured",
    dcProviderLiveHealth: "Live health checked",
    dcSymbolExamples: "Supported symbol examples",
    dcSourceAkShare: "AKShare",
    dcAkShareTitle: "AKShare",
    dcAkShareDesc:
      "Active China-friendly free provider for A-shares and US equities. Primary source in auto failover.",
    dcStooqTitle: "Stooq",
    dcStooqDesc:
      "Free CSV provider for US/HK/EU equities. Used as last fallback if bot checks block access.",
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
    robustnessChecks: "Robustness",
    robustnessChecksDesc:
      "Parameter sensitivity, out-of-sample validation, and future walk-forward and model robustness checks.",
    robustnessPageDesc:
      "Test whether strategy behavior is sensitive to parameters or unstable out of sample.",
    robustnessEducationalNote:
      "Robustness checks help reduce overclaiming. A strategy that works only for one parameter set or only in-sample may not be reliable.",
    modelLab: "Model Lab",
    modelLabDesc:
      "ML dataset builder, feature engineering, logistic regression, gradient boosting models, and future deep learning signal research.",
    experiments: "Saved Runs",
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

    systemCurrentDataSource: "Current data source: auto (AKShare → Yahoo → Stooq)",
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
    yes: "Yes",
    no: "No",
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

    paperTrading: "Paper Trading",
    paperTradingDesc:
      "Evaluate today's strategy signal against a simulated account. Five-level risk rules gate simulated position changes. No live orders.",
    paperTradingNote: "Paper trading only. Signals use prior-day position semantics (no look-ahead).",
    paperEvaluate: "Evaluate Signal",
    paperExecute: "Execute Paper Trade",
    paperReset: "Reset Account",
    paperTodaySignal: "Today's Signal",
    paperAction: "Paper Action",
    paperAccount: "Paper Account",
    paperRisk: "Risk Monitor",
    paperRiskLevel: "Risk Level",
    paperAllowedAction: "Allowed Action",
    paperPortfolioValue: "Portfolio Value",
    paperUnrealizedPnl: "Unrealized P&L",
    paperRealizedPnl: "Realized P&L",
    paperCurrentDrawdown: "Current Drawdown",
    paperPosition: "Position",
    paperCooldown: "Cooldown Until",
    paperNotes: "Research Notes",
    paperNotesPlaceholder: "Optional notes for this paper session...",
    paperTradeJournal: "Trade Journal",
    paperFlat: "Flat",
    paperLong: "Long",
    paperConfidence: "Confidence",
    paperTargetPosition: "Target Position",
    paperCash: "Cash",
    paperShares: "Shares",
    paperEntryPrice: "Entry Price",
    paperCurrentPrice: "Current Price",
    paperRiskReasons: "Risk Reasons",
    paperComponentLevels: "Risk Components",
    paperExecuteResult: "Execution",
    paperNoTrade: "No paper trade executed.",
    paperResetConfirm: "Reset paper account to initial capital?",
    paperEvaluateFailed: "Paper trading evaluation failed.",
    paperExecuteFailed: "Paper trade execution failed.",
    paperResetFailed: "Failed to reset paper account.",
    modulePaperTradingOverviewDesc:
      "Simulated forward trading with a five-level risk engine and trade journal.",
    overviewPaperAccount: "Paper Account",
    overviewPaperAccountDesc: "Current simulated account snapshot from the latest evaluation.",
    overviewOpenPaperTrading: "Open Paper Trading",
    overviewPaperNotEvaluated: "No paper session yet. Open Paper Trading to evaluate a signal.",
  },
  zh: {
    appTitle: "AI 量化研究",
    appTitleShort: "量化研究",
    appSubtitle: "围绕研究、实验、证据与决策的研究工作区——仅供演示。",
    educationalDemo: "研究演示",
    dailyMarketData: "日线市场数据",
    notFinancialAdvice: "非投资建议",
    navOverview: "总览",
    navResearchWorkspace: "研究",
    navGroupCockpit: "决策驾驶舱",
    navStrategyHealthScore: "策略健康度",
    navReturnQualityLens: "收益质量",
    navRiskGateReview: "风控闸口",
    navScenarioShockTest: "情景冲击",
    navDecisionLedger: "决策台账",
    navDecisionRoom: "策略决策室",
    navGroupResearch: "研究",
    navGroupTools: "研究工具",
    navGroupArchive: "存档",
    navDataCenter: "数据",
    navMarketWatch: "行情",
    navStrategyLab: "回测",
    navComparison: "对比",
    navRobustness: "稳健性",
    navModelLab: "模型实验",
    navExperiments: "实验",
    navPaperTrading: "模拟试盘",
    navResearchNotes: "笔记",
    navAiAgent: "AI 助手",
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
    backendUnreachable: "研究后端当前不可用或正在启动，请稍后重试。",

    marketWatch: "行情",
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

    strategyLab: "回测",
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
    backtestReviewTitle: "回测复盘",
    backtestReviewDesc:
      "从治理视角总结模拟回测质量、风险档位与是否适合进入模拟试盘。",
    backtestReviewNote:
      "以下为规则复盘，基于模拟回测语境，不构成交易建议。",
    backtestReviewKeyFindings: "关键发现",
    backtestReviewRiskLevel: "回测风险等级",
    backtestReviewPaperEligibility: "模拟试盘准入",
    backtestReviewManagement: "管理层解读",
    backtestReviewEligible: "可进入模拟试盘",
    backtestReviewWatch: "观察后再模拟试盘",
    backtestReviewNotEligible: "暂不适合模拟试盘",
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

    saveBacktestRun: "保存实验",
    savingBacktestRun: "保存中...",
    experimentNotes: "备注",
    experimentNotesPlaceholder: "可选：为本次回测填写研究备注",
    saveBacktestSuccess: "回测已保存到实验中心。",
    saveBacktestFailed: "无法保存回测实验。",
    saveRequiresResult: "请先运行回测再保存。",
    openExperiments: "查看已保存实验",

    experimentsPageTitle: "实验存档",
    experimentsPageDesc: "查看已保存的回测记录，打开详情或横向对比结果。",
    experimentsListTitle: "记录列表",
    experimentsListDesc: "筛选、排序已保存记录。点击行看详情，勾选多行可对比。",
    experimentsLoading: "正在加载已保存实验...",
    experimentsEmpty: "暂无已保存实验。请先在策略实验室保存一次回测。",
    experimentsLoadFailed: "无法加载实验列表。",
    experimentsDetail: "记录详情",
    experimentsBackToList: "返回列表",
    experimentsCreatedAt: "保存时间",
    experimentsTradeCount: "交易笔数",
    experimentsSelectHint: "点击一行查看完整详情。",
    experimentsDelete: "删除",
    experimentsDeleted: "实验已删除。",
    experimentsDeleteFailed: "无法删除实验。",
    experimentsNotes: "备注",
    experimentsConfig: "策略配置",
    experimentsNoTrades: "本次运行没有保存交易记录。",

    experimentsCompareTitle: "结果对比",
    experimentsCompareDesc: "选择 2–4 条记录，对比关键指标。",
    experimentsCompareSelect: "对比",
    experimentsCompareClear: "清除选择",
    experimentsCompareNeedTwo: "请至少选择 2 条记录进行对比。",
    experimentsCompareMax: "一次最多对比 4 条记录。",
    experimentsCompareSummary: "对比摘要",
    experimentsCompareBestReturn: "最高总收益",
    experimentsCompareBestSharpe: "最高 Sharpe",
    experimentsCompareLowestDrawdown: "最低回撤",
    experimentsCompareRunLabel: "实验",

    experimentsFilterTicker: "标的筛选",
    experimentsFilterStrategy: "策略筛选",
    experimentsFilterAll: "全部",
    experimentsSortBy: "排序字段",
    experimentsSortDirection: "排序方向",
    experimentsSortCreatedAt: "创建时间",
    experimentsSortTotalReturn: "总收益",
    experimentsSortSharpe: "Sharpe 比率",
    experimentsSortDrawdown: "最大回撤",
    experimentsSortAsc: "升序",
    experimentsSortDesc: "降序",
    experimentsShowingCount: "显示 {shown} / {total} 条已保存记录",
    experimentsFilterEmpty: "当前筛选条件下没有匹配的记录。",
    experimentsFilterReset: "重置筛选",
    experimentsRunId: "运行 ID",
    experimentsDeleteConfirm: "确定删除这条已保存实验吗？此操作无法撤销。",
    experimentsSavedRedirect: "回测已保存，正在显示实验详情。",
    experimentsDetailEmpty: "选择一条已保存记录，查看指标、配置与交易日志。",

    researchListEyebrow: "研究",
    researchListTitle: "研究",
    researchListSubtitle:
      "每个研究对应一个研究问题。实验、证据与结论都归属在研究之内。",
    researchListNewResearch: "新建研究",
    researchListCreateResearch: "创建研究",
    researchListLoadDemo: "加载演示研究",
    researchListDemoLoaded: "已恢复演示研究到列表。",
    researchListCreated: "已在本地创建研究。",
    researchListCreateFailed: "无法创建研究，请重试。",
    researchListKpiResearch: "研究总数",
    researchListSummaryAria: "研究工作区摘要",
    researchListKpiDefined: "草稿 / 已定义",
    researchListKpiEvidenceAvailable: "运行中 / 已有证据",
    researchListKpiReviewArchived: "待复核 / 已归档",
    researchListEvidenceStatus: "证据状态",
    researchListQuestionLabel: "研究问题",
    researchListLatestEvidence: "最新证据",
    researchListModalName: "研究标题",
    researchListModalNameRequired: "研究标题为必填项。",
    researchListModalQuestion: "研究问题",
    researchListModalHypothesis: "假设",
    researchListModalHypothesisRequired: "假设为必填项。",
    researchListModalLocalNote:
      "在当前浏览器创建研究问题。实验稍后在研究内设计；指标由后端真实计算。",
    researchListModalQuestionRequired: "研究问题为必填项。",
    researchListModalSymbolRequired: "标的代码为必填项。",
    researchListModalShortInvalid: "短期均线窗口必须是正整数。",
    researchListModalLongInvalid: "长期均线窗口必须大于短期窗口。",
    researchListModalDateInvalid: "开始日期必须早于结束日期。",
    researchListModalCostInvalid: "交易成本不能为负数。",
    researchListModalTagsHint: "可选 — 逗号分隔的标签",
    researchListModalCreate: "创建",
    researchListModalCancel: "取消",
    researchListTemplateMa: "均线交叉",
    researchListTemplateMomentum: "动量",
    researchListTemplateMeanReversion: "均值回归",
    researchListTemplateCustom: "自定义",
    researchListSearch: "搜索",
    researchListSearchPlaceholder: "按标题或研究问题搜索…",
    researchListFilterStatus: "状态",
    researchListFilterOwner: "负责人",
    researchListFilterTag: "标签",
    researchListFilterAll: "全部",
    researchListSort: "排序",
    researchListSortUpdated: "最近更新",
    researchListSortCreated: "最近创建",
    researchListSortName: "名称 (A–Z)",
    researchListSortConfidence: "置信度（高优先）",
    researchListLoading: "正在加载研究…",
    researchListErrorTitle: "研究列表暂不可用",
    researchListRetry: "重试",
    researchListResultCount: "项研究",
    researchListEmptyFilterTitle: "没有符合筛选条件的研究",
    researchListEmptyFilterDescription: "请放宽筛选条件或清空搜索词。",
    researchListClearFilters: "清空筛选",
    researchListEmptyTitle: "尚无研究",
    researchListEmptyDescription:
      "从一个研究问题开始，或加载趋势跟踪演示以探索工作区。",
    researchListOpenWorkspace: "进入工作区",
    researchListDuplicate: "复制",
    researchListArchive: "归档",
    researchListMore: "更多",
    researchListMoreTodo: "更多操作即将提供",
    researchListDuplicated: "已在本地复制项目（模拟）。",
    researchListArchived: "已在本地归档研究。",
    researchListExperimentCount: "实验",
    researchListLastValidation: "最近验证",
    researchListRecommendation: "当前建议",
    researchListUpdated: "更新于",
    researchListOwner: "负责人",
    researchListConfidence: "置信度",
    researchListEvaluationArea: "评估",
    researchListSymbol: "标的",
    researchListBenchmark: "基准",
    researchListStrategy: "策略",
    researchListDataStatus: "数据状态",
    researchListMetricsStatus: "指标状态",
    researchListValidationStatus: "验证状态",
    researchListEvaluationStatus: "评估状态",

    researchWsBackToList: "返回研究列表",
    researchWsMoreActions: "更多操作",
    researchWsMoreActionsHint:
      "重命名、共享与破坏性操作延后实现。当前模拟不会修改状态。",
    researchWsCreated: "创建于",
    researchWsTags: "标签",
    researchWsLoading: "正在加载研究工作区…",
    researchWsErrorTitle: "研究工作区暂不可用",
    researchWsRetry: "重试",
    researchWsNotFoundTitle: "未找到该研究",
    researchWsNotFoundDescription:
      "没有与此 ID 匹配的研究。请返回研究列表选择有效项目。",
    researchWsNavOverview: "总览",
    researchWsNavNotebook: "笔记",
    researchWsNavExperiments: "实验",
    researchWsNavValidation: "证据",
    researchWsNavEvaluation: "审阅",
    researchWsNavCopilot: "Copilot",
    researchWsNavTimeline: "时间线",
    researchWsNavFiles: "文件",
    researchWsNavSettings: "设置",
    researchWsNavTools: "辅助工具",
    researchWsProgressTitle: "研究进度",
    researchWsProgressResearch: "研究",
    researchWsProgressExperiments: "实验",
    researchWsProgressEvidence: "证据",
    researchWsProgressDecision: "决策",
    researchWsQuickActionsTitle: "快捷操作",
    researchWsQuickRunExperiment: "运行实验",
    researchWsQuickOpenValidation: "打开验证",
    researchWsQuickGenerateReview: "生成审阅",
    researchWsRecentExperiments: "最近实验",
    researchWsLatestEvidence: "最新证据",
    researchWsCurrentDecision: "当前决策",
    researchWsNoExperiments: "尚无实验——先定义第一个协议。",
    researchWsNoEvidence: "尚无证据包。",
    researchWsDecisionPending: "决策有待证据与审阅。",
    researchWsKeyResultsUnavailable: "运行研究以计算历史证据。",
    researchWsOosSharpeUnavailable: "运行验证以计算样本外夏普比率。",
    researchWsGuidedWorkflowTitle: "进度",
    researchWsStepRunResearch: "运行研究",
    researchWsStepValidateEvidence: "压力测试",
    researchWsStepReviewEvaluation: "证据体检",
    researchWsStepAskCopilot: "向 Copilot 提问",
    researchWsGuidedLoading: "进行中…",
    researchWsGuidedFailed: "需要关注",
    researchWsGuidedUnavailableAfterExecution: "请先完成历史执行。",
    researchWsGuidedUnavailableAfterValidation: "请先运行验证，再请求评估。",
    researchWsGuidedUnavailableAfterEvaluation: "请先请求评估，再使用 Copilot。",
    researchWsNextStepTitle: "下一步",
    researchWsNextStepRunResearchTitle: "运行研究",
    researchWsNextStepRunResearchDescription: "按已配置协议计算历史证据。",
    researchWsNextStepRunResearchCta: "运行研究",
    researchWsNextStepRunResearchLoadingCta: "正在运行研究…",
    researchWsNextStepRunResearchRetryCta: "重试研究",
    researchWsNextStepValidateTitle: "验证证据",
    researchWsNextStepValidateDescription:
      "运行确定性 OOS、参数、成本与数据质量检查。",
    researchWsNextStepValidateCta: "运行验证",
    researchWsNextStepEvaluateTitle: "审阅评估",
    researchWsNextStepEvaluateDescription: "汇总证据覆盖与未完成要求。",
    researchWsNextStepEvaluateCta: "请求评估",
    researchWsNextStepCopilotTitle: "向 Copilot 提问",
    researchWsNextStepCopilotDescription: "基于现有证据提问。",
    researchWsNextStepCopilotCta: "打开 Copilot",
    researchWsConclusionNotRequested: "尚未请求评估。",
    researchWsConclusionIncomplete: "当前证据尚不足以形成最终研究决策。",
    researchWsConclusionBlocked: "评估因必需证据不足而被阻塞。",
    researchWsEvidencePreview: "证据预览",
    researchListNextStep: "下一步",
    researchListNextStepRunResearch: "运行研究",
    researchListNextStepValidate: "验证证据",
    researchListNextStepEvaluate: "请求评估",
    researchListNextStepReview: "审阅评估",
    researchWsQuestion: "研究问题",
    researchWsHypothesis: "假设",
    researchWsObjective: "研究目标",
    researchWsCurrentStage: "当前阶段",
    researchWsConfidence: "研究置信度",
    researchWsSummary: "研究摘要",
    researchWsEvidenceNarrative: "证据摘要",
    researchWsValidationSummary: "验证摘要",
    researchWsKeyStrengths: "主要优势",
    researchWsKnownWeaknesses: "已知弱点",
    researchWsOpenQuestions: "未决问题",
    researchWsNextActions: "下一步行动",
    researchWsLifecycleTitle: "研究生命周期",
    researchWsLifecycleDescription:
      "对齐 Architecture Bible 第 3 章的权威进度阶段。已完成、当前与后续阶段均有明确标注。",
    researchWsEvidenceTitle: "证据清单",
    researchWsEvidenceDescription:
      "仅展示确定性证据包。状态与简洁结果——不是交易信号。",
    researchWsEvidencePreviewTitle: "关联证据（预览）",
    researchWsEvidencePreviewDescription:
      "本分区仍为占位时，展示总览中的部分证据以保持上下文。",
    researchWsActionsTitle: "工作区操作",
    researchWsActionsDescription:
      "使用现有研究工作流，在各证据阶段之间操作和切换。",
    researchWsActionNotebook: "添加笔记条目",
    researchWsActionExperiment: "创建实验",
    researchWsActionValidation: "运行验证",
    researchWsActionValidationRunning: "正在运行验证…",
    researchWsActionEvaluation: "请求评估",
    researchWsActionCopilot: "打开 Research Copilot",
    researchWsActionExport: "导出研究",
    researchWsActionHintNotebook: "打开研究笔记。",
    researchWsActionHintExperiment: "打开计划中的实验。",
    researchWsActionHintValidation: "基于当前执行证据运行确定性验证。",
    researchWsActionHintEvaluation: "查看由验证证据推导的治理结论。",
    researchWsActionHintEvaluationDisabled: "请先运行验证。",
    researchWsActionHintCopilot: "基于当前研究证据提问。",
    researchWsActionHintCopilotDisabled: "请先运行验证。",
    researchWsActionHintExport: "当前版本暂不支持导出。",
    researchWsComingLater: "后续 PR 提供",
    researchWsDeferredNote: "延后至后续 PR。当前仅为研究定义，不可执行工作流。",
    researchWsExecutionPendingNote:
      "市场衍生证据将由 Research Execution Engine 填充。不展示虚构的通过/失败或分数。",
    researchWsStrategyConfig: "策略配置",
    researchWsDataRequirements: "数据要求",
    researchWsNotebookTitle: "笔记",
    researchWsNotebookSummary:
      "笔记将保存带日期的研究记录、假设变更，并明确区分解释与量化事实。",
    researchWsNotebookCap1: "追加式条目，含作者与时间戳",
    researchWsNotebookCap2: "笔记关联 Evidence / Experiment ID",
    researchWsNotebookCap3: "区分事实、计算与模型解释",
    researchWsExperimentsTitle: "实验",
    researchWsExperimentsSummary:
      "实验列表将展示与研究计划绑定的设计、批准、运行与终态实验。",
    researchWsExperimentsCap1: "带协议版本的实验登记",
    researchWsExperimentsCap2: "启停由 Application 层负责，而非 UI 执行",
    researchWsExperimentsCap3: "终态结果进入证据候选",
    researchWsValidationTitle: "验证",
    researchWsValidationSectionSummary:
      "SPY MA 交叉的验证阶段。真实历史序列计算完成前保持「未开始」或「等待数据」。",
    researchWsValidationCap1: "来自实价的历史回测与基准对比",
    researchWsValidationCap2: "按时间切分的 OOS 与有界敏感性（禁止打乱时序）",
    researchWsValidationCap3: "交易成本与数据质量审查通过后再进入评估",
    researchWsValidationNotStarted: "未开始",
    researchWsValidationAwaitingData: "等待数据",
    researchWsValidationCompleted: "已完成",
    researchValSummary:
      "来自后端的验证证据。状态和指标按返回值展示，浏览器不会重新计算。",
    researchValLoading: "正在从后端加载验证证据…",
    researchValUnavailableTitle: "验证证据不可用",
    researchValUnavailableDescription:
      "后端未返回验证证据，不展示模拟结果。",
    researchValRetry: "重试验证",
    researchValStatus: "状态",
    researchValEvidenceComplete: "证据完整",
    researchValYes: "是",
    researchValNo: "否",
    researchValIncomplete: "不完整",
    researchValFailed: "失败",
    researchValUnavailable: "不可用",
    researchValSource: "来源",
    researchValGenerated: "生成时间",
    researchValRules: "规则",
    researchValWarnings: "需关注",
    researchValDataNotes: "数据说明",
    researchValBlockers: "阻塞项",
    researchValEvidence: "证据",
    researchValOosTitle: "样本外验证",
    researchValSplitDate: "精确切分日期",
    researchValInSampleRatio: "样本内比例",
    researchValMinimumOos: "最少样本外观测数",
    researchValBoundary: "边界约定",
    researchValInSample: "样本内",
    researchValOutOfSample: "样本外",
    researchValBenchmark: "样本外基准",
    researchValObservations: "观测数",
    researchValMetric: "指标",
    researchValTotalReturn: "总收益",
    researchValCagr: "复合年增长率",
    researchValSharpe: "夏普比率",
    researchValMaxDrawdown: "最大回撤",
    researchValVolatility: "年化波动率",
    researchValTrades: "交易次数",
    researchValTotalCosts: "总交易成本",
    researchValParameterTitle: "参数敏感性",
    researchValValidCombinations: "有效组合",
    researchValProfitableCombinations: "盈利组合",
    researchValPositiveSharpe: "正夏普组合",
    researchValMedianSharpe: "夏普中位数",
    researchValSharpeRange: "夏普区间",
    researchValMedianDrawdown: "最大回撤中位数",
    researchValCanonicalPercentile: "规范参数夏普百分位",
    researchValShortWindow: "短窗口",
    researchValLongWindow: "长窗口",
    researchValCanonical: "规范参数",
    researchValCostTitle: "交易成本敏感性",
    researchValTransactionCost: "交易成本",
    researchValReturnDegradation: "相对零成本收益衰减",
    researchValSharpeDegradation: "相对零成本夏普衰减",
    researchValMathematicallyValid: "数学有效",
    researchValCanonicalCost: "规范交易成本",
    researchValDataQualityTitle: "数据质量",
    researchValProvider: "数据源",
    researchValDateRange: "实际日期区间",
    researchValCache: "缓存",
    researchValCacheHit: "命中缓存",
    researchValCacheMiss: "未命中缓存",
    researchValFatalIssues: "致命问题",
    researchValChecks: "数据质量检查",
    researchValCheck: "检查项",
    researchValSeverity: "严重性",
    researchValDetails: "详情",
    researchValNotAvailable: "n/a",
    researchWsCalculatedMetrics: "结果",
    researchWsMetricTotalReturn: "总收益",
    researchWsMetricBenchReturn: "基准总收益",
    researchExecRealData: "真实历史数据",
    researchExecCached: "缓存",
    researchExecStale: "过期缓存",
    researchExecProvider: "数据源",
    researchExecAssetClass: "资产类别",
    researchExecAdjustment: "复权方式",
    researchExecSymbol: "标的",
    researchExecRange: "实际日期区间",
    researchExecRetrieved: "获取时间",
    researchExecDisclaimer:
      "历史研究结果——不构成投资建议，亦不构成对未来表现的预测。",
    researchExecLoading: "正在从后端加载研究执行结果…",
    researchExecUnavailableTitle: "研究执行不可用",
    researchExecUnavailableDescription:
      "后端未返回计算证据。不展示虚构指标。",
    researchExecRetry: "重试执行",
    researchWsEvaluationTitle: "评估",
    researchEvalSummary:
      "评估仅汇总 PR-009 已计算的验证证据，不执行新计算、不打分、不给出投资建议。",
    researchEvalStatus: "评估状态",
    researchEvalCompleted: "已完成",
    researchEvalIncomplete: "不完整",
    researchEvalBlocked: "受阻",
    researchEvalSource: "数据源",
    researchEvalGenerated: "生成时间",
    researchEvalCoverageTitle: "证据覆盖度",
    researchEvalImplementedStages: "已实现阶段数",
    researchEvalCompletedStagesCount: "已完成阶段数",
    researchEvalCoveragePercentage: "覆盖率",
    researchEvalCoverageDisclaimer:
      "覆盖率仅衡量实现完整度，不是置信度、质量或稳健性评分。",
    researchEvalEvidenceSummaryTitle: "证据摘要",
    researchEvalStageColumn: "阶段",
    researchEvalStatusColumn: "状态",
    researchEvalSummaryColumn: "摘要",
    researchEvalCompletedEvidenceTitle: "已完成证据",
    researchEvalIncompleteEvidenceTitle: "不完整证据",
    researchEvalOutstandingEvidenceTitle: "还缺什么",
    researchEvalLimitationsTitle: "局限说明",
    researchEvalBlockersTitle: "阻塞项",
    researchEvalDecisionReadiness: "能下结论了吗",
    researchEvalKeyFindings: "主要发现",
    researchEvalNextGovernanceAction: "下一步做什么",
    researchEvalDetailsTitle: "评估详情",
    researchEvalNone: "无",
    researchEvalNotAvailable: "n/a",
    researchEvalLoading: "正在从后端加载评估证据…",
    researchEvalUnavailableTitle: "评估不可用",
    researchEvalUnavailableDescription: "后端未返回评估摘要。不展示虚构证据。",
    researchEvalRetry: "重试评估",
    researchEvalAwaitingValidationTitle: "需要验证证据",
    researchEvalAwaitingValidationDescription:
      "请先运行或加载验证证据，之后才能生成评估。",
    researchEvalGoToValidation: "前往验证",
    researchCopilotTitle: "证据驱动的研究 Copilot",
    researchCopilotSubtitle:
      "解释现有工作区证据。不计算指标、不重跑回测、不推荐交易。",
    researchCopilotDisclaimer:
      "回答仅为解释层。执行、验证与评估结果仍为权威来源。",
    researchCopilotSampleQuestionsTitle: "示例问题",
    researchCopilotSample1: "当前评估为何不完整？",
    researchCopilotSample2: "样本外（OOS）证据说明了什么？",
    researchCopilotSample3: "该策略对交易成本有多敏感？",
    researchCopilotSample4: "还缺少哪些研究证据？",
    researchCopilotSample5: "系统如何防止前视偏差？",
    researchCopilotQuestionPlaceholder: "询问证据、验证或治理相关问题",
    researchCopilotAskButton: "向 Copilot 提问",
    researchCopilotAskingButton: "正在生成有据回答…",
    researchCopilotAnswerTitle: "回答",
    researchCopilotCitationsTitle: "证据引用",
    researchCopilotWarningsTitle: "警告",
    researchCopilotGroundingTitle: "依据状态",
    researchCopilotGeneratedAt: "生成时间",
    researchCopilotGrounded: "有据",
    researchCopilotPartiallyGrounded: "部分有据",
    researchCopilotUnavailable: "不可用",
    researchCopilotAwaitingValidationTitle: "需要验证证据",
    researchCopilotAwaitingValidationDescription:
      "请先运行或加载验证证据，再提出与证据相关的问题。",
    researchCopilotGoToValidation: "前往验证",
    researchCopilotNotConfigured: "本部署未配置 Research Copilot。",
    researchCopilotLimitations:
      "Copilot 不能批准策略、预测收益，也不能替代确定性验证。",
    researchCopilotUnavailableTitle: "Research Copilot 不可用",
    researchCopilotUnavailableDescription:
      "该工作区分区仅适用于规范 MA 交叉研究。",
    researchWsTimelineTitle: "时间线",
    researchWsTimelineSummary: "时间线将展示本研究聚合的不可变领域事件。",
    researchWsTimelineCap1: "带操作者与原因的状态迁移",
    researchWsTimelineCap2: "实验与验证里程碑",
    researchWsTimelineCap3: "适用时的重开与重设计事件",
    researchWsFilesTitle: "文件",
    researchWsFilesSummary:
      "文件区将引用版本化产物（配置、报告、笔记），而不是通用网盘。",
    researchWsFilesCap1: "产物元数据与校验和",
    researchWsFilesCap2: "关联到证据包",
    researchWsFilesCap3: "本 PR 不含任意上传",
    researchWsSettingsTitle: "设置",
    researchWsSettingsSummary:
      "设置覆盖所有权、可见性与研究元数据——不是交易账户配置。",
    researchWsSettingsCap1: "负责人与协作者角色",
    researchWsSettingsCap2: "标签与命名约定",
    researchWsSettingsCap3: "归档 / 重开策略（治理约束）",

    researchNbTitle: "研究笔记",
    researchNbDesignNotesTitle: "研究设计笔记",
    researchNbEntryCount: "条记录",
    researchNbLastUpdated: "最近更新",
    researchNbNewEntry: "新建条目",
    researchNbLoading: "正在加载笔记条目…",
    researchNbErrorTitle: "笔记暂不可用",
    researchNbRetry: "重试",
    researchNbEmptyTitle: "尚无研究笔记",
    researchNbEmptyDescription: "记录第一条观察、假设或决策。",
    researchNbFilterEmptyTitle: "没有符合筛选的条目",
    researchNbFilterEmptyDescription: "请更换条目类型或显示全部。",
    researchNbFilterType: "条目类型",
    researchNbFilterAll: "全部",
    researchNbSort: "排序",
    researchNbSortNewest: "最新优先",
    researchNbSortOldest: "最早优先",
    researchNbCardAuthor: "作者",
    researchNbCardCreated: "创建于",
    researchNbCardEdited: "已编辑",
    researchNbCardRelated: "关联产物",
    researchNbComposerTitle: "新建笔记条目",
    researchNbComposerType: "条目类型",
    researchNbComposerEntryTitle: "标题",
    researchNbComposerContent: "正文",
    researchNbComposerTags: "标签",
    researchNbComposerTagsHint: "逗号分隔（可选）",
    researchNbComposerArtifact: "关联产物（可选）",
    researchNbComposerArtifactNone: "无",
    researchNbComposerSave: "保存条目",
    researchNbComposerCancel: "取消",
    researchNbValidationType: "请选择条目类型。",
    researchNbValidationTitle: "请填写标题。",
    researchNbValidationBody: "请填写正文。",
    researchTlTitle: "时间线",
    researchTlDescription:
      "本研究聚合的活动记录。会话内保存的笔记会追加本地事件。",
    researchTlSessionNote: "TODO(api)：替换为 Research 上下文的领域事件流。",
    researchTlEmpty: "该研究项目尚无时间线事件。",

    researchExpTitle: "实验",
    researchExpTotalCount: "个实验",
    researchExpActiveCount: "个进行中",
    researchExpNew: "新建实验",
    researchExpLoading: "正在加载实验…",
    researchExpErrorTitle: "实验列表暂不可用",
    researchExpRetry: "重试",
    researchExpEmptyTitle: "尚无实验",
    researchExpEmptyDescription: "设计第一个受控假设检验实验。",
    researchExpFilterEmptyTitle: "没有符合筛选条件的实验",
    researchExpFilterEmptyDescription: "请清空筛选或放宽搜索。",
    researchExpNotFoundTitle: "未找到该实验",
    researchExpNotFoundDescription: "当前研究的模拟目录中没有匹配此 ID 的实验。",
    researchExpBackToList: "返回实验列表",
    researchExpSearch: "搜索",
    researchExpSearchPlaceholder: "名称、假设、数据集、参数…",
    researchExpFilterStatus: "状态",
    researchExpFilterType: "类型",
    researchExpSort: "排序",
    researchExpFilterAll: "全部",
    researchExpSortUpdated: "最近更新",
    researchExpSortCreated: "最近创建",
    researchExpSortResult: "结果（Sharpe）",
    researchExpCardHypothesis: "假设",
    researchExpCardDataset: "数据集 / 标的",
    researchExpCardWindow: "样本区间",
    researchExpCardBenchmark: "基准",
    researchExpCardResult: "结果摘要",
    researchExpCardReadiness: "验证就绪度",
    researchExpCardParameters: "关键参数",
    researchExpCardLinkedNotes: "关联笔记",
    researchExpOpenDetail: "查看详情",
    researchExpComposerTitle: "新建实验（Designed）",
    researchExpComposerName: "实验名称",
    researchExpComposerHypothesis: "假设",
    researchExpComposerType: "实验类型",
    researchExpComposerDataset: "数据集或标的",
    researchExpComposerStart: "开始日期",
    researchExpComposerEnd: "结束日期",
    researchExpComposerBenchmark: "基准",
    researchExpComposerParameters: "参数",
    researchExpComposerParametersHint: "每行一个 key=value（可选）",
    researchExpComposerSuccess: "成功标准",
    researchExpComposerFalsify: "证伪条件",
    researchExpComposerNotes: "备注",
    researchExpComposerSave: "保存为 Designed",
    researchExpComposerCancel: "取消",
    researchExpValidationName: "请填写实验名称。",
    researchExpValidationHypothesis: "请填写假设。",
    researchExpValidationType: "请选择实验类型。",
    researchExpValidationDataset: "请填写数据集或标的。",
    researchExpValidationStart: "请填写开始日期。",
    researchExpValidationEnd: "请填写结束日期。",
    researchExpValidationDateRange: "日期区间无效。",
    researchExpValidationSuccess: "请填写成功标准。",
    researchExpValidationFalsify: "请填写证伪条件。",
    researchExpDetailTitle: "实验详情",
    researchExpDetailClose: "关闭详情",
    researchExpDetailOverview: "总览",
    researchExpDetailConfig: "配置",
    researchExpDetailEvidence: "关联证据",
    researchExpDetailNotebook: "关联笔记条目",
    researchExpNone: "无",
    researchExpLifecycleTitle: "实验生命周期",
    researchExpLifecycleDescription:
      "Designed → Approved → Running → Completed（Architecture Bible 第 3 章）。Failed / Invalidated 为终态旁路。",
    researchExpLifecycleCompleted: "已完成",
    researchExpLifecycleCurrent: "当前",
    researchExpLifecycleUpcoming: "后续",
    researchExpLifecycleTerminal: "终态",
    researchExpLifecycleGoverned:
      "批准 / 启动 / 完成动作延后实现。UI 不得静默违反冻结状态机。",
    researchExpMetricsTitle: "主要指标",
    researchExpMetricsDisclaimer:
      "指标仅在 Research Execution Engine 完成计算后显示。历史研究——不构成投资建议。",
    researchExpMetricSharpe: "夏普",
    researchExpMetricCagr: "年化收益",
    researchExpMetricMaxDD: "最大回撤",
    researchExpMetricVol: "波动率",
    researchExpMetricTrades: "交易次数",
    researchExpMetricWinRate: "胜率",
    researchExpMetricCost: "总交易成本",

    overviewTitle: "工作台总览",
    overviewDesc:
      "按功能分组展示研究工作台各模块，并如实标注每个模块的可用状态——已上线、开发中或尚未开始。",
    executiveCockpit: "管理层驾驶舱",
    executiveCockpitDesc:
      "汇总模拟组合态势、风控闸口与决策可追溯信息，供管理层审阅与治理。",
    executiveCockpitTileDesc:
      "六宫格入口：策略健康度、收益质量、风控闸口、情景冲击与决策留痕。",
    cockpitGridTitle: "决策驾驶舱模块",
    cockpitGridDesc:
      "各模块支撑模拟审阅流程，不构成投资建议，也不执行真实交易。",
    cockpitDisclaimer: "仅供模拟决策支持，非投资建议，不用于实盘交易。",
    cockpitNav: "模拟净值",
    cockpitYtdReturn: "年初至今收益（模拟）",
    cockpitMaxDrawdown: "最大回撤",
    cockpitSharpe: "夏普比率",
    cockpitRiskLevel: "风险等级",
    categoryDecisionCockpit: "决策驾驶舱",
    strategyHealthScore: "策略健康度评分",
    strategyHealthScoreDesc:
      "基于回撤、夏普漂移、成本拖累与风控信号的模拟健康度综合评分。",
    returnQualityLens: "收益质量透视",
    returnQualityLensDesc:
      "模拟收益归因与质量透视，供管理层审阅，不代表收益承诺。",
    returnQualityLensModuleNote:
      "收益质量透视用于判断模拟收益是否来自可接受的回撤、成本效率和风险调整后表现，而不是只看收益率本身。",
    returnQualityLensSimulatedNote:
      "以下为模拟收益与风险调整指标，仅供治理审阅，不构成投资建议。",
    returnQualityExcessReturn: "超额收益",
    returnQualityMaxDrawdown: "最大回撤",
    returnQualityCostDrag: "成本拖累",
    returnQualityHitRate: "胜率",
    returnQualityProfitFactor: "盈亏比",
    returnQualityCapitalAtRisk: "风险敞口",
    returnQualityDrawdownBuffer: "距红色档位回撤缓冲",
    riskGateReview: "风控闸口审查",
    riskGateReviewDesc:
      "五档风险治理面板：信号输入、闸口校验与允许的模拟动作。",
    riskGateReviewModuleNote:
      "策略信号不会直接进入模拟动作，必须先经过风控闸口，根据回撤、波动率、连续亏损和信号冲突决定是否允许继续试盘、限制加仓或进入观察。",
    riskGateSimulatedNote:
      "以下为模拟试盘治理流程示意，不涉及真实下单或实盘执行。",
    riskGateStepStrategySignal: "策略信号",
    riskGateStepGateReview: "风控闸口审查",
    riskGateStepFinalAction: "最终模拟动作",
    riskGateRawSignal: "原始信号",
    riskGateRiskLevel: "风险等级",
    riskGateDecision: "闸口结论",
    riskGateReasons: "审查原因",
    scenarioShockTest: "情景冲击测试",
    scenarioShockTestDesc:
      "本模块用于模拟预设市场冲击下，策略净值、回撤和风控等级可能如何变化。它不是市场预测，而是风险预案工具。",
    scenarioShockTestNote:
      "以下为模拟冲击情景，仅供风险预案审阅，不构成投资建议，也不代表市场预测。",
    scenarioShockNavImpact: "净值影响",
    scenarioShockRiskAfter: "冲击后风控等级",
    scenarioShockTriggeredRules: "触发规则",
    scenarioShockSystemAction: "系统动作",
    scenarioShockInterpretation: "管理层解读",
    decisionLedger: "决策留痕台账",
    decisionLedgerDesc:
      "记录每一次策略信号、风控闸口判断、模拟动作、人工备注和后续结果，形成可追溯、可复盘的决策台账。",
    decisionLedgerNote:
      "治理审计留痕，强调人工复核与问责追溯。不是交易流水账——每一行都记录审阅判断与后续跟进。",
    ledgerDate: "日期",
    ledgerSymbol: "标的",
    ledgerStrategy: "策略",
    ledgerRawSignal: "原始信号",
    ledgerRiskLevel: "风险等级",
    ledgerGateDecision: "闸口结论",
    ledgerFinalPaperAction: "最终模拟动作",
    ledgerExplanation: "系统说明",
    ledgerHumanNote: "人工备注",
    ledgerOutcome: "后续结果",
    decisionRoom: "策略决策室",
    decisionRoomDesc:
      "本模块用于解释策略信号如何经过风控闸口审查，并转化为最终模拟动作。它不提供投资建议，也不执行真实交易。",
    decisionRoomNote:
      "以下为治理演示用的模拟 AI 解释，非真实 LLM 调用，不涉及实盘交易。",
    decisionRoomSignalSnapshot: "信号快照",
    decisionRoomRolesTitle: "策略决策室 — 三视角解读",
    decisionRoomRetrievedContext: "检索到的风控上下文",
    decisionRoomRagNote:
      "模拟自 risk_knowledge 文档的 RAG 片段。本演示页未接入实时检索。",
    decisionRoomReviewQuestions: "复盘问题",
    moduleDecisionRoomOverviewDesc:
      "以三角色视角解释「信号 → 闸口 → 模拟动作」，并展示模拟政策检索上下文。",
    moduleStrategyHealthScoreOverviewDesc:
      "策略治理检查点的模拟健康度加权评分。",
    moduleReturnQualityLensOverviewDesc:
      "面向管理层审阅的模拟收益质量与归因透视。",
    moduleRiskGateReviewOverviewDesc:
      "风控闸口流程：信号 → 闸口校验 → 允许的模拟动作。",
    moduleScenarioShockTestOverviewDesc:
      "预设冲击情景库，模拟净值、回撤与风控等级的预案审阅。",
    moduleDecisionLedgerOverviewDesc:
      "信号、闸口结论、人工备注与审阅结果的可追溯审计台账。",
    strategyHealthScorePlaceholderSummary:
      "策略健康度评分计划仅基于真实的验证与评估证据构建综合评分。目前尚无可用的评分方法，因此不展示任何分数。",
    strategyHealthScorePlaceholderCap1: "综合评分将来自真实的夏普比率、回撤与成本拖累证据",
    strategyHealthScorePlaceholderCap2: "评分需以已完成的验证与评估结果为依据，而非模拟维度",
    strategyHealthScorePlaceholderCap3: "仅在评分方法被定义并评审通过后才会上线",
    returnQualityLensPlaceholderSummary:
      "收益质量透视计划在研究执行与验证引擎产出真实证据后，展示真实的收益归因、成本拖累与胜率。当前不展示任何模拟数字。",
    returnQualityLensPlaceholderCap1: "收益、基准与超额收益均来自真实执行证据",
    returnQualityLensPlaceholderCap2: "成本拖累与胜率来自真实的验证阶段结果",
    returnQualityLensPlaceholderCap3: "策略完成执行与验证后即可查看",
    riskGateReviewPlaceholderSummary:
      "风控闸口审查计划将确定性治理规则应用于真实策略证据。在相关规则与证据具备之前，不展示任何模拟信号、闸口结论或模拟动作。",
    riskGateReviewPlaceholderCap1: "确定性风控规则将应用于真实的评估证据",
    riskGateReviewPlaceholderCap2: "信号、闸口结论与动作均可追溯至来源，绝不模拟",
    riskGateReviewPlaceholderCap3: "上线前需经过明确的护栏规则评审",
    scenarioShockTestPlaceholderSummary:
      "情景冲击测试计划对真实策略历史运行压力与regime情景。在该能力具备之前，不展示任何模拟净值、回撤或风控等级结果。",
    scenarioShockTestPlaceholderCap1: "压力测试与regime分析将基于真实的已验证证据",
    scenarioShockTestPlaceholderCap2: "净值、回撤与风控等级影响将被计算，绝不模拟",
    scenarioShockTestPlaceholderCap3: "作为稳健性能力路线图的一部分交付",
    decisionLedgerPlaceholderSummary:
      "决策留痕台账计划在风控闸口审查与策略决策室具备真实证据后，记录带人工问责的真实治理决策。当前不展示任何模拟条目。",
    decisionLedgerPlaceholderCap1: "台账条目将基于真实的信号、闸口结论与结果证据",
    decisionLedgerPlaceholderCap2: "人工复核备注将关联可审计的决策记录",
    decisionLedgerPlaceholderCap3: "真实策略产生治理决策后即会填充",
    decisionRoomPlaceholderSummary:
      "策略决策室计划解释真实信号如何经过风控治理转化为模拟盘动作，AI 解读将明确标注并可追溯至证据。当前不展示任何模拟角色或检索片段。",
    decisionRoomPlaceholderCap1: "对真实信号、闸口与动作证据的 AI 解读，并会明确标注",
    decisionRoomPlaceholderCap2: "检索到的上下文将可追溯至真实政策与证据来源",
    decisionRoomPlaceholderCap3: "治理化的 AI 审阅能力落地后即可使用",
    publicPreviewDeferredNote:
      "在真实研究证据具备之前暂缓上线。本预览页面中的虚构演示数据已被移除。",
    overviewStatusLegend:
      "模块标签说明：可使用 = 现在就能用 · 开发中 = 仅占位，功能未完成 · 未开始 = 还在路线图里。",
    categoryCoreResearch: "核心研究",
    categoryDataStorage: "数据与存储",
    categoryModelAi: "模型与 AI",
    categorySystemNotes: "系统说明",
    statusActive: "可使用",
    statusBasicSupport: "部分可用",
    statusPlanned: "开发中",
    statusComingLater: "未开始",
    comingSoonTitle: "即将上线",
    openModule: "进入",
    openLegacyDemo: "打开完整演示",
    legacyDemoHint: "本模块迁移完成前，完整功能请暂时使用旧版演示页。",
    modulePlannedStatus: "功能尚未完成，当前页面只是占位。",
    moduleMigratingStatus: "本模块已可使用。",

    dataCenter: "数据",
    dataCenterPageDesc:
      "管理数据源覆盖范围、代码格式、资产类别和未来数据提供方集成。",
    dataCenterDesc:
      "记录当前 Yahoo/yfinance 覆盖范围、资产类别、代码格式与多数据源规划路线图。",
    dcCurrentActiveProvider: "当前启用数据源",
    dcLiveProviderStatus: "已配置数据源状态",
    dcActiveProvider: "当前启用数据源",
    dcPreferredSource: "首选数据源",
    dcPreferredSourceDesc:
      "默认 auto（AKShare → Yahoo → Stooq）。锁定某一源则强制使用；锁定失败不会回退。",
    dcPreferredSourceOptionAuto: "auto（自动回退）",
    dcPreferredSourceOptionAkshare: "akshare",
    dcPreferredSourceOptionYahoo: "yahoo",
    dcPreferredSourceOptionStooq: "stooq",
    dcProbeSource: "探测 AAPL",
    dcProbeLoading: "探测中...",
    dcProbeSuccess: "实际命中",
    dcProbeError: "探测失败",
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
    dcSourcePlanned: "尚未接入",
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
    dcAssetCnAkShare: "中国大陆 A 股",
    dcAssetCryptoYahoo: "通过 Yahoo 的加密货币",
    dcAssetIndices: "指数",
    dcAssetFx: "外汇",
    dcAssetFutures: "商品 / 期货",
    dcAssetCsvUpload: "CSV 上传",
    dcNoteCnAkShare: "A 股通过 AKShare 路由，默认使用前复权（qfq）日线。",
    dcNoteCryptoCoinGecko: "计划使用 CoinGecko 提供更丰富的加密市场数据。",
    dcNoteCsvUpload: "用于自定义研究数据集与模型实验室实验。",
    dcRoutingMode: "路由模式",
    dcProviderInstalled: "已安装",
    dcProviderConfigured: "已配置",
    dcProviderLiveHealth: "已做实时健康检查",
    dcSymbolExamples: "支持的标的示例",
    dcSourceAkShare: "AKShare",
    dcAkShareTitle: "AKShare",
    dcAkShareDesc:
      "已接入：国内更稳的免费源，覆盖 A 股与美股；auto 回退链中的首选。",
    dcStooqTitle: "Stooq",
    dcStooqDesc:
      "免费 CSV 源，覆盖美股/港股/欧股；若触发浏览器校验则自动跳过。",
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
    robustnessChecks: "稳健性",
    robustnessChecksDesc:
      "参数敏感性、样本外验证，以及后续的滚动窗口与模型稳健性检查。",
    robustnessPageDesc: "检查策略是否对参数过度敏感，或在样本外表现不稳定。",
    robustnessEducationalNote:
      "稳健性检查用于减少过度解读。如果一个策略只在某一组参数或样本内有效，可靠性可能不足。",
    modelLab: "模型实验室",
    modelLabDesc:
      "机器学习数据集构建、特征工程、逻辑回归、梯度提升模型，以及后续深度学习信号研究。",
    experiments: "实验",
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

    systemCurrentDataSource: "当前数据源：自动（AKShare → Yahoo → Stooq）",
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
    yes: "是",
    no: "否",
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

    paperTrading: "模拟试盘",
    paperTradingDesc:
      "用模拟账户评估今日策略信号，五档风控规则约束买卖动作。不会下真实单。",
    paperTradingNote: "仅供模拟试盘。信号采用前一日持仓语义，避免未来函数。",
    paperEvaluate: "评估信号",
    paperExecute: "执行模拟交易",
    paperReset: "重置账户",
    paperTodaySignal: "今日信号",
    paperAction: "模拟动作",
    paperAccount: "模拟账户",
    paperRisk: "风控监控",
    paperRiskLevel: "风控等级",
    paperAllowedAction: "允许操作",
    paperPortfolioValue: "账户净值",
    paperUnrealizedPnl: "浮动盈亏",
    paperRealizedPnl: "已实现盈亏",
    paperCurrentDrawdown: "当前回撤",
    paperPosition: "持仓状态",
    paperCooldown: "冷却截止",
    paperNotes: "研究备注",
    paperNotesPlaceholder: "可选：记录本次模拟试盘的研究备注…",
    paperTradeJournal: "交易日志",
    paperFlat: "空仓",
    paperLong: "多头",
    paperConfidence: "置信度",
    paperTargetPosition: "目标仓位",
    paperCash: "现金",
    paperShares: "持股数",
    paperEntryPrice: "入场价",
    paperCurrentPrice: "现价",
    paperRiskReasons: "风控原因",
    paperComponentLevels: "分项等级",
    paperExecuteResult: "执行结果",
    paperNoTrade: "未执行模拟交易。",
    paperResetConfirm: "确认将模拟账户重置为初始资金？",
    paperEvaluateFailed: "模拟试盘评估失败。",
    paperExecuteFailed: "模拟交易执行失败。",
    paperResetFailed: "重置模拟账户失败。",
    modulePaperTradingOverviewDesc:
      "带五档风控引擎的模拟向前试盘与交易日志。",
    overviewPaperAccount: "模拟账户",
    overviewPaperAccountDesc: "最近一次评估后的模拟账户快照。",
    overviewOpenPaperTrading: "进入模拟试盘",
    overviewPaperNotEvaluated: "尚未开始模拟试盘，请进入模拟试盘页评估信号。",
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
  AKShare: "AKShare",
  Stooq: "Stooq",
  "auto (AKShare / Yahoo / Stooq)": "自动（AKShare / Yahoo / Stooq）",
  "Risk indicators are within normal range": "风险指标处于正常范围",
  "Recent Sharpe ratio declined": "近期夏普比率下降",
  "MA and momentum signals conflict": "均线与动量信号冲突",
  "Short MA above long MA; next-day paper position is long.":
    "短期均线上穿长期均线；下一交易日模拟持仓为多头。",
  "Short MA not above long MA; next-day paper position is flat.":
    "短期均线未高于长期均线；下一交易日模拟持仓为空仓。",
  "Strategy signal is positive; paper account would hold.":
    "策略信号为正；模拟账户将持有仓位。",
  "Strategy signal is flat; paper account would stay in cash.":
    "策略信号为空；模拟账户保持现金。",
  "Paper trading simulation only. Not financial advice. No live orders.":
    "仅供模拟试盘，非投资建议，不会下真实单。",
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

const RISK_LABEL_ZH: Record<string, string> = {
  Green: "正常",
  "Light Yellow": "轻度预警",
  Yellow: "谨慎",
  Orange: "高风险",
  Red: "停止跟随",
};

const ALLOWED_ACTION_ZH: Record<string, string> = {
  "Normal paper trading": "正常模拟",
  "Cautious paper trading": "小心模拟",
  "Hold or reduce only": "仅持有或减仓",
  "No new positions": "暂停新增仓位",
  "Stop following / cooldown": "停止模拟跟随",
};

const PAPER_ACTION_ZH: Record<string, string> = {
  BUY: "买入",
  SELL: "卖出",
  HOLD: "持有",
  WAIT: "观望",
};

const CONFIDENCE_ZH: Record<string, string> = {
  High: "高",
  Medium: "中",
  Low: "低",
};

export function translateRiskLabel(lang: Language, label: string): string {
  if (lang === "en") {
    return label;
  }
  return RISK_LABEL_ZH[label] ?? label;
}

export function translateAllowedAction(lang: Language, action: string): string {
  if (lang === "en") {
    return action;
  }
  return ALLOWED_ACTION_ZH[action] ?? action;
}

export function translatePaperAction(lang: Language, action: string): string {
  if (lang === "en") {
    return action;
  }
  return PAPER_ACTION_ZH[action] ?? action;
}

export function translateConfidence(lang: Language, confidence: string): string {
  if (lang === "en") {
    return confidence;
  }
  return CONFIDENCE_ZH[confidence] ?? confidence;
}

export function paperRiskVariant(level: number):
  | "success"
  | "info"
  | "warning"
  | "danger"
  | "neutral" {
  if (level <= 1) {
    return "success";
  }
  if (level === 2) {
    return "info";
  }
  if (level <= 4) {
    return "warning";
  }
  return "danger";
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
