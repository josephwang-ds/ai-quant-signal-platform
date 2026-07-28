"""Risk factor family — trailing return volatility and drawdown."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.cross_sectional.constants import (
    ANNUALIZATION_FACTOR,
    DOWNSIDE_VOL_MIN_PERIODS,
    DOWNSIDE_VOL_WINDOW,
)


def _clean_numeric(series: pd.Series) -> pd.Series:
    out = pd.to_numeric(series, errors="coerce")
    return out.replace([np.inf, -np.inf], np.nan)


def _max_drawdown_window(prices: np.ndarray) -> float:
    """Worst peak-to-trough decline inside a fixed window of prices."""
    if prices.size == 0 or np.any(~np.isfinite(prices)):
        return np.nan
    peak = prices[0]
    max_dd = 0.0
    for price in prices:
        if not np.isfinite(price) or price <= 0:
            return np.nan
        if price > peak:
            peak = price
        drawdown = price / peak - 1.0
        if drawdown < max_dd:
            max_dd = drawdown
    return float(max_dd)


def compute_downside_deviation_20d(daily_ret: pd.Series) -> pd.Series:
    """
    Annualized downside deviation over a trailing 20-observation window.

    Definition (Phase 1 / ADR-0011):
      1. daily returns r_t
      2. replace positive returns with 0; keep negatives
      3. downside_deviation = sqrt(mean(min(r, 0)^2)) * sqrt(252)

    External field name remains ``downside_volatility_20d`` for API stability.
    Requires ``DOWNSIDE_VOL_MIN_PERIODS`` observations; otherwise null.
    Never emits infinity; insufficient history is null (not zero).
    """
    downside = daily_ret.clip(upper=0.0)
    mean_sq = (
        downside.pow(2)
        .rolling(window=DOWNSIDE_VOL_WINDOW, min_periods=DOWNSIDE_VOL_MIN_PERIODS)
        .mean()
    )
    # sqrt of mean square; null when window unavailable (mean_sq is NaN).
    rms = np.sqrt(mean_sq)
    annualized = rms * ANNUALIZATION_FACTOR
    return annualized.replace([np.inf, -np.inf], np.nan)


def compute_risk_factors(close: pd.Series) -> pd.DataFrame:
    """
    Compute risk factors from an adjusted-close series sorted by date.

    Volatilities / downside deviation are annualized with sqrt(252).
    Warm-up rows remain null.
    """
    px = _clean_numeric(close)
    daily_ret = px.pct_change()
    out = pd.DataFrame(index=px.index)

    vol20 = daily_ret.rolling(window=20, min_periods=20).std(ddof=1)
    vol60 = daily_ret.rolling(window=60, min_periods=60).std(ddof=1)
    out["volatility_20d"] = vol20 * ANNUALIZATION_FACTOR
    out["volatility_60d"] = vol60 * ANNUALIZATION_FACTOR

    out["downside_volatility_20d"] = compute_downside_deviation_20d(daily_ret)

    out["max_drawdown_60d"] = (
        px.rolling(window=60, min_periods=60)
        .apply(_max_drawdown_window, raw=True)
    )
    return out.replace([np.inf, -np.inf], np.nan)
