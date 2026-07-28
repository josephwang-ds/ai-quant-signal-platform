"""Constants for the cross-sectional factor dataset."""

from __future__ import annotations

FACTOR_VERSION = "cs_factors_v1"
UNIVERSE_ID_LIQUID_31 = "us_liquid_31_v1"
UNIVERSE_ID_LIQUID_50 = "us_liquid_50_v1"

# Annualization for trailing daily-return volatilities (trading days).
TRADING_DAYS_PER_YEAR = 252
ANNUALIZATION_FACTOR = TRADING_DAYS_PER_YEAR**0.5

DEFAULT_LIQUIDITY_DOLLAR_VOLUME_FLOOR = 5_000_000.0
DEFAULT_PREVIEW_ROWS = 50
MAX_PREVIEW_ROWS = 200
# Demo / request guardrails (product target is ~30–100 names).
MAX_REQUEST_SYMBOLS = 100
MIN_HISTORY_DAYS = 60

# Trailing windows that require a full observation count (warm-up → null).
DOWNSIDE_VOL_WINDOW = 20
DOWNSIDE_VOL_MIN_PERIODS = 20

MOMENTUM_FACTORS: tuple[str, ...] = (
    "return_5d",
    "return_20d",
    "return_60d",
    "distance_to_ma20",
    "distance_to_ma60",
)

RISK_FACTORS: tuple[str, ...] = (
    "volatility_20d",
    "volatility_60d",
    "downside_volatility_20d",
    "max_drawdown_60d",
)

VOLUME_FACTORS: tuple[str, ...] = (
    "volume_ratio_5_20",
    "volume_zscore_20",
    "dollar_volume_20",
    "liquidity_eligible",
)

# Continuous alpha factors for Phase 2 research (exclude eligibility flag).
RESEARCH_FACTOR_COLUMNS: tuple[str, ...] = (
    MOMENTUM_FACTORS
    + RISK_FACTORS
    + (
        "volume_ratio_5_20",
        "volume_zscore_20",
        "dollar_volume_20",
    )
)

FACTOR_COLUMNS: tuple[str, ...] = MOMENTUM_FACTORS + RISK_FACTORS + VOLUME_FACTORS

# Phase 2 research defaults (31–50 name demo universes).
DEFAULT_MIN_CROSS_SECTION_SIZE = 10
DEFAULT_MIN_QUANTILE_SIZE = 2
DEFAULT_QUANTILE_COUNT = 5
DEFAULT_CORRELATION_WARNING_THRESHOLD = 0.7
DEFAULT_MIN_TURNOVER_OVERLAP = 10
DEFAULT_MIN_STABILITY_PERIOD_DATES = 20
DEFAULT_RESEARCH_PREVIEW_ROWS = 50
MAX_RESEARCH_PREVIEW_ROWS = 200

LABEL_COLUMNS: tuple[str, ...] = (
    "forward_return_5d",
    "forward_return_20d",
)

METADATA_COLUMNS: tuple[str, ...] = (
    "date",
    "symbol",
    "source",
    "data_as_of",
    "factor_version",
    "universe_version",
)

PANEL_SORT_COLUMNS: tuple[str, ...] = ("symbol", "date")
