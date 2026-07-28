"""Model-row eligibility (complete-case on selected features + label)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _finite(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    return pd.Series(np.isfinite(values.to_numpy(dtype=float, copy=False)), index=series.index)


def model_eligible_mask(
    panel: pd.DataFrame,
    *,
    features: list[str] | tuple[str, ...],
    label: str,
    apply_liquidity_filter: bool,
) -> tuple[pd.Series, dict[str, int]]:
    """
    Complete-case eligibility for the selected feature set + label.

    Trade-off: complete-case reduces sample size vs imputation, but avoids
    inventing values and keeps leakage auditing simple for Phase 3.
    Unselected columns do not affect eligibility.
    """
    reasons = {
        "missing_symbol": 0,
        "missing_date": 0,
        "missing_label": 0,
        "missing_feature": 0,
        "liquidity_filtered": 0,
    }
    if panel.empty:
        return pd.Series(dtype=bool), reasons

    symbol_ok = panel["symbol"].notna() & (panel["symbol"].astype(str).str.len() > 0)
    date_ok = panel["date"].notna()
    label_ok = _finite(panel[label]) if label in panel.columns else pd.Series(False, index=panel.index)
    feature_ok = pd.Series(True, index=panel.index)
    for col in features:
        if col not in panel.columns:
            feature_ok &= False
        else:
            feature_ok &= _finite(panel[col])

    reasons["missing_symbol"] = int((~symbol_ok).sum())
    reasons["missing_date"] = int((~date_ok).sum())
    reasons["missing_label"] = int((~label_ok).sum())
    reasons["missing_feature"] = int((~feature_ok).sum())

    mask = symbol_ok & date_ok & label_ok & feature_ok
    if apply_liquidity_filter:
        if "liquidity_eligible" not in panel.columns:
            reasons["liquidity_filtered"] = int(mask.sum())
            mask = pd.Series(False, index=panel.index)
        else:
            liq_ok = panel["liquidity_eligible"].apply(lambda v: v is True)
            reasons["liquidity_filtered"] = int((mask & ~liq_ok).sum())
            mask = mask & liq_ok
    return mask, reasons


def summarize_eligibility(
    panel: pd.DataFrame,
    mask: pd.Series,
    reasons: dict[str, int],
) -> dict[str, Any]:
    eligible = panel.loc[mask]
    return {
        "total_rows": int(len(panel)),
        "eligible_rows": int(len(eligible)),
        "excluded_rows": int(len(panel) - len(eligible)),
        "exclusion_reasons": reasons,
        "eligible_dates": int(eligible["date"].nunique()) if not eligible.empty else 0,
        "eligible_symbols": int(eligible["symbol"].nunique()) if not eligible.empty else 0,
        "missing_data_policy": "complete_case_selected_features",
    }
