from pydantic import BaseModel, field_validator, model_validator
from typing import Optional

# 单次请求允许的最大 ticker 数量
MAX_TICKERS = 20

# lookback 交易日窗口范围
MIN_LOOKBACK_DAYS = 80
MAX_LOOKBACK_DAYS = 1000

# 行情拉取允许的数据源（请求参数）
ALLOWED_MARKET_DATA_SOURCES = frozenset({"auto", "akshare", "yahoo", "stooq"})


def normalize_request_data_source(value: str) -> str:
    """校验并标准化行情请求的 data_source。"""
    source = (value or "auto").strip().lower()
    if not source or source in {"auto", "fallback"}:
        return "auto"
    if source in ALLOWED_MARKET_DATA_SOURCES:
        return source
    raise ValueError(
        'data_source must be "auto", "akshare", "yahoo", or "stooq"'
    )


def normalize_stored_data_source(value: str) -> str:
    """标准化实验保存中的 data_source（兼容响应长描述）。"""
    source = (value or "auto").strip().lower()
    if not source:
        return "auto"
    if "stooq" in source:
        return "stooq"
    if "akshare" in source:
        return "akshare"
    if "yahoo" in source or "yfinance" in source:
        return "yahoo"
    if source in {"auto", "fallback"}:
        return "auto"
    return source


class MarketWatchRequest(BaseModel):
    """多 ticker 市场观察排名请求体。"""

    tickers: list[str]
    lookback_days: int = 120
    data_source: str = "auto"

    @field_validator("lookback_days")
    @classmethod
    def validate_lookback_days(cls, value: int) -> int:
        """校验信号排名 lookback 窗口（交易日）。"""
        if value < MIN_LOOKBACK_DAYS or value > MAX_LOOKBACK_DAYS:
            raise ValueError(
                f"lookback_days must be between {MIN_LOOKBACK_DAYS} and {MAX_LOOKBACK_DAYS}"
            )
        return value

    @field_validator("data_source")
    @classmethod
    def validate_data_source(cls, value: str) -> str:
        return normalize_request_data_source(value)

    @model_validator(mode="after")
    def normalize_tickers(self) -> "MarketWatchRequest":
        """标准化 ticker 列表：大写、去空、去重（保留顺序）、校验数量。"""
        seen: set[str] = set()
        normalized: list[str] = []

        for raw in self.tickers:
            ticker = raw.upper().strip()
            if not ticker:
                continue
            if ticker in seen:
                continue
            seen.add(ticker)
            normalized.append(ticker)

        if not normalized:
            raise ValueError("tickers must not be empty")

        if len(normalized) > MAX_TICKERS:
            raise ValueError(f"maximum {MAX_TICKERS} tickers per request")

        self.tickers = normalized
        return self


class ChartCompareRequest(BaseModel):
    """多 ticker 归一化对比图请求体。"""

    tickers: list[str]
    start_date: str = "2022-01-01"
    end_date: Optional[str] = None
    data_source: str = "auto"

    @field_validator("data_source")
    @classmethod
    def validate_data_source(cls, value: str) -> str:
        return normalize_request_data_source(value)

    @model_validator(mode="after")
    def normalize_tickers(self) -> "ChartCompareRequest":
        """标准化 ticker 列表：大写、去空、去重（保留顺序）、校验数量。"""
        seen: set[str] = set()
        normalized: list[str] = []

        for raw in self.tickers:
            ticker = raw.upper().strip()
            if not ticker:
                continue
            if ticker in seen:
                continue
            seen.add(ticker)
            normalized.append(ticker)

        if not normalized:
            raise ValueError("tickers must not be empty")

        if len(normalized) > MAX_TICKERS:
            raise ValueError(f"maximum {MAX_TICKERS} tickers per request")

        self.tickers = normalized
        return self


