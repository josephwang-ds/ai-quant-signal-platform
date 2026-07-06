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
