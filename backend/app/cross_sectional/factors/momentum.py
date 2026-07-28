"""Momentum factor family — point-in-time trailing windows only."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _clean_numeric(series: pd.Series) -> pd.Series:
    out = pd.to_numeric(series, errors="coerce")
    return out.replace([np.inf, -np.inf], np.nan)


def compute_momentum_factors(close: pd.Series) -> pd.DataFrame:
    """
    Compute momentum factors from an adjusted-close series sorted by date.

    Warm-up rows that lack a full lookback window remain null.
    """
    px = _clean_numeric(close)
    out = pd.DataFrame(index=px.index)
    out["return_5d"] = px / px.shift(5) - 1.0
    out["return_20d"] = px / px.shift(20) - 1.0
    out["return_60d"] = px / px.shift(60) - 1.0
    ma20 = px.rolling(window=20, min_periods=20).mean()
    ma60 = px.rolling(window=60, min_periods=60).mean()
    out["distance_to_ma20"] = px / ma20 - 1.0
    out["distance_to_ma60"] = px / ma60 - 1.0
    return out.replace([np.inf, -np.inf], np.nan)
