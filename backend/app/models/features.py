"""Historical feature frame for next-day direction models.

Leakage guard: features are lagged / contemporaneous market state only.
The label ``y_next_up`` uses a forward shift and is never included in X.

Daily single-ticker samples are limited — keep FEATURE_COLUMNS in the 15–20
range (this set is at the upper bound). Hundreds of features invite overfitting.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from app.features.technical_indicators import (
    TRADING_DAYS_PER_YEAR,
    add_technical_indicators,
    calculate_rsi,
)

# Relative MA gaps replace raw MAs to avoid price-scale leakage into models.
# All columns are historical rolling / contemporaneous — no forward shifts.
FEATURE_COLUMNS: list[str] = [
    # Multi-horizon momentum
    "return_5d",
    "return_10d",
    "return_20d",
    "return_120d",
    # MA gaps + short/long structure (ma20/ma60 ratio; raw MAs stay out of X)
    "ma5_gap",
    "ma10_gap",
    "ma20_gap",
    "ma_short_long_ratio",
    # Volatility regime
    "volatility_20d",
    "volatility_60d",
    "vol_ratio_20_60",
    # Multi-horizon RSI
    "rsi_7",
    "rsi_14",
    "rsi_21",
    # MACD (EMA12 − EMA26) and signal
    "macd",
    "macd_signal",
    # Bollinger band position: (close − ma20) / (2 × std20)
    "bb_position",
    # Volume
    "volume_change_5d",
    "obv_norm",
    # Distance to 52-week high / low
    "dist_52w_high",
    "dist_52w_low",
]

_FORBIDDEN_FEATURE_TOKENS = ("_next_", "future_")


def _assert_no_future_feature_columns(columns: list[str]) -> None:
    for name in columns:
        lowered = name.lower()
        for token in _FORBIDDEN_FEATURE_TOKENS:
            if token in lowered:
                raise AssertionError(
                    f"FEATURE_COLUMNS must not include future-looking columns; got '{name}'."
                )
        if name.startswith("y_"):
            raise AssertionError(
                f"FEATURE_COLUMNS must not include label columns; got '{name}'."
            )


_assert_no_future_feature_columns(FEATURE_COLUMNS)


def feature_set_payload() -> dict[str, object]:
    """Serializable feature inventory for comparison API responses."""
    columns = list(FEATURE_COLUMNS)
    return {"columns": columns, "count": len(columns)}


def build_feature_frame(
    price_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """
    Build model features and next-day up/down label from an OHLCV frame.

    Returns:
        X: feature matrix (FEATURE_COLUMNS only)
        y: binary next-day up label (0/1)
        aligned_df: rows aligned with X/y, including date/close/daily_return
    """
    df = add_technical_indicators(price_df.copy())
    close = df["close"]
    volume = df["volume"]
    daily_return = df["daily_return"]

    # Momentum
    df["return_5d"] = close.pct_change(5)
    df["return_10d"] = close.pct_change(10)
    df["return_120d"] = close.pct_change(120)

    # Moving averages / gaps (ma20 / ma60 already from add_technical_indicators)
    df["ma5"] = close.rolling(5).mean()
    df["ma10"] = close.rolling(10).mean()
    df["ma5_gap"] = close / df["ma5"] - 1.0
    df["ma10_gap"] = close / df["ma10"] - 1.0
    df["ma20_gap"] = close / df["ma20"] - 1.0
    df["ma_short_long_ratio"] = df["ma20"] / df["ma60"] - 1.0

    # Volatility
    df["volatility_60d"] = daily_return.rolling(60).std() * math.sqrt(
        TRADING_DAYS_PER_YEAR
    )
    df["vol_ratio_20_60"] = df["volatility_20d"] / df["volatility_60d"]

    # RSI
    df["rsi_7"] = calculate_rsi(close, window=7)
    df["rsi_21"] = calculate_rsi(close, window=21)

    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()

    # Bollinger position
    std20 = close.rolling(20).std()
    df["bb_position"] = (close - df["ma20"]) / (2.0 * std20)

    # Volume
    df["volume_change_5d"] = volume.pct_change(5)
    signed_volume = np.sign(close.diff().fillna(0.0)) * volume
    obv = signed_volume.cumsum()
    obv_mean = obv.rolling(60).mean()
    obv_std = obv.rolling(60).std()
    df["obv_norm"] = (obv - obv_mean) / obv_std

    # 52-week extremes (≈252 trading days)
    rolling_max_252 = close.rolling(252).max()
    rolling_min_252 = close.rolling(252).min()
    df["dist_52w_high"] = close / rolling_max_252 - 1.0
    df["dist_52w_low"] = close / rolling_min_252 - 1.0

    # Label uses tomorrow's close / return — never placed into FEATURE_COLUMNS / X.
    df["y_next_up"] = (close.shift(-1) > close).astype(int)
    df["y_next_return"] = close.pct_change().shift(-1)

    required = FEATURE_COLUMNS + ["y_next_up", "y_next_return"]
    df = df.dropna(subset=required).copy()

    X = df[FEATURE_COLUMNS].copy()
    y = df["y_next_up"].copy()

    assert "y_next_up" not in X.columns
    assert "y_next_return" not in X.columns
    assert y.name == "y_next_up"
    _assert_no_future_feature_columns(list(X.columns))

    return X, y, df
