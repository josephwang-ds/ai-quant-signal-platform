import type {
  BacktestResponse,
  BacktestRunDetail,
  BacktestRunListResponse,
  BacktestStrategy,
  CombinedMode,
  CompareChartResponse,
  DataSourceStatusResponse,
  IndicatorsResponse,
  MarketWatchResponse,
  OOSResponse,
  PriceProbeResponse,
  SaveBacktestRunRequest,
  SaveBacktestRunResponse,
  SensitivityResponse,
  StrategyComparisonResponse,
  PaperAccountSnapshotResponse,
  PaperTradingResponse,
} from "@/types/market";
import { getDataSourcePreference } from "@/lib/dataSourcePreference";
import type { MarketDataSource } from "@/lib/dataSourcePreference";
import { buildApiUrl } from "@/lib/apiConfig";
import {
  API_REQUEST_TIMEOUT_MS,
  API_STATUS_TIMEOUT_MS,
  requestJson,
} from "@/lib/apiRequest";

function withPreferredDataSource(
  body: Record<string, unknown>
): Record<string, unknown> {
  return {
    ...body,
    data_source: getDataSourcePreference(),
  };
}

// 健康检查接口返回的数据结构
export type HealthResponse = {
  status: string;
  service: string;
};

type FastApiValidationError = {
  loc?: (string | number)[];
  msg?: string;
};

/**
 * 调用后端 GET /health，确认 FastAPI 服务是否可用。
 */
export async function getBackendHealth(): Promise<HealthResponse> {
  return requestJson<HealthResponse>(
    "/health",
    {},
    { timeoutMs: API_STATUS_TIMEOUT_MS }
  );
}

/**
 * 获取数据源配置/安装状态；此端点不探测提供商的实时连通性。
 */
export async function getDataSourceStatus(): Promise<DataSourceStatusResponse> {
  return requestJson<DataSourceStatusResponse>(
    "/api/data-sources/status",
    { cache: "no-store" },
    { timeoutMs: API_STATUS_TIMEOUT_MS }
  );
}

/**
 * 调用后端 GET /api/price/{ticker}，用于 Data Center 探测实际命中源。
 */
export async function probePriceData(
  ticker = "AAPL",
  startDate = "2024-01-01",
  dataSource?: MarketDataSource
): Promise<PriceProbeResponse> {
  const source = dataSource ?? getDataSourcePreference();
  const params = new URLSearchParams({
    start_date: startDate,
    data_source: source,
  });

  const response = await fetch(
    `${buildApiUrl(`/api/price/${encodeURIComponent(ticker)}`)}?${params.toString()}`,
    { cache: "no-store" }
  );

  if (!response.ok) {
    const message = await parseApiError(
      response,
      `Price probe failed for ${ticker} (status ${response.status})`
    );
    throw new Error(message);
  }

  return response.json() as Promise<PriceProbeResponse>;
}

/**
 * 解析 FastAPI 错误响应为可读错误信息。
 */
async function parseApiError(response: Response, fallback: string): Promise<string> {
  try {
    const body = (await response.json()) as {
      detail?:
        | string
        | FastApiValidationError[]
        | { message?: string; errors?: { ticker: string; error: string }[] };
      message?: string;
    };

    if (typeof body.detail === "string") {
      return body.detail;
    }

    if (Array.isArray(body.detail)) {
      const messages = body.detail
        .map((item) => {
          if (!item || typeof item !== "object" || !item.msg) {
            return null;
          }
          const location = Array.isArray(item.loc)
            ? item.loc.filter((part) => part !== "body").join(".")
            : "";
          return location ? `${location}: ${item.msg}` : item.msg;
        })
        .filter(Boolean);
      if (messages.length > 0) {
        return messages.join("; ");
      }
    }

    if (
      body.detail &&
      typeof body.detail === "object" &&
      !Array.isArray(body.detail) &&
      ("message" in body.detail || "errors" in body.detail)
    ) {
      const structuredDetail = body.detail as {
        message?: string;
        errors?: { ticker: string; error: string }[];
      };
      const parts = [structuredDetail.message ?? fallback];
      if (structuredDetail.errors?.length) {
        const errorLines = structuredDetail.errors.map(
          (item) => `${item.ticker}: ${item.error}`
        );
        parts.push(errorLines.join("; "));
      }
      return parts.filter(Boolean).join(" — ");
    }

    if (body.message) {
      return body.message;
    }
  } catch {
    // 无法解析 JSON 时使用默认信息
  }

  return fallback;
}

