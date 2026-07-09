from datetime import date, timedelta
import math
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.data_sources import router as data_sources_router
from app.api.routes.database import router as database_router
from app.api.routes.experiments import router as experiments_router
from app.config import get_allowed_origins
from app.backtest.engine import (
    run_combined_signal_backtest,
    run_ma_crossover_backtest,
    run_momentum_backtest,
)
from app.backtest.compare import run_strategy_comparison
from app.backtest.metrics import calculate_backtest_metrics
from app.backtest.oos import generate_oos_interpretation, run_oos_validation
from app.data_providers.yahoo_provider import load_price_data
from app.features.technical_indicators import add_technical_indicators
from app.recommendation.scoring import score_latest_signal
from app.schemas import (
    BacktestRequest,
    ChartCompareRequest,
    MarketWatchRequest,
    OOSRequest,
    SensitivityRequest,
    StrategyComparisonRequest,
)

# 创建 FastAPI 应用实例
app = FastAPI(
    title="AI Quant Signal Backend",
    description="Learning-stage quant research API.",
)

# 允许前端跨域访问；生产环境通过 ALLOWED_ORIGINS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(data_sources_router)
app.include_router(database_router)
app.include_router(experiments_router)

# 响应中最多返回的行数（仅用于 /api/price）
MAX_PRICE_ROWS = 300

# Market Watch / 数据新鲜度说明
DATA_NOTE = (
    "Latest date is based on the most recent available daily bar from "
    "Yahoo Finance via yfinance. Data may be delayed depending on exchange "
    "and provider."
)


def _download_start_date_for_lookback(lookback_days: int) -> str:
    """
    将 lookback 交易日窗口转换为安全的 yfinance 下载起始日期。

    使用 calendar-day buffer（lookback_days * 2）以确保有足够交易日
    计算 60 日滚动指标。
    """
    buffer_calendar_days = lookback_days * 2
    start = date.today() - timedelta(days=buffer_calendar_days)
    return start.isoformat()


def _optional_number(value: Any, decimals: int) -> Optional[float]:
    """将指标值转为 JSON 数字；NaN/缺失时返回 null。"""
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return round(number, decimals)


def _row_to_dict(row) -> dict:
    """将 DataFrame 单行转为 API 响应中的价格字典。"""
    return {
        "date": row["date"].strftime("%Y-%m-%d"),
        "open": round(float(row["open"]), 4),
        "high": round(float(row["high"]), 4),
        "low": round(float(row["low"]), 4),
        "close": round(float(row["close"]), 4),
        "volume": int(row["volume"]),
    }


def _latest_indicator_dict(row) -> dict:
    """将最新一行指标数据转为 API 响应中的 latest 字典。"""
    return {
        "date": row["date"].strftime("%Y-%m-%d"),
        "close": round(float(row["close"]), 4),
        "daily_return": _optional_number(row.get("daily_return"), 6),
        "return_20d": _optional_number(row.get("return_20d"), 6),
        "return_60d": _optional_number(row.get("return_60d"), 6),
        "ma20": _optional_number(row.get("ma20"), 4),
        "ma60": _optional_number(row.get("ma60"), 4),
        "volatility_20d": _optional_number(row.get("volatility_20d"), 6),
        "rsi_14": _optional_number(row.get("rsi_14"), 4),
        "volume_change": _optional_number(row.get("volume_change"), 6),
    }


def _indicator_row_dict(row) -> dict:
    """将单行指标数据转为 API 响应中的 data 数组元素。"""
    return {
        "date": row["date"].strftime("%Y-%m-%d"),
        "close": round(float(row["close"]), 4),
        "ma20": _optional_number(row.get("ma20"), 4),
        "ma60": _optional_number(row.get("ma60"), 4),
        "rsi_14": _optional_number(row.get("rsi_14"), 4),
        "volatility_20d": _optional_number(row.get("volatility_20d"), 6),
        "return_20d": _optional_number(row.get("return_20d"), 6),
        "return_60d": _optional_number(row.get("return_60d"), 6),
        "volume_change": _optional_number(row.get("volume_change"), 6),
    }


