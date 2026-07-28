"""Eligible cross-section filters for factor × label × date statistics."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _is_finite_series(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    arr = values.to_numpy(dtype=float, copy=False)
    return pd.Series(np.isfinite(arr), index=series.index)


def eligible_mask(
    day: pd.DataFrame,
    *,
    factor: str,
    label: str,
    apply_liquidity_filter: bool,
) -> tuple[pd.Series, dict[str, int]]:
    """
    Return boolean mask of eligible rows for one date slice.

    Exclusion reasons are counted independently where possible; a row may
    contribute to multiple reason counters if multiple fields fail.
    """
    n_total = int(len(day))
    reasons: dict[str, int] = {
        "missing_factor": 0,
        "missing_label": 0,
        "liquidity_filtered": 0,
        "missing_symbol": 0,
        "missing_date": 0,
    }
    if n_total == 0:
        return pd.Series(dtype=bool), reasons

    symbol_ok = day["symbol"].notna() & (day["symbol"].astype(str).str.len() > 0)
    date_ok = day["date"].notna()
    factor_ok = _is_finite_series(day[factor]) if factor in day.columns else pd.Series(False, index=day.index)
    label_ok = _is_finite_series(day[label]) if label in day.columns else pd.Series(False, index=day.index)

    reasons["missing_symbol"] = int((~symbol_ok).sum())
    reasons["missing_date"] = int((~date_ok).sum())
    reasons["missing_factor"] = int((~factor_ok).sum())
    reasons["missing_label"] = int((~label_ok).sum())

    mask = symbol_ok & date_ok & factor_ok & label_ok
    if apply_liquidity_filter:
        if "liquidity_eligible" not in day.columns:
            reasons["liquidity_filtered"] = int(mask.sum())
            mask = pd.Series(False, index=day.index)
        else:
            liq = day["liquidity_eligible"]
            # True only; None/False/NA exclude.
            liq_ok = liq.apply(lambda v: v is True or v is np.True_)
            reasons["liquidity_filtered"] = int((mask & ~liq_ok).sum())
            mask = mask & liq_ok

    return mask, reasons


def slice_eligible(
    panel: pd.DataFrame,
    *,
    date_value: Any,
    factor: str,
    label: str,
    apply_liquidity_filter: bool,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Filter one calendar date to the eligible cross-section."""
    day = panel.loc[panel["date"] == date_value].copy()
    mask, reasons = eligible_mask(
        day,
        factor=factor,
        label=label,
        apply_liquidity_filter=apply_liquidity_filter,
    )
    eligible = day.loc[mask].copy()
    meta = {
        "eligible_count": int(len(eligible)),
        "excluded_count": int(len(day) - len(eligible)),
        "exclusion_reasons": reasons,
        "row_count": int(len(day)),
    }
    return eligible, meta
