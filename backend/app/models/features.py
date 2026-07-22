"""Historical feature frame for next-day direction models.

Leakage guard: features are lagged / contemporaneous market state only.
The label ``y_next_up`` uses a forward shift and is never included in X.
"""

from __future__ import annotations

import pandas as pd

from app.features.technical_indicators import add_technical_indicators

# Relative MA gaps replace raw ma20/ma60 to avoid price-scale leakage into models.
FEATURE_COLUMNS: list[str] = [
    "return_20d",
    "return_60d",
    "ma20_gap",
    "ma60_gap",
    "volatility_20d",
    "volume_change",
    "rsi_14",
]

_FORBIDDEN_FEATURE_TOKEN = "_next_"


def _assert_no_future_feature_columns(columns: list[str]) -> None:
    for name in columns:
        if _FORBIDDEN_FEATURE_TOKEN in name:
            raise AssertionError(
                f"FEATURE_COLUMNS must not include future-looking columns; got '{name}'."
            )
        if name.startswith("y_"):
            raise AssertionError(
                f"FEATURE_COLUMNS must not include label columns; got '{name}'."
            )


_assert_no_future_feature_columns(FEATURE_COLUMNS)


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
    df["ma20_gap"] = close / df["ma20"] - 1.0
    df["ma60_gap"] = close / df["ma60"] - 1.0

    # Label uses tomorrow's close — never placed into FEATURE_COLUMNS / X.
    df["y_next_up"] = (close.shift(-1) > close).astype(int)

    required = FEATURE_COLUMNS + ["y_next_up"]
    df = df.dropna(subset=required).copy()

    X = df[FEATURE_COLUMNS].copy()
    y = df["y_next_up"].copy()

    assert "y_next_up" not in X.columns
    assert y.name == "y_next_up"
    _assert_no_future_feature_columns(list(X.columns))

    return X, y, df