def _optional_int(value) -> Optional[int]:
    """将可选信号列转为 int，缺失或 NaN 时返回 None。"""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    return int(value)


def _backtest_row_dict(row) -> dict:
    """将单行回测数据转为 API 响应中的 data 数组元素。"""
    return {
        "date": row["date"].strftime("%Y-%m-%d"),
        "close": round(float(row["close"]), 4),
        "ma_short": _optional_number(row.get("ma_short"), 4),
        "ma_long": _optional_number(row.get("ma_long"), 4),
        "ma_signal": _optional_int(row.get("ma_signal")),
        "signal": int(row["signal"]),
        "position": int(row["position"]),
        "daily_return": _optional_number(row.get("daily_return"), 6),
        "strategy_return": _optional_number(row.get("strategy_return"), 6),
        "cumulative_strategy": _optional_number(row.get("cumulative_strategy"), 6),
        "cumulative_benchmark": _optional_number(row.get("cumulative_benchmark"), 6),
        "drawdown": _optional_number(
            row.get("drawdown") if row.get("drawdown") is not None else row.get("strategy_drawdown"),
            6,
        ),
        "strategy_drawdown": _optional_number(
            row.get("strategy_drawdown")
            if row.get("strategy_drawdown") is not None
            else row.get("drawdown"),
            6,
        ),
        "benchmark_drawdown": _optional_number(row.get("benchmark_drawdown"), 6),
        "momentum_return": _optional_number(row.get("momentum_return"), 6),
        "momentum_signal": _optional_int(row.get("momentum_signal")),
        "combined_signal": _optional_int(row.get("combined_signal")),
        "combined_mode": row.get("combined_mode"),
        "trade": _optional_number(row.get("trade"), 6),
        "trade_action": row["trade_action"]
        if row.get("trade_action") is not None
        and not (isinstance(row.get("trade_action"), float) and math.isnan(row.get("trade_action")))
        else None,
        "trade_reason": row["trade_reason"]
        if row.get("trade_reason") is not None
        and not (isinstance(row.get("trade_reason"), float) and math.isnan(row.get("trade_reason")))
        else None,
    }


def _build_trade_log(backtest_df, ticker: str, strategy: str) -> list[dict]:
    """从回测结果中提取紧凑交易记录（仅含买卖行）。"""
    trade_log: list[dict] = []
    for _, row in backtest_df.iterrows():
        action = row.get("trade_action")
        if action is None or (isinstance(action, float) and math.isnan(action)):
            continue
        trade_log.append(
            {
                "date": row["date"].strftime("%Y-%m-%d"),
                "ticker": ticker.upper(),
                "action": action,
                "price": round(float(row["close"]), 2),
                "signal": int(row["signal"]),
                "position_after": int(row["position"]),
                "reason": row["trade_reason"],
                "strategy": strategy,
            }
        )
    return trade_log


def _backtest_strategy_config(request: BacktestRequest) -> dict[str, Any]:
    """构建回测策略配置元数据。"""
    return {
        "strategy": request.strategy,
        "short_window": request.short_window,
        "long_window": request.long_window,
        "momentum_window": request.momentum_window,
        "combined_mode": request.combined_mode,
        "transaction_cost": request.transaction_cost,
    }


def _backtest_parameters_dict(request: BacktestRequest) -> dict[str, Any]:
    """按策略类型构建回测参数字典（向后兼容）。"""
    config = _backtest_strategy_config(request)
    params: dict[str, Any] = {"transaction_cost": config["transaction_cost"]}
    if request.strategy == "ma_crossover":
        params["short_window"] = config["short_window"]
        params["long_window"] = config["long_window"]
    elif request.strategy == "momentum":
        params["momentum_window"] = config["momentum_window"]
    elif request.strategy == "combined_signal":
        params.update(
            {
                "short_window": config["short_window"],
                "long_window": config["long_window"],
                "momentum_window": config["momentum_window"],
                "combined_mode": config["combined_mode"],
            }
        )
    return params