/**
 * 调用后端 POST /api/market-watch，获取多 ticker 信号排名。
 */
export async function runMarketWatch(
  tickers: string[],
  lookbackDays: number
): Promise<MarketWatchResponse> {
  const response = await fetch(buildApiUrl("/api/market-watch"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    body: JSON.stringify(
      withPreferredDataSource({
        tickers,
        lookback_days: lookbackDays,
      })
    ),
  });

  if (!response.ok) {
    const message = await parseApiError(
      response,
      `Market watch request failed with status ${response.status}`
    );
    throw new Error(message);
  }

  return response.json() as Promise<MarketWatchResponse>;
}

/**
 * 调用后端 GET /api/indicators/{ticker}，获取价格与均线数据。
 */
export async function getIndicators(
  ticker: string,
  startDate: string,
  endDate?: string
): Promise<IndicatorsResponse> {
  const params = new URLSearchParams({
    start_date: startDate,
    data_source: getDataSourcePreference(),
  });
  const trimmedEndDate = endDate?.trim();
  if (trimmedEndDate) {
    params.set("end_date", trimmedEndDate);
  }

  const response = await fetch(
    `${buildApiUrl(`/api/indicators/${encodeURIComponent(ticker)}`)}?${params.toString()}`,
    { cache: "no-store" }
  );

  if (!response.ok) {
    const message = await parseApiError(
      response,
      `Failed to load indicators for ${ticker} (status ${response.status})`
    );
    throw new Error(message);
  }

  return response.json() as Promise<IndicatorsResponse>;
}

/**
 * 调用后端 POST /api/chart/compare，获取多 ticker 归一化对比图数据。
 */