class BacktestRequest(BaseModel):
    """单 ticker 策略回测请求体。"""

    ticker: str
    start_date: str = "2022-01-01"
    end_date: Optional[str] = None
    strategy: str = "ma_crossover"
    short_window: int = 20
    long_window: int = 60
    momentum_window: int = 60
    combined_mode: str = "conservative"
    transaction_cost: float = 0.001
    data_source: str = "auto"

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        """标准化 ticker：大写、去空。"""
        ticker = value.upper().strip()
        if not ticker:
            raise ValueError("ticker must not be empty")
        return ticker

    @field_validator("strategy")
    @classmethod
    def validate_strategy(cls, value: str) -> str:
        """支持均线交叉、动量与组合信号策略。"""
        allowed = ("ma_crossover", "momentum", "combined_signal")
        if value not in allowed:
            raise ValueError(
                'strategy must be "ma_crossover", "momentum", or "combined_signal"'
            )
        return value

    @field_validator("combined_mode")
    @classmethod
    def validate_combined_mode(cls, value: str) -> str:
        if value not in ("conservative", "aggressive"):
            raise ValueError('combined_mode must be "conservative" or "aggressive"')
        return value

    @field_validator("data_source")
    @classmethod
    def validate_data_source(cls, value: str) -> str:
        return normalize_request_data_source(value)

    @field_validator("short_window")
    @classmethod
    def validate_short_window(cls, value: int) -> int:
        if value < 2:
            raise ValueError("short_window must be >= 2")
        return value

    @field_validator("long_window")
    @classmethod
    def validate_long_window(cls, value: int) -> int:
        if value < 2:
            raise ValueError("long_window must be >= 2")
        return value

    @field_validator("momentum_window")
    @classmethod
    def validate_momentum_window(cls, value: int) -> int:
        if value < 5 or value > 252:
            raise ValueError("momentum_window must be between 5 and 252")
        return value

    @field_validator("transaction_cost")
    @classmethod
    def validate_transaction_cost(cls, value: float) -> float:
        if value < 0 or value > 0.05:
            raise ValueError("transaction_cost must be between 0 and 0.05")
        return value

    @model_validator(mode="after")
    def validate_strategy_params(self) -> "BacktestRequest":
        if self.strategy in ("ma_crossover", "combined_signal"):
            if self.long_window <= self.short_window:
                raise ValueError("long_window must be > short_window")
        return self


class RiskReviewRequest(BacktestRequest):
    """Risk review request — backtest params plus live risk dials."""

    drawdown_mode: str = "current"
    risk_profile: str = "aggressive"

    @field_validator("drawdown_mode")
    @classmethod
    def validate_drawdown_mode(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"current", "historical"}:
            raise ValueError('drawdown_mode must be "current" or "historical"')
        return cleaned

    @field_validator("risk_profile")
    @classmethod
    def validate_risk_profile(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"conservative", "moderate", "aggressive"}:
            raise ValueError(
                'risk_profile must be "conservative", "moderate", or "aggressive"'
            )
        return cleaned


class StrategyComparisonRequest(BaseModel):
    """多策略横向对比请求体。"""

    ticker: str
    start_date: str = "2022-01-01"
    end_date: Optional[str] = None
    transaction_cost: float = 0.001
    short_window: int = 20
    long_window: int = 60
    momentum_window: int = 60
    data_source: str = "auto"

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        ticker = value.upper().strip()
        if not ticker:
            raise ValueError("ticker must not be empty")
        return ticker

    @field_validator("data_source")
    @classmethod
    def validate_data_source(cls, value: str) -> str:
        return normalize_request_data_source(value)

    @field_validator("short_window")
    @classmethod
    def validate_short_window(cls, value: int) -> int:
        if value < 2:
            raise ValueError("short_window must be >= 2")
        return value

    @field_validator("long_window")
    @classmethod
    def validate_long_window(cls, value: int) -> int:
        if value < 2:
            raise ValueError("long_window must be >= 2")
        return value

    @field_validator("momentum_window")
    @classmethod
    def validate_momentum_window(cls, value: int) -> int:
        if value < 5 or value > 252:
            raise ValueError("momentum_window must be between 5 and 252")
        return value

    @field_validator("transaction_cost")
    @classmethod
    def validate_transaction_cost(cls, value: float) -> float:
        if value < 0 or value > 0.05:
            raise ValueError("transaction_cost must be between 0 and 0.05")
        return value

    @model_validator(mode="after")
    def validate_windows(self) -> "StrategyComparisonRequest":
        if self.long_window <= self.short_window:
            raise ValueError("long_window must be > short_window")
        return self