def _sensitivity_result_row(
    short_window: int,
    long_window: int,
    metrics: dict[str, Any],
) -> dict[str, Any]:
    """将单组参数的回测指标转为敏感性分析结果行。"""
    return {
        "short_window": short_window,
        "long_window": long_window,
        "total_return": metrics.get("total_return"),
        "benchmark_return": metrics.get("benchmark_return"),
        "cagr": metrics.get("cagr"),
        "sharpe_ratio": metrics.get("sharpe_ratio"),
        "max_drawdown": metrics.get("max_drawdown"),
        "strategy_max_drawdown": metrics.get("strategy_max_drawdown"),
        "benchmark_max_drawdown": metrics.get("benchmark_max_drawdown"),
        "volatility": metrics.get("volatility"),
        "win_rate": metrics.get("win_rate"),
        "number_of_trades": metrics.get("number_of_trades"),
        "transaction_cost_total": metrics.get("transaction_cost_total"),
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    """健康检查端点，用于确认服务是否正常运行。"""
    return {"status": "ok", "service": "ai-quant-signal-backend"}


@app.get("/api/price/{ticker}")
def get_price_data(
    ticker: str,
    start_date: str = Query(default="2022-01-01", description="起始日期 YYYY-MM-DD"),
) -> dict:
    """
    获取指定股票的历史价格数据（来源：Yahoo Finance）。
    """
    normalized_ticker = ticker.upper().strip()

    try:
        df = load_price_data(normalized_ticker, start_date)
    except ValueError as exc:
        # 无效 ticker 或无数据
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        # 其他异常（网络、解析等）
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load price data for '{normalized_ticker}': {exc}",
        ) from exc

    # 取最近 MAX_PRICE_ROWS 行，保持响应轻量
    recent_df = df.tail(MAX_PRICE_ROWS)

    latest_row = df.iloc[-1]

    return {
        "ticker": normalized_ticker,
        "start_date": start_date,
        "data_source": "Yahoo Finance via yfinance",
        "rows": len(df),
        "latest": _row_to_dict(latest_row),
        "prices": [_row_to_dict(row) for _, row in recent_df.iterrows()],
    }


@app.get("/api/indicators/{ticker}")
def get_indicators(
    ticker: str,
    start_date: str = Query(default="2022-01-01", description="起始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(default=None, description="可选结束日期 YYYY-MM-DD（含当日）"),
    limit: Optional[int] = Query(default=None, ge=1, description="可选：仅返回最近 N 行"),
) -> dict:
    """
    获取指定股票的技术指标数据（基于 Yahoo Finance 价格计算）。

    图表用途默认返回完整区间数据；早期 MA/RSI 可为 null，不因指标缺失删行。
    """
    normalized_ticker = ticker.upper().strip()
    normalized_end_date = end_date.strip() if end_date else None

    try:
        df = load_price_data(normalized_ticker, start_date, normalized_end_date)
        df = add_technical_indicators(df)

        # 图表数据：仅要求 close 有效，保留滚动窗口尚未就绪的行
        df = df.dropna(subset=["close"])

        if df.empty:
            range_label = (
                f"from {start_date} to {normalized_end_date}"
                if normalized_end_date
                else f"since {start_date}"
            )
            raise HTTPException(
                status_code=400,
                detail=(
                    f"No price data available for "
                    f"'{normalized_ticker}' {range_label}."
                ),
            )

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load indicators for '{normalized_ticker}': {exc}",
        ) from exc

    output_df = df.tail(limit) if limit is not None else df
    latest_row = df.iloc[-1]

    response = {
        "ticker": normalized_ticker,
        "start_date": start_date,
        "end_date": normalized_end_date,
        "data_source": "Yahoo Finance via yfinance",
        "rows": len(output_df),
        "latest": _latest_indicator_dict(latest_row),
        "data": [_indicator_row_dict(row) for _, row in output_df.iterrows()],
    }
    return response


