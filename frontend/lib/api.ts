import type {
  BacktestResponse,
  BacktestStrategy,
  CombinedMode,
  CompareChartResponse,
  IndicatorsResponse,
  MarketWatchResponse,
  OOSResponse,
  SensitivityResponse,
  StrategyComparisonResponse,
} from "@/types/market";

function resolveApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (configured) {
    return configured.replace(/\/$/, "");
  }
  if (process.env.NODE_ENV === "development") {
    return "http://localhost:8000";
  }
  return "";
}

const API_BASE_URL = resolveApiBaseUrl();

function buildApiUrl(path: string): string {
  if (!API_BASE_URL) {
    throw new Error(
      "NEXT_PUBLIC_API_BASE_URL is not configured. Set it in Vercel project environment variables."
    );
  }
  return `${API_BASE_URL}${path}`;
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
  const response = await fetch(buildApiUrl("/health"));

  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }

  return response.json() as Promise<HealthResponse>;
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
    body: JSON.stringify({
      tickers,
      lookback_days: lookbackDays,
    }),
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
  const params = new URLSearchParams({ start_date: startDate });
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
  const body: {
    tickers: string[];
    start_date: string;
    end_date?: string;
  } = {
    tickers,
    start_date: startDate,
  };

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
  const body: Record<string, unknown> = {
    ticker: params.ticker,
    start_date: params.start_date,
    strategy: params.strategy,
    transaction_cost: params.transaction_cost,
  };

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
  const body: RunStrategyComparisonParams = {
    ticker: params.ticker,
    start_date: params.start_date,
    transaction_cost: params.transaction_cost,
    short_window: params.short_window,
    long_window: params.long_window,
    momentum_window: params.momentum_window,
  };

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
  const body: RunBacktestSensitivityParams & { strategy: "ma_crossover" } = {
    ticker: params.ticker,
    start_date: params.start_date,
    strategy: "ma_crossover",
    transaction_cost: params.transaction_cost,
  };

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
  const body: RunOOSValidationParams & { strategy: "ma_crossover" } = {
    ticker: params.ticker,
    start_date: params.start_date,
    split_date: params.split_date,
    strategy: "ma_crossover",
    short_window: params.short_window,
    long_window: params.long_window,
    transaction_cost: params.transaction_cost,
  };

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