export async function runCompareChart(
  tickers: string[],
  startDate: string,
  endDate?: string | null
): Promise<CompareChartResponse> {
  const body: Record<string, unknown> = withPreferredDataSource({
    tickers,
    start_date: startDate,
  });

  const trimmedEndDate = endDate?.trim();
  if (trimmedEndDate) {
    body.end_date = trimmedEndDate;
  }

  const response = await fetch(buildApiUrl("/api/chart/compare"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const message = await parseApiError(
      response,
      `Chart compare request failed with status ${response.status}`
    );
    throw new Error(message);
  }

  return response.json() as Promise<CompareChartResponse>;
}

export type RunBacktestParams = {
  ticker: string;
  start_date: string;
  end_date?: string | null;
  strategy: BacktestStrategy;
  short_window?: number;
  long_window?: number;
  momentum_window?: number;
  combined_mode?: CombinedMode;
  transaction_cost: number;
};

/**
 * 调用后端 POST /api/backtest，运行策略回测。
 */
export async function runBacktest(params: RunBacktestParams): Promise<BacktestResponse> {
  const body: Record<string, unknown> = withPreferredDataSource({
    ticker: params.ticker,
    start_date: params.start_date,
    strategy: params.strategy,
    transaction_cost: params.transaction_cost,
  });

  if (params.strategy === "ma_crossover") {
    body.short_window = params.short_window;
    body.long_window = params.long_window;
  } else if (params.strategy === "momentum") {
    body.momentum_window = params.momentum_window;
  } else if (params.strategy === "combined_signal") {
    body.short_window = params.short_window;
    body.long_window = params.long_window;
    body.momentum_window = params.momentum_window;
    body.combined_mode = params.combined_mode;
  }

  const trimmedEndDate = params.end_date?.trim();
  if (trimmedEndDate) {
    body.end_date = trimmedEndDate;
  }

  const response = await fetch(buildApiUrl("/api/backtest"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const message = await parseApiError(
      response,
      `Backtest request failed with status ${response.status}`
    );
    throw new Error(message);
  }

  return response.json() as Promise<BacktestResponse>;
}

export type RunStrategyComparisonParams = {
  ticker: string;
  start_date: string;
  end_date?: string | null;
  transaction_cost: number;
  short_window: number;
  long_window: number;
  momentum_window: number;
};

/**
 * 调用后端 POST /api/backtest/compare-strategies，横向对比固定策略集合。
 */
export async function runStrategyComparison(
  params: RunStrategyComparisonParams
): Promise<StrategyComparisonResponse> {
  const body: Record<string, unknown> = withPreferredDataSource({
    ticker: params.ticker,
    start_date: params.start_date,
    transaction_cost: params.transaction_cost,
    short_window: params.short_window,
    long_window: params.long_window,
    momentum_window: params.momentum_window,
  });

  const trimmedEndDate = params.end_date?.trim();
  if (trimmedEndDate) {
    body.end_date = trimmedEndDate;
  }

  const response = await fetch(buildApiUrl("/api/backtest/compare-strategies"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const message = await parseApiError(
      response,
      `Strategy comparison request failed with status ${response.status}`
    );
    throw new Error(message);
  }

  return response.json() as Promise<StrategyComparisonResponse>;
}

export type ModelComparisonKind = "ml" | "rule";

export type ModelComparisonMetrics = {
  total_return: number | null;
  benchmark_return?: number | null;
  cagr?: number | null;
  volatility?: number | null;
  sharpe_ratio: number | null;
  max_drawdown: number | null;
  strategy_max_drawdown?: number | null;
  number_of_trades: number | null;
  transaction_cost_total?: number | null;
  win_rate?: number | null;
};

export type ModelComparisonResult = {
  label: string;
  kind: ModelComparisonKind;
  strategy: string;
  metrics: ModelComparisonMetrics;
  test_start?: string;
  test_end?: string;
  directional_accuracy?: number;
  directional_accuracy_note?: string;
  feature_importance?: Record<string, number>;
};

export type ModelComparisonSummary = {
  best_total_return: string | null;
  best_sharpe: string | null;
  lowest_drawdown: string | null;
  fewest_trades: string | null;
};

export type ModelComparisonEquityRow = {
  date: string;
  [label: string]: string | number;
};

export type ModelComparisonResponse = {
  ticker?: string;
  start_date?: string;
  end_date?: string | null;
  data_source?: string;
  split_date: string;
  n_train: number;
  n_test: number;
  test_start: string;
  test_end: string;
  results: ModelComparisonResult[];
  summary: ModelComparisonSummary;
  interpretation: string[];
  equity_curve_labels?: string[];
  equity_curve_rows?: ModelComparisonEquityRow[];
};

export type RunModelComparisonParams = {
  ticker: string;
  start_date: string;
  end_date?: string | null;
  split_date: string;
  transaction_cost: number;
  short_window: number;
  long_window: number;
  momentum_window: number;
  models?: string[];
};

/**
 * 调用后端 POST /api/v1/models/compare：时序切分下对比规则策略与 ML 模型。
 */
export async function runModelComparison(
  params: RunModelComparisonParams
): Promise<ModelComparisonResponse> {
  const body: Record<string, unknown> = withPreferredDataSource({
    ticker: params.ticker,
    start_date: params.start_date,
    split_date: params.split_date,
    transaction_cost: params.transaction_cost,
    short_window: params.short_window,
    long_window: params.long_window,
    momentum_window: params.momentum_window,
  });

  const trimmedEndDate = params.end_date?.trim();
  if (trimmedEndDate) {
    body.end_date = trimmedEndDate;
  }
  if (params.models && params.models.length > 0) {
    body.models = params.models;
  }

  return requestJson<ModelComparisonResponse>(
    "api/v1/models/compare",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
      body: JSON.stringify(body),
    },
    { timeoutMs: API_REQUEST_TIMEOUT_MS }
  );
}

export type RunRiskReviewParams = RunBacktestParams;

export type RiskReviewAssessment = {
  risk_level: number;
  risk_label: string;
  allowed_action: string;
  risk_reasons: string[];
  component_levels: Record<string, number>;
};

export type RiskReviewResponse = {
  ticker: string;
  strategy: string;
  start_date: string;
  end_date: string | null;
  data_source: string;
  metrics: Record<string, number | null>;
  risk: RiskReviewAssessment;
};

/**
 * 调用后端 POST /api/v1/risk/review：回测指标 → 五档风控评估。
 */
export async function runRiskReview(
  params: RunRiskReviewParams
): Promise<RiskReviewResponse> {
  const body: Record<string, unknown> = withPreferredDataSource({
    ticker: params.ticker,
    start_date: params.start_date,
    strategy: params.strategy,
    transaction_cost: params.transaction_cost,
  });

  if (params.strategy === "ma_crossover") {
    body.short_window = params.short_window;
    body.long_window = params.long_window;
  } else if (params.strategy === "momentum") {
    body.momentum_window = params.momentum_window;
  } else if (params.strategy === "combined_signal") {
    body.short_window = params.short_window;
    body.long_window = params.long_window;
    body.momentum_window = params.momentum_window;
    body.combined_mode = params.combined_mode;
  }

  const trimmedEndDate = params.end_date?.trim();
  if (trimmedEndDate) {
    body.end_date = trimmedEndDate;
  }

  return requestJson<RiskReviewResponse>(
    "api/v1/risk/review",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
      body: JSON.stringify(body),
    },
    { timeoutMs: API_REQUEST_TIMEOUT_MS }
  );
}

export type RunBacktestSensitivityParams = {
  ticker: string;
  start_date: string;
  end_date?: string | null;
  transaction_cost: number;
};

/**
 * 调用后端 POST /api/backtest/sensitivity，比较多组均线窗口参数。
 */
export async function runBacktestSensitivity(
  params: RunBacktestSensitivityParams
): Promise<SensitivityResponse> {
  const body: Record<string, unknown> = withPreferredDataSource({
    ticker: params.ticker,
    start_date: params.start_date,
    strategy: "ma_crossover",
    transaction_cost: params.transaction_cost,
  });

  const trimmedEndDate = params.end_date?.trim();
  if (trimmedEndDate) {
    body.end_date = trimmedEndDate;
  }

  const response = await fetch(buildApiUrl("/api/backtest/sensitivity"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const message = await parseApiError(
      response,
      `Sensitivity analysis request failed with status ${response.status}`
    );
    throw new Error(message);
  }

  return response.json() as Promise<SensitivityResponse>;
}

export type RunOOSValidationParams = {
  ticker: string;
  start_date: string;
  split_date: string;
  end_date?: string | null;
  short_window: number;
  long_window: number;
  transaction_cost: number;
};

/**
 * 调用后端 POST /api/backtest/oos，运行样本外切分验证。
 */
export async function runOOSValidation(
  params: RunOOSValidationParams
): Promise<OOSResponse> {
  const body: Record<string, unknown> = withPreferredDataSource({
    ticker: params.ticker,
    start_date: params.start_date,
    split_date: params.split_date,
    strategy: "ma_crossover",
    short_window: params.short_window,
    long_window: params.long_window,
    transaction_cost: params.transaction_cost,
  });

  const trimmedEndDate = params.end_date?.trim();
  if (trimmedEndDate) {
    body.end_date = trimmedEndDate;
  }

  const response = await fetch(buildApiUrl("/api/backtest/oos"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const message = await parseApiError(
      response,
      `OOS validation request failed with status ${response.status}`
    );
    throw new Error(message);
  }

  return response.json() as Promise<OOSResponse>;
}

/**
 * 调用后端 POST /api/experiments/backtest-runs，保存回测实验。
 */
export async function saveBacktestRun(
  payload: SaveBacktestRunRequest
): Promise<SaveBacktestRunResponse> {
  const response = await fetch(buildApiUrl("/api/experiments/backtest-runs"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const message = await parseApiError(
      response,
      `Save backtest run failed with status ${response.status}`
    );
    throw new Error(message);
  }

  return response.json() as Promise<SaveBacktestRunResponse>;
}

/**
 * 调用后端 GET /api/experiments/backtest-runs，列出已保存实验。
 */
export async function listBacktestRuns(
  limit = 50,
  offset = 0
): Promise<BacktestRunListResponse> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });

  const response = await fetch(
    `${buildApiUrl("/api/experiments/backtest-runs")}?${params.toString()}`,
    { cache: "no-store" }
  );

  if (!response.ok) {
    const message = await parseApiError(
      response,
      `List backtest runs failed with status ${response.status}`
    );
    throw new Error(message);
  }

  return response.json() as Promise<BacktestRunListResponse>;
}

/**
 * 调用后端 GET /api/experiments/backtest-runs/{id}，获取实验详情。
 */
export async function getBacktestRun(runId: string): Promise<BacktestRunDetail> {
  const response = await fetch(
    buildApiUrl(`/api/experiments/backtest-runs/${encodeURIComponent(runId)}`),
    { cache: "no-store" }
  );

  if (!response.ok) {
    const message = await parseApiError(
      response,
      `Get backtest run failed with status ${response.status}`
    );
    throw new Error(message);
  }

  return response.json() as Promise<BacktestRunDetail>;
}

/**
 * 调用后端 DELETE /api/experiments/backtest-runs/{id}，删除实验。
 */
export async function deleteBacktestRun(
  runId: string
): Promise<{ id: string; message: string }> {
  const response = await fetch(
    buildApiUrl(`/api/experiments/backtest-runs/${encodeURIComponent(runId)}`),
    {
      method: "DELETE",
      cache: "no-store",
    }
  );

  if (!response.ok) {
    const message = await parseApiError(
      response,
      `Delete backtest run failed with status ${response.status}`
    );
    throw new Error(message);
  }

  return response.json() as Promise<{ id: string; message: string }>;
}

export type PaperTradingParams = RunBacktestParams & {
  account_id?: string;
  notes?: string | null;
};

function buildPaperTradingBody(params: PaperTradingParams): Record<string, unknown> {
  const body: Record<string, unknown> = withPreferredDataSource({
    ticker: params.ticker,
    start_date: params.start_date,
    strategy: params.strategy,
    transaction_cost: params.transaction_cost,
    account_id: params.account_id ?? "default",
  });

  if (params.strategy === "ma_crossover") {
    body.short_window = params.short_window;
    body.long_window = params.long_window;
  } else if (params.strategy === "momentum") {
    body.momentum_window = params.momentum_window;
  } else if (params.strategy === "combined_signal") {
    body.short_window = params.short_window;
    body.long_window = params.long_window;
    body.momentum_window = params.momentum_window;
    body.combined_mode = params.combined_mode;
  }

  const trimmedEndDate = params.end_date?.trim();
  if (trimmedEndDate) {
    body.end_date = trimmedEndDate;
  }

  if (params.notes?.trim()) {
    body.notes = params.notes.trim();
  }

  return body;
}

/**
 * 调用后端 GET /api/paper/account，获取模拟账户快照。
 */
export async function getPaperAccount(
  accountId = "default"
): Promise<PaperAccountSnapshotResponse> {
  const response = await fetch(
    buildApiUrl(`/api/paper/account?account_id=${encodeURIComponent(accountId)}`),
    { cache: "no-store" }
  );

  if (!response.ok) {
    const message = await parseApiError(
      response,
      `Paper account request failed with status ${response.status}`
    );
    throw new Error(message);
  }

  return response.json() as Promise<PaperAccountSnapshotResponse>;
}

/**
 * 调用后端 POST /api/paper/dashboard，评估今日信号与风控（不执行交易）。
 */
export async function evaluatePaperTrading(
  params: PaperTradingParams
): Promise<PaperTradingResponse> {
  const response = await fetch(buildApiUrl("/api/paper/dashboard"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    body: JSON.stringify(buildPaperTradingBody(params)),
  });

  if (!response.ok) {
    const message = await parseApiError(
      response,
      `Paper dashboard request failed with status ${response.status}`
    );
    throw new Error(message);
  }

  return response.json() as Promise<PaperTradingResponse>;
}

/**
 * 调用后端 POST /api/paper/execute，在风控允许时执行模拟交易。
 */
export async function executePaperTrading(
  params: PaperTradingParams
): Promise<PaperTradingResponse> {
  const response = await fetch(buildApiUrl("/api/paper/execute"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    body: JSON.stringify(buildPaperTradingBody(params)),
  });

  if (!response.ok) {
    const message = await parseApiError(
      response,
      `Paper execute request failed with status ${response.status}`
    );
    throw new Error(message);
  }

  return response.json() as Promise<PaperTradingResponse>;
}

/**
 * 调用后端 POST /api/paper/reset，重置模拟账户。
 */
export async function resetPaperAccount(
  accountId = "default"
): Promise<{ account: PaperAccountSnapshotResponse["account"]; message: string }> {
  const response = await fetch(
    buildApiUrl(`/api/paper/reset?account_id=${encodeURIComponent(accountId)}`),
    {
      method: "POST",
      cache: "no-store",
    }
  );

  if (!response.ok) {
    const message = await parseApiError(
      response,
      `Paper reset request failed with status ${response.status}`
    );
    throw new Error(message);
  }

  return response.json() as Promise<{
    account: PaperAccountSnapshotResponse["account"];
    message: string;
  }>;
}