@app.get("/api/signal/{ticker}")
def get_signal(
    ticker: str,
    start_date: str = Query(default="2022-01-01", description="起始日期 YYYY-MM-DD"),
) -> dict:
    """
    获取指定股票的规则型信号评分（watchlist 标签，非买卖建议）。
    """
    normalized_ticker = ticker.upper().strip()

    try:
        df = load_price_data(normalized_ticker, start_date)
        df = add_technical_indicators(df)
        result = score_latest_signal(df)
    except ValueError as exc:
        msg = str(exc)
        if msg.startswith("Not enough indicator data to calculate signal score"):
            raise HTTPException(status_code=400, detail=msg) from exc
        raise HTTPException(status_code=404, detail=msg) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to score signal for '{normalized_ticker}': {exc}",
        ) from exc

    return result


def _score_ticker_signal(ticker: str, start_date: str) -> dict:
    """对单个 ticker 执行完整信号评分流程。"""
    df = load_price_data(ticker, start_date)
    df = add_technical_indicators(df)
    return score_latest_signal(df)


@app.post("/api/market-watch")
def market_watch(request: MarketWatchRequest) -> dict:
    """
    批量获取多个 ticker 的信号评分，按 signal_score 降序排名。

    单个 ticker 失败不会中断整个请求，错误会写入 errors 数组。
    """
    results: list[dict] = []
    errors: list[dict] = []

    download_start_date = _download_start_date_for_lookback(request.lookback_days)

    for ticker in request.tickers:
        try:
            signal = _score_ticker_signal(ticker, download_start_date)
            results.append(signal)
        except ValueError as exc:
            errors.append({"ticker": ticker, "error": str(exc)})
        except Exception as exc:
            errors.append(
                {
                    "ticker": ticker,
                    "error": f"Failed to process '{ticker}': {exc}",
                }
            )

    if not results:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "All tickers failed to process.",
                "errors": errors,
            },
        )

    # 按信号分数降序排列
    results.sort(key=lambda item: item["signal_score"], reverse=True)

    latest_date = max(item["date"] for item in results)

    return {
        "data_source": "Yahoo Finance via yfinance",
        "lookback_days": request.lookback_days,
        "download_start_date": download_start_date,
        "latest_date": latest_date,
        "results": results,
        "errors": errors,
        "data_note": DATA_NOTE,
    }


@app.post("/api/chart/compare")
def chart_compare(request: ChartCompareRequest) -> dict:
    """
    多 ticker 归一化收盘价对比图数据（首日 close = 100）。

    单个 ticker 失败不会中断整个请求，错误会写入 errors 数组。
    """
    normalized_end_date = request.end_date.strip() if request.end_date else None
    normalized_by_ticker: dict[str, dict[str, float]] = {}
    successful_tickers: list[str] = []
    errors: list[dict] = []

    for ticker in request.tickers:
        try:
            df = load_price_data(ticker, request.start_date, normalized_end_date)
            first_close = float(df.iloc[0]["close"])
            if first_close == 0:
                raise ValueError(f"Invalid first close price for '{ticker}'.")

            series: dict[str, float] = {}
            for _, row in df.iterrows():
                date_str = row["date"].strftime("%Y-%m-%d")
                normalized_close = round(float(row["close"]) / first_close * 100, 4)
                series[date_str] = normalized_close

            normalized_by_ticker[ticker] = series
            successful_tickers.append(ticker)
        except ValueError as exc:
            errors.append({"ticker": ticker, "error": str(exc)})
        except Exception as exc:
            errors.append(
                {"ticker": ticker, "error": f"Failed to process '{ticker}': {exc}"}
            )

    if not successful_tickers:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "All tickers failed to process.",
                "errors": errors,
            },
        )

    # 取所有成功 ticker 共有的交易日，保证对比对齐
    common_dates = set(normalized_by_ticker[successful_tickers[0]].keys())
    for ticker in successful_tickers[1:]:
        common_dates &= set(normalized_by_ticker[ticker].keys())

    aligned_dates = sorted(common_dates)

    data = []
    for date_str in aligned_dates:
        row = {"date": date_str}
        for ticker in successful_tickers:
            row[ticker] = normalized_by_ticker[ticker][date_str]
        data.append(row)

    response = {
        "data_source": "Yahoo Finance via yfinance",
        "start_date": request.start_date,
        "tickers": successful_tickers,
        "data": data,
        "errors": errors,
    }
    if normalized_end_date:
        response["end_date"] = normalized_end_date
    else:
        response["end_date"] = None
    return response


