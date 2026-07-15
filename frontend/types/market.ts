export type SignalFeatures = {
  daily_return: number;
  return_20d: number;
  return_60d: number;
  ma20: number;
  ma60: number;
  distance_to_ma20: number;
  distance_to_ma60: number;
  volatility_20d: number;
  rsi_14: number;
  volume_change: number;
};

export type SignalComponent = {
  name: string;
  passed: boolean;
  points: number;
  description: string;
};

export type SignalResult = {
  ticker: string;
  date: string;
  last_price: number;
  signal_score: number;
  signal_label: string;
  reasons: string[];
  signal_components: SignalComponent[];
  features: SignalFeatures;
};

export type MarketWatchError = {
  ticker: string;
  error: string;
};

export type MarketWatchRequest = {
  tickers: string[];
  lookback_days: number;
};

export type MarketWatchResponse = {
  data_source: string;
  lookback_days: number;
  download_start_date: string;
  latest_date: string;
  results: SignalResult[];
  errors: MarketWatchError[];
  data_note: string;
};

export type IndicatorRow = {
  date: string;
  close: number;
  ma20: number | null;
  ma60: number | null;
  rsi_14: number | null;
  volatility_20d: number | null;
  return_20d: number | null;
  return_60d: number | null;
  volume_change: number | null;
};

export type IndicatorsResponse = {
  ticker: string;
  start_date: string;
  end_date: string | null;
  data_source: string;
  rows: number;
  latest: IndicatorRow;
  data: IndicatorRow[];
};

export type CompareChartResponse = {
  data_source: string;
  start_date: string;
  end_date: string | null;
  tickers: string[];
  data: Array<Record<string, string | number | null>>;
  errors: MarketWatchError[];
};

export type ChartMode = "selected" | "compare";

export type BacktestStrategy = "ma_crossover" | "momentum" | "combined_signal";

export type CombinedMode = "conservative" | "aggressive";

export type BacktestStrategyConfig = {
  strategy: BacktestStrategy;
  short_window: number;
  long_window: number;
  momentum_window: number;
  combined_mode: CombinedMode;
  transaction_cost: number;
};

export type BacktestMetrics = {
  total_return: number | null;
  benchmark_return: number | null;
  cagr: number | null;
  volatility: number | null;
  sharpe_ratio: number | null;
  max_drawdown: number | null;
  strategy_max_drawdown: number | null;
  benchmark_max_drawdown: number | null;
  win_rate: number | null;
  number_of_trades: number | null;
  transaction_cost_total: number | null;
};

export type BacktestRow = {
  date: string;
  close: number;
  ma_short?: number | null;
  ma_long?: number | null;
  ma_signal?: number | null;
  momentum_return?: number | null;
  momentum_signal?: number | null;
  combined_signal?: number | null;
  combined_mode?: string | null;
  signal: number;
  position: number;
  daily_return: number;
  strategy_return: number;
  cumulative_strategy: number;
  cumulative_benchmark: number;
  drawdown: number;
  strategy_drawdown: number | null;
  benchmark_drawdown: number | null;
  trade_action?: "BUY" | "SELL" | null;
  trade_reason?: string | null;
};

export type TradeLogRow = {
  date: string;
  ticker: string;
  action: "BUY" | "SELL";
  price: number;
  signal: number;
  position_after: number;
  reason: string;
  strategy: string;
};

export type BacktestResponse = {
  ticker: string;
  strategy: string;
  start_date: string;
  end_date: string | null;
  data_source: string;
  parameters: {
    short_window?: number;
    long_window?: number;
    momentum_window?: number;
    combined_mode?: CombinedMode;
    transaction_cost: number;
  };
  strategy_config?: BacktestStrategyConfig;
  metrics: BacktestMetrics;
  data: BacktestRow[];
  trade_log: TradeLogRow[];
};

export type SensitivityResultRow = {
  short_window: number;
  long_window: number;
  total_return: number | null;
  benchmark_return: number | null;
  cagr: number | null;
  sharpe_ratio: number | null;
  max_drawdown: number | null;
  strategy_max_drawdown: number | null;
  benchmark_max_drawdown: number | null;
  volatility: number | null;
  win_rate: number | null;
  number_of_trades: number | null;
  transaction_cost_total: number | null;
};

export type SensitivityError = {
  short_window: number;
  long_window: number;
  error: string;
};

export type SensitivityResponse = {
  ticker: string;
  strategy: string;
  start_date: string;
  end_date: string | null;
  transaction_cost: number;
  data_source: string;
  results: SensitivityResultRow[];
  errors: SensitivityError[];
};

export type StrategyComparisonResult = {
  label: string;
  strategy: string;
  strategy_config: Partial<BacktestStrategyConfig> & Record<string, unknown>;
  metrics: BacktestMetrics;
};

export type StrategyComparisonSummary = {
  best_total_return: string | null;
  best_sharpe: string | null;
  lowest_drawdown: string | null;
  fewest_trades: string | null;
};

export type StrategyComparisonResponse = {
  ticker: string;
  start_date: string;
  end_date: string | null;
  transaction_cost: number;
  data_source: string;
  results: StrategyComparisonResult[];
  summary: StrategyComparisonSummary;
  interpretation: string[];
};

