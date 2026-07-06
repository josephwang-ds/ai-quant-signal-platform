from pydantic import BaseModel, field_validator, model_validator
from typing import Optional

# 单次请求允许的最大 ticker 数量
MAX_TICKERS = 20

# lookback 交易日窗口范围
MIN_LOOKBACK_DAYS = 80
MAX_LOOKBACK_DAYS = 1000


class MarketWatchRequest(BaseModel):
    """多 ticker 市场观察排名请求体。"""

    tickers: list[str]
    lookback_days: int = 120

    @field_validator("lookback_days")
    @classmethod
    def validate_lookback_days(cls, value: int) -> int:
        """校验信号排名 lookback 窗口（交易日）。"""
        if value < MIN_LOOKBACK_DAYS or value > MAX_LOOKBACK_DAYS:
            raise ValueError(
                f"lookback_days must be between {MIN_LOOKBACK_DAYS} and {MAX_LOOKBACK_DAYS}"
            )
        return value

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
    transaction_cost: float = 0.001

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
        """支持双均线交叉与动量策略。"""
        if value not in ("ma_crossover", "momentum"):
            raise ValueError('strategy must be "ma_crossover" or "momentum"')
        return value

    @field_validator("short_window")
    @classmethod
    def validate_short_window(cls, value: int) -> int:
        if value < 2:
            raise ValueError("short_window must be >= 2")
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
        if self.strategy == "ma_crossover" and self.long_window <= self.short_window:
            raise ValueError("long_window must be > short_window")
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