class ModelComparisonRequest(BaseModel):
    """ML vs rule-strategy chronological comparison request."""

    ticker: str
    start_date: str = "2020-01-01"
    end_date: Optional[str] = None
    split_date: Optional[str] = None
    transaction_cost: float = 0.001
    short_window: int = 20
    long_window: int = 60
    momentum_window: int = 60
    data_source: str = "auto"
    models: Optional[list[str]] = None
    n_folds: Optional[int] = None
    scheme: str = "expanding"
    # When models is set, cnn/lstm/rl come from that list; include_lstm only applies if models is None.
    include_lstm: bool = True
    tune: bool = False
    preprocessing: str = "none"
    pca_components: Optional[int] = None
    select_k: Optional[int] = None

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        ticker = value.upper().strip()
        if not ticker:
            raise ValueError("ticker must not be empty")
        return ticker

    @field_validator("data_source")
    @classmethod
    def validate_data_source(cls, value: str) -> str:
        return normalize_request_data_source(value)

    @field_validator("preprocessing")
    @classmethod
    def validate_preprocessing(cls, value: str) -> str:
        cleaned = value.strip().lower()
        allowed = {"none", "pca", "select_kbest", "l1_select"}
        if cleaned not in allowed:
            raise ValueError(
                'preprocessing must be "none", "pca", "select_kbest", or "l1_select"'
            )
        return cleaned

    @field_validator("pca_components")
    @classmethod
    def validate_pca_components(cls, value: Optional[int]) -> Optional[int]:
        if value is None:
            return None
        if value < 1:
            raise ValueError("pca_components must be >= 1")
        return value

    @field_validator("select_k")
    @classmethod
    def validate_select_k(cls, value: Optional[int]) -> Optional[int]:
        if value is None:
            return None
        if value < 1:
            raise ValueError("select_k must be >= 1")
        return value

    @field_validator("short_window")
    @classmethod
    def validate_short_window(cls, value: int) -> int:
        if value < 2:
            raise ValueError("short_window must be >= 2")
        return value

    @field_validator("long_window")
    @classmethod
    def validate_long_window(cls, value: int) -> int:
        if value < 2:
            raise ValueError("long_window must be >= 2")
        return value

    @field_validator("momentum_window")
    @classmethod
    def validate_momentum_window(cls, value: int) -> int:
        if value < 5 or value > 252:
            raise ValueError("momentum_window must be between 5 and 252")
        return value

    @field_validator("transaction_cost")
    @classmethod
    def validate_transaction_cost(cls, value: float) -> float:
        if value < 0 or value > 0.05:
            raise ValueError("transaction_cost must be between 0 and 0.05")
        return value

    @field_validator("models")
    @classmethod
    def validate_models(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        if value is None:
            return None
        cleaned = [item.strip() for item in value if item and item.strip()]
        if not cleaned:
            raise ValueError("models must be a non-empty list when provided")
        return cleaned

    @field_validator("n_folds")
    @classmethod
    def validate_n_folds(cls, value: Optional[int]) -> Optional[int]:
        if value is None:
            return None
        if value < 2:
            raise ValueError("n_folds must be >= 2 when provided")
        return value

    @field_validator("scheme")
    @classmethod
    def validate_scheme(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"expanding", "rolling"}:
            raise ValueError('scheme must be "expanding" or "rolling"')
        return cleaned

    @model_validator(mode="after")
    def validate_dates_and_windows(self) -> "ModelComparisonRequest":
        if self.long_window <= self.short_window:
            raise ValueError("long_window must be > short_window")

        start = self.start_date.strip()
        self.start_date = start

        split_raw = self.split_date.strip() if self.split_date else ""
        if self.n_folds is None:
            if not split_raw:
                raise ValueError("split_date is required when n_folds is not provided")
            if split_raw <= start:
                raise ValueError("split_date must be after start_date")
            self.split_date = split_raw
        else:
            if split_raw and split_raw <= start:
                raise ValueError("split_date must be after start_date")
            self.split_date = split_raw or None

        if self.end_date:
            end = self.end_date.strip()
            if end and self.split_date and end <= self.split_date:
                raise ValueError("end_date must be after split_date when provided")
            self.end_date = end or None
        return self


# 参数敏感性分析默认均线窗口组合
DEFAULT_SENSITIVITY_PARAMETER_SETS = [
    {"short_window": 10, "long_window": 30},
    {"short_window": 20, "long_window": 60},
    {"short_window": 50, "long_window": 120},
    {"short_window": 50, "long_window": 200},
]

MAX_SENSITIVITY_PARAMETER_SETS = 20


class ParameterSet(BaseModel):
    """双均线窗口参数组合。"""

    short_window: int
    long_window: int

    @field_validator("short_window")
    @classmethod
    def validate_short_window(cls, value: int) -> int:
        if value < 2:
            raise ValueError("short_window must be >= 2")
        return value

    @model_validator(mode="after")
    def validate_windows(self) -> "ParameterSet":
        if self.long_window <= self.short_window:
            raise ValueError("long_window must be > short_window")
        return self


class SensitivityRequest(BaseModel):
    """多参数组合敏感性分析请求体。"""

    ticker: str
    start_date: str = "2022-01-01"
    end_date: Optional[str] = None
    strategy: str = "ma_crossover"
    transaction_cost: float = 0.001
    parameter_sets: Optional[list[ParameterSet]] = None
    data_source: str = "auto"

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        """标准化 ticker：大写、去空。"""
        ticker = value.upper().strip()
        if not ticker:
            raise ValueError("ticker must not be empty")
        return ticker

    @field_validator("strategy")
    @classmethod
    def validate_strategy(cls, value: str) -> str:
        """当前仅支持双均线交叉策略。"""
        if value != "ma_crossover":
            raise ValueError('strategy currently only allows "ma_crossover"')
        return value

    @field_validator("data_source")
    @classmethod
    def validate_data_source(cls, value: str) -> str:
        return normalize_request_data_source(value)

    @field_validator("transaction_cost")
    @classmethod
    def validate_transaction_cost(cls, value: float) -> float:
        if value < 0 or value > 0.05:
            raise ValueError("transaction_cost must be between 0 and 0.05")
        return value

    @model_validator(mode="after")
    def apply_defaults_and_validate_sets(self) -> "SensitivityRequest":
        if self.parameter_sets is None:
            self.parameter_sets = [
                ParameterSet(**item) for item in DEFAULT_SENSITIVITY_PARAMETER_SETS
            ]
        if len(self.parameter_sets) > MAX_SENSITIVITY_PARAMETER_SETS:
            raise ValueError(
                f"maximum {MAX_SENSITIVITY_PARAMETER_SETS} parameter_sets per request"
            )
        return self


class OOSRequest(BaseModel):
    """样本外切分验证请求体。"""

    ticker: str
    start_date: str = "2022-01-01"
    split_date: str = "2025-01-01"
    end_date: Optional[str] = None
    strategy: str = "ma_crossover"
    short_window: int = 20
    long_window: int = 60
    transaction_cost: float = 0.001
    data_source: str = "auto"

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        """标准化 ticker：大写、去空。"""
        ticker = value.upper().strip()
        if not ticker:
            raise ValueError("ticker must not be empty")
        return ticker

    @field_validator("strategy")
    @classmethod
    def validate_strategy(cls, value: str) -> str:
        """当前仅支持双均线交叉策略。"""
        if value != "ma_crossover":
            raise ValueError('strategy currently only allows "ma_crossover"')
        return value

    @field_validator("data_source")
    @classmethod
    def validate_data_source(cls, value: str) -> str:
        return normalize_request_data_source(value)

    @field_validator("short_window")
    @classmethod
    def validate_short_window(cls, value: int) -> int:
        if value < 2:
            raise ValueError("short_window must be >= 2")
        return value

    @field_validator("transaction_cost")
    @classmethod
    def validate_transaction_cost(cls, value: float) -> float:
        if value < 0 or value > 0.05:
            raise ValueError("transaction_cost must be between 0 and 0.05")
        return value

    @model_validator(mode="after")
    def validate_dates_and_windows(self) -> "OOSRequest":
        if self.long_window <= self.short_window:
            raise ValueError("long_window must be > short_window")

        start = self.start_date.strip()
        split = self.split_date.strip()
        if split <= start:
            raise ValueError("split_date must be after start_date")

        if self.end_date:
            end = self.end_date.strip()
            if end <= split:
                raise ValueError("end_date must be after split_date when provided")

        self.start_date = start
        self.split_date = split
        if self.end_date:
            self.end_date = self.end_date.strip()
        return self


class SaveBacktestTradeItem(BaseModel):
    """保存回测时的单笔交易记录。"""

    date: str
    action: str
    price: Optional[float] = None
    signal: Optional[float] = None
    position_after: Optional[float] = None
    reason: Optional[str] = None

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        action = value.upper().strip()
        if action not in ("BUY", "SELL"):
            raise ValueError('action must be "BUY" or "SELL"')
        return action

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        trade_date = value.strip()
        if not trade_date:
            raise ValueError("date must not be empty")
        return trade_date


class SaveBacktestRunRequest(BaseModel):
    """保存 Strategy Lab 回测结果到 Experiments。"""

    ticker: str
    market: Optional[str] = None
    data_source: str = "auto"
    strategy: str
    strategy_config: dict
    start_date: str
    end_date: Optional[str] = None
    transaction_cost: Optional[float] = None
    metrics: dict
    notes: Optional[str] = None
    trade_log: list[SaveBacktestTradeItem] = []

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        ticker = value.upper().strip()
        if not ticker:
            raise ValueError("ticker must not be empty")
        return ticker

    @field_validator("strategy")
    @classmethod
    def validate_strategy(cls, value: str) -> str:
        allowed = ("ma_crossover", "momentum", "combined_signal")
        if value not in allowed:
            raise ValueError(
                'strategy must be "ma_crossover", "momentum", or "combined_signal"'
            )
        return value

    @field_validator("data_source")
    @classmethod
    def normalize_data_source(cls, value: str) -> str:
        return normalize_stored_data_source(value)

    @field_validator("start_date")
    @classmethod
    def validate_start_date(cls, value: str) -> str:
        start = value.strip()
        if not start:
            raise ValueError("start_date must not be empty")
        return start

    @model_validator(mode="after")
    def normalize_optional_fields(self) -> "SaveBacktestRunRequest":
        if self.end_date:
            self.end_date = self.end_date.strip() or None
        if self.notes is not None:
            self.notes = self.notes.strip() or None
        if self.market is not None:
            self.market = self.market.strip() or None
        if not isinstance(self.strategy_config, dict) or not self.strategy_config:
            raise ValueError("strategy_config must be a non-empty object")
        if not isinstance(self.metrics, dict) or not self.metrics:
            raise ValueError("metrics must be a non-empty object")
        return self


class PaperTradingRequest(BacktestRequest):
    """模拟试盘请求体（复用回测参数）。"""

    account_id: str = "default"
    notes: Optional[str] = None

    @field_validator("account_id")
    @classmethod
    def normalize_account_id(cls, value: str) -> str:
        account_id = value.strip() or "default"
        return account_id

    @model_validator(mode="after")
    def normalize_notes(self) -> "PaperTradingRequest":
        if self.notes is not None:
            self.notes = self.notes.strip() or None
        return self