export type OOSSegmentMetrics = {
  total_return: number | null;
  benchmark_return: number | null;
  cagr: number | null;
  sharpe_ratio: number | null;
  max_drawdown: number | null;
  strategy_max_drawdown: number | null;
  benchmark_max_drawdown: number | null;
  volatility: number | null;
  win_rate: number | null;
  number_of_trades: number | null;
  transaction_cost_total: number | null;
};

export type OOSSegment = {
  period_start: string;
  period_end: string;
  rows: number;
  metrics: OOSSegmentMetrics;
};

export type OOSSegments = {
  full_period: OOSSegment;
  in_sample: OOSSegment;
  out_of_sample: OOSSegment;
};

export type OOSResponse = {
  ticker: string;
  strategy: string;
  start_date: string;
  split_date: string;
  end_date: string | null;
  data_source: string;
  parameters: {
    short_window: number;
    long_window: number;
    transaction_cost: number;
  };
  segments: OOSSegments;
  interpretation: string[];
};

export type ResearchDataProviderStatus = {
  name: string;
  installed: boolean;
  configured: boolean;
  supported_assets: string[];
  live_health_checked: boolean;
};

export type DataSourceProviderStatus = {
  name: string;
  status: string;
  asset_classes?: string[];
  note?: string;
};

export type DataSourceStatusResponse = {
  routing_mode?: string;
  providers: Array<DataSourceProviderStatus | ResearchDataProviderStatus>;
  symbol_examples?: string[];
  notes?: string[];
  active_provider?: string;
  fallback_chain?: {
    default: string[];
    a_share: string[];
  };
};

export type PriceProbeResponse = {
  ticker: string;
  start_date: string;
  data_source: string;
  rows: number;
  latest: {
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume?: number;
  };
};

export type SaveBacktestTradeItem = {
  date: string;
  action: "BUY" | "SELL" | string;
  price?: number | null;
  signal?: number | null;
  position_after?: number | null;
  reason?: string | null;
};

export type SaveBacktestRunRequest = {
  ticker: string;
  market?: string | null;
  data_source?: string;
  strategy: string;
  strategy_config: Record<string, unknown>;
  start_date: string;
  end_date?: string | null;
  transaction_cost?: number | null;
  metrics: Record<string, unknown>;
  notes?: string | null;
  trade_log: SaveBacktestTradeItem[];
};

export type SaveBacktestRunResponse = {
  id: string;
  message: string;
};

export type BacktestRunSummary = {
  id: string;
  ticker: string;
  market?: string | null;
  data_source: string;
  strategy: string;
  strategy_config: Record<string, unknown>;
  start_date: string;
  end_date?: string | null;
  transaction_cost?: number | null;
  metrics: BacktestMetrics;
  notes?: string | null;
  created_at: string;
  trade_count?: number;
};

export type BacktestRunTrade = {
  id: string;
  trade_date: string;
  action: string;
  price?: number | null;
  signal?: number | null;
  position_after?: number | null;
  reason?: string | null;
  created_at?: string;
};

export type BacktestRunDetail = BacktestRunSummary & {
  trades: BacktestRunTrade[];
};

export type BacktestRunListResponse = {
  items: BacktestRunSummary[];
  count: number;
  limit: number;
  offset: number;
};

export type PaperRiskAssessment = {
  risk_level: number;
  risk_label: string;
  allowed_action: string;
  risk_reasons: string[];
  component_levels: Record<string, number>;
};

export type PaperTodaySignal = {
  date: string;
  symbol: string;
  strategy: string;
  signal: string;
  confidence: string;
  risk_level: number;
  reason: string;
  paper_action: string;
  target_position: number;
};

export type PaperAccount = {
  account_id: string;
  cash: number;
  initial_capital: number;
  ticker: string | null;
  strategy: string | null;
  shares: number;
  entry_price: number | null;
  position: number;
  current_price: number | null;
  portfolio_value: number;
  unrealized_pnl: number;
  realized_pnl: number;
  drawdown: number;
  consecutive_losses: number;
  cooldown_until: string | null;
  last_risk_level: number | null;
  last_risk_label: string | null;
  notes: string | null;
  updated_at: string;
  trade_count: number;
};

export type PaperTradeJournalEntry = {
  trade_date: string;
  symbol: string;
  action: string;
  price: number;
  shares: number;
  cash_after: number;
  reason: string;
  risk_level: number;
};

export type PaperTradingResponse = {
  ticker: string;
  strategy: string;
  data_source: string;
  start_date: string;
  end_date: string | null;
  strategy_config: BacktestStrategyConfig;
  today_signal: PaperTodaySignal;
  risk: PaperRiskAssessment;
  account: PaperAccount;
  research_metrics: BacktestMetrics;
  trade_journal: PaperTradeJournalEntry[];
  disclaimer: string;
  execution_message?: string;
};

export type PaperAccountSnapshotResponse = {
  account: PaperAccount;
  trade_journal: PaperTradeJournalEntry[];
};
