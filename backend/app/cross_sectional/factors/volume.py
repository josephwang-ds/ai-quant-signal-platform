"""Volume / liquidity factor family."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.cross_sectional.constants import DEFAULT_LIQUIDITY_DOLLAR_VOLUME_FLOOR


def _clean_numeric(series: pd.Series) -> pd.Series:
    out = pd.to_numeric(series, errors="coerce")
    return out.replace([np.inf, -np.inf], np.nan)


def compute_volume_factors(
    close: pd.Series,
    volume: pd.Series,
    *,
    liquidity_dollar_volume_floor: float = DEFAULT_LIQUIDITY_DOLLAR_VOLUME_FLOOR,
) -> pd.DataFrame:
    """
    Compute volume/liquidity factors from sorted close and volume series.

    Zero trailing volume variance yields null ``volume_zscore_20`` (not inf).
    """
    px = _clean_numeric(close)
    vol = _clean_numeric(volume)
    out = pd.DataFrame(index=px.index)

    mean5 = vol.rolling(window=5, min_periods=5).mean()
    mean20 = vol.rolling(window=20, min_periods=20).mean()
    std20 = vol.rolling(window=20, min_periods=20).std(ddof=1)

    ratio = mean5 / mean20
    out["volume_ratio_5_20"] = ratio.replace([np.inf, -np.inf], np.nan)

    zscore = (vol - mean20) / std20
    # Zero variance → explicit missing (avoid inf / arbitrary zeros).
    zscore = zscore.mask(std20.isna() | (std20 <= 0), np.nan)
    out["volume_zscore_20"] = zscore.replace([np.inf, -np.inf], np.nan)

    dollar = px * vol
    out["dollar_volume_20"] = dollar.rolling(window=20, min_periods=20).mean()
    eligible = (out["dollar_volume_20"] >= float(liquidity_dollar_volume_floor)).astype(
        object
    )
    # Warm-up / missing dollar volume → eligibility unknown (null), not False.
    eligible[out["dollar_volume_20"].isna()] = None
    out["liquidity_eligible"] = eligible
    return out.replace([np.inf, -np.inf], np.nan)
