"""Named universes and factor builders for cross-sectional validation."""

from __future__ import annotations

import numpy as np
import pandas as pd

US_SECTOR_ETFS: tuple[str, ...] = (
    "XLB",
    "XLE",
    "XLF",
    "XLI",
    "XLK",
    "XLP",
    "XLU",
    "XLV",
    "XLY",
    "XLRE",
)

UNIVERSE_PRESETS: dict[str, tuple[str, ...]] = {
    "us_sector_etfs": US_SECTOR_ETFS,
}

SUPPORTED_FACTORS = frozenset({"momentum", "low_volatility"})
COMING_SOON_FACTORS = frozenset({"value"})


def resolve_universe(universe_id: str) -> tuple[str, ...]:
    key = str(universe_id or "").strip().lower()
    if key not in UNIVERSE_PRESETS:
        raise ValueError(
            f"Unknown universe '{universe_id}'. Supported: {sorted(UNIVERSE_PRESETS)}"
        )
    return UNIVERSE_PRESETS[key]


def month_end_index(dates: pd.DatetimeIndex) -> pd.DatetimeIndex:
    idx = pd.DatetimeIndex(dates)
    if idx.empty:
        return idx
    s = pd.Series(idx, index=idx)
    ends = s.groupby(s.dt.to_period("M")).max()
    return pd.DatetimeIndex(pd.to_datetime(ends.values)).sort_values()


def build_price_panel(price_by_symbol: dict[str, pd.Series]) -> pd.DataFrame:
    """Wide daily close panel; columns = symbols."""
    frame = pd.DataFrame(price_by_symbol).sort_index()
    frame.index = pd.DatetimeIndex(frame.index)
    return frame.astype(float)


def build_monthly_forward_returns(
    price_panel: pd.DataFrame,
    *,
    holding_period_months: int = 1,
) -> pd.DataFrame:
    """
    Month-end forward return over ``holding_period_months`` calendar months
    of month-end prices: P_{t+h}/P_t - 1, indexed by formation month-end.
    """
    if holding_period_months < 1:
        raise ValueError("holding_period_months must be >= 1")
    month_ends = month_end_index(price_panel.index)
    monthly = price_panel.reindex(month_ends).ffill()
    forward = monthly.shift(-holding_period_months) / monthly - 1.0
    # Drop trailing rows without complete forward window
    return forward.iloc[:-holding_period_months] if holding_period_months else forward


def build_momentum_factor(
    price_panel: pd.DataFrame,
    *,
    lookback_months: int = 12,
    skip_months: int = 1,
) -> pd.DataFrame:
    """12-1 momentum at month-end: P_{t-skip}/P_{t-lookback} - 1."""
    if lookback_months <= skip_months:
        raise ValueError("lookback_months must exceed skip_months")
    month_ends = month_end_index(price_panel.index)
    monthly = price_panel.reindex(month_ends).ffill()
    lagged = monthly.shift(skip_months)
    past = monthly.shift(lookback_months)
    factor = lagged / past - 1.0
    return factor


def build_low_volatility_factor(
    price_panel: pd.DataFrame,
    *,
    window_days: int = 60,
) -> pd.DataFrame:
    """−1 × realized daily-return vol over ``window_days``, sampled at month-end."""
    if window_days < 5:
        raise ValueError("window_days must be >= 5")
    daily_ret = price_panel.pct_change()
    vol = daily_ret.rolling(window=window_days, min_periods=window_days).std()
    month_ends = month_end_index(price_panel.index)
    sampled = vol.reindex(month_ends).ffill()
    return -sampled


def build_factor_panel(
    factor_id: str,
    price_panel: pd.DataFrame,
) -> pd.DataFrame:
    key = str(factor_id or "").strip().lower()
    if key in COMING_SOON_FACTORS:
        raise ValueError(f"Factor '{factor_id}' is Coming Soon.")
    if key == "momentum":
        return build_momentum_factor(price_panel)
    if key == "low_volatility":
        return build_low_volatility_factor(price_panel)
    raise ValueError(
        f"Unsupported factor '{factor_id}'. Supported: {sorted(SUPPORTED_FACTORS)}"
    )


def align_factor_and_forward(
    factor: pd.DataFrame,
    forward: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Intersect periods and columns; drop all-null rows."""
    periods = factor.index.intersection(forward.index)
    columns = factor.columns.intersection(forward.columns)
    f = factor.loc[periods, columns]
    r = forward.loc[periods, columns]
    mask = f.notna().sum(axis=1) >= 5
    return f.loc[mask], r.loc[mask]