@app.post("/api/backtest")
def run_backtest(request: BacktestRequest) -> dict:
    """
    单 ticker 策略回测（支持 ma_crossover、momentum、combined_signal）。
    """
    normalized_end_date = request.end_date.strip() if request.end_date else None

    try:
        price_df = load_price_data(
            request.ticker,
            request.start_date,
            normalized_end_date,
        )

        if request.strategy == "ma_crossover":
            backtest_df = run_ma_crossover_backtest(
                price_df,
                short_window=request.short_window,
                long_window=request.long_window,
                transaction_cost=request.transaction_cost,
            )
        elif request.strategy == "momentum":
            backtest_df = run_momentum_backtest(
                price_df,
                momentum_window=request.momentum_window,
                transaction_cost=request.transaction_cost,
            )
        elif request.strategy == "combined_signal":
            backtest_df = run_combined_signal_backtest(
                price_df,
                short_window=request.short_window,
                long_window=request.long_window,
                momentum_window=request.momentum_window,
                combined_mode=request.combined_mode,
                transaction_cost=request.transaction_cost,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported strategy: '{request.strategy}'.",
            )

        metrics = calculate_backtest_metrics(backtest_df)

    except HTTPException:
        raise
    except ValueError as exc:
        msg = str(exc)
        if msg.startswith("No price data found"):
            raise HTTPException(status_code=404, detail=msg) from exc
        raise HTTPException(status_code=400, detail=msg) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run backtest for '{request.ticker}': {exc}",
        ) from exc

    return {
        "ticker": request.ticker,
        "strategy": request.strategy,
        "start_date": request.start_date,
        "end_date": normalized_end_date,
        "data_source": "Yahoo Finance via yfinance",
        "parameters": _backtest_parameters_dict(request),
        "strategy_config": _backtest_strategy_config(request),
        "metrics": metrics,
        "data": [_backtest_row_dict(row) for _, row in backtest_df.iterrows()],
        "trade_log": _build_trade_log(backtest_df, request.ticker, request.strategy),
    }


@app.post("/api/backtest/compare-strategies")
def compare_backtest_strategies(request: StrategyComparisonRequest) -> dict:
    """在同一标的与区间下对比固定策略集合的紧凑指标。"""
    normalized_end_date = request.end_date.strip() if request.end_date else None

    try:
        price_df = load_price_data(
            request.ticker,
            request.start_date,
            normalized_end_date,
        )
        comparison = run_strategy_comparison(
            price_df,
            ticker=request.ticker,
            transaction_cost=request.transaction_cost,
            short_window=request.short_window,
            long_window=request.long_window,
            momentum_window=request.momentum_window,
        )
    except HTTPException:
        raise
    except ValueError as exc:
        msg = str(exc)
        if msg.startswith("No price data found"):
            raise HTTPException(status_code=404, detail=msg) from exc
        raise HTTPException(status_code=400, detail=msg) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compare strategies for '{request.ticker}': {exc}",
        ) from exc

    return {
        "ticker": request.ticker,
        "start_date": request.start_date,
        "end_date": normalized_end_date,
        "transaction_cost": request.transaction_cost,
        "data_source": "Yahoo Finance via yfinance",
        "results": comparison["results"],
        "summary": comparison["summary"],
        "interpretation": comparison["interpretation"],
    }


@app.post("/api/backtest/sensitivity")
def run_backtest_sensitivity(request: SensitivityRequest) -> dict:
    """
    多组均线窗口参数的敏感性分析（仅返回指标摘要，不含完整时间序列）。
    """
    normalized_end_date = request.end_date.strip() if request.end_date else None

    try:
        price_df = load_price_data(
            request.ticker,
            request.start_date,
            normalized_end_date,
        )
    except ValueError as exc:
        msg = str(exc)
        if msg.startswith("No price data found"):
            raise HTTPException(status_code=404, detail=msg) from exc
        raise HTTPException(status_code=400, detail=msg) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load price data for '{request.ticker}': {exc}",
        ) from exc

    results: list[dict] = []
    errors: list[dict] = []

    for param_set in request.parameter_sets:
        try:
            backtest_df = run_ma_crossover_backtest(
                price_df,
                short_window=param_set.short_window,
                long_window=param_set.long_window,
                transaction_cost=request.transaction_cost,
            )
            metrics = calculate_backtest_metrics(backtest_df)
            results.append(
                _sensitivity_result_row(
                    param_set.short_window,
                    param_set.long_window,
                    metrics,
                )
            )
        except ValueError as exc:
            errors.append(
                {
                    "short_window": param_set.short_window,
                    "long_window": param_set.long_window,
                    "error": str(exc),
                }
            )
        except Exception as exc:
            errors.append(
                {
                    "short_window": param_set.short_window,
                    "long_window": param_set.long_window,
                    "error": (
                        f"Failed to run sensitivity for "
                        f"{param_set.short_window}/{param_set.long_window}: {exc}"
                    ),
                }
            )

    if not results:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "All parameter sets failed to process.",
                "errors": errors,
            },
        )

    return {
        "ticker": request.ticker,
        "strategy": request.strategy,
        "start_date": request.start_date,
        "end_date": normalized_end_date,
        "transaction_cost": request.transaction_cost,
        "data_source": "Yahoo Finance via yfinance",
        "results": results,
        "errors": errors,
    }


@app.post("/api/backtest/oos")
def run_backtest_oos(request: OOSRequest) -> dict:
    """
    样本外切分验证：对比全样本、样本内、样本外三段绩效。
    """
    normalized_end_date = request.end_date.strip() if request.end_date else None

    try:
        price_df = load_price_data(
            request.ticker,
            request.start_date,
            normalized_end_date,
        )

        if request.strategy != "ma_crossover":
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported strategy: '{request.strategy}'.",
            )

        segments = run_oos_validation(
            price_df,
            split_date=request.split_date,
            short_window=request.short_window,
            long_window=request.long_window,
            transaction_cost=request.transaction_cost,
        )
        interpretation = generate_oos_interpretation(segments)

    except HTTPException:
        raise
    except ValueError as exc:
        msg = str(exc)
        if msg.startswith("No price data found"):
            raise HTTPException(status_code=404, detail=msg) from exc
        raise HTTPException(status_code=400, detail=msg) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run OOS validation for '{request.ticker}': {exc}",
        ) from exc

    return {
        "ticker": request.ticker,
        "strategy": request.strategy,
        "start_date": request.start_date,
        "split_date": request.split_date,
        "end_date": normalized_end_date,
        "data_source": "Yahoo Finance via yfinance",
        "parameters": {
            "short_window": request.short_window,
            "long_window": request.long_window,
            "transaction_cost": request.transaction_cost,
        },
        "segments": segments,
        "interpretation": interpretation,
    }
