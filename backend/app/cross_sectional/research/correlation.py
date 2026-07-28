"""Cross-sectional factor-value correlation and redundancy warnings."""

from __future__ import annotations

from itertools import combinations
from typing import Any

import numpy as np
import pandas as pd

from app.cross_sectional.research.rank_ic import STATUS_AVAILABLE, STATUS_UNAVAILABLE


def compute_factor_correlations(
    panel: pd.DataFrame,
    *,
    factors: tuple[str, ...] | list[str],
    minimum_pairwise_size: int,
    apply_liquidity_filter: bool,
) -> list[dict[str, Any]]:
    """
    Per-date Spearman correlations for unordered factor pairs (A < B).

    Uses rows where both factors are finite. Does not fill missing with zero.
    """
    if panel.empty or len(factors) < 2:
        return []
    work = panel.sort_values(["date", "symbol"]).copy()
    work["date"] = pd.to_datetime(work["date"])
    pairs = [
        (a, b)
        for a, b in combinations(sorted(factors), 2)
    ]
    rows: list[dict[str, Any]] = []

    for dt in sorted(work["date"].dropna().unique()):
        day = work.loc[work["date"] == dt]
        if apply_liquidity_filter and "liquidity_eligible" in day.columns:
            day = day.loc[day["liquidity_eligible"].apply(lambda v: v is True)]
        date_str = str(pd.Timestamp(dt).date())
        for a, b in pairs:
            if a not in day.columns or b not in day.columns:
                rows.append(
                    {
                        "date": date_str,
                        "factor_a": a,
                        "factor_b": b,
                        "correlation": None,
                        "sample_size": 0,
                        "status": STATUS_UNAVAILABLE,
                        "unavailable_reason": "missing_factor_column",
                    }
                )
                continue
            sub = day[[a, b]].apply(pd.to_numeric, errors="coerce").dropna()
            n = int(len(sub))
            if n < int(minimum_pairwise_size):
                rows.append(
                    {
                        "date": date_str,
                        "factor_a": a,
                        "factor_b": b,
                        "correlation": None,
                        "sample_size": n,
                        "status": STATUS_UNAVAILABLE,
                        "unavailable_reason": "below_minimum_pairwise_size",
                    }
                )
                continue
            if float(sub[a].std(ddof=0)) == 0.0 or float(sub[b].std(ddof=0)) == 0.0:
                rows.append(
                    {
                        "date": date_str,
                        "factor_a": a,
                        "factor_b": b,
                        "correlation": None,
                        "sample_size": n,
                        "status": STATUS_UNAVAILABLE,
                        "unavailable_reason": "constant_factor",
                    }
                )
                continue
            corr = float(sub[a].corr(sub[b], method="spearman"))
            if not np.isfinite(corr):
                rows.append(
                    {
                        "date": date_str,
                        "factor_a": a,
                        "factor_b": b,
                        "correlation": None,
                        "sample_size": n,
                        "status": STATUS_UNAVAILABLE,
                        "unavailable_reason": "degenerate_correlation",
                    }
                )
            else:
                rows.append(
                    {
                        "date": date_str,
                        "factor_a": a,
                        "factor_b": b,
                        "correlation": corr,
                        "sample_size": n,
                        "status": STATUS_AVAILABLE,
                        "unavailable_reason": None,
                    }
                )
    return rows


def summarize_correlations(
    daily: list[dict[str, Any]],
    *,
    warning_threshold: float,
) -> dict[str, Any]:
    pair_map: dict[tuple[str, str], list[float]] = {}
    unavailable_counts: dict[tuple[str, str], int] = {}
    for row in daily:
        key = (str(row["factor_a"]), str(row["factor_b"]))
        if row.get("status") == STATUS_AVAILABLE and row.get("correlation") is not None:
            pair_map.setdefault(key, []).append(float(row["correlation"]))
        else:
            unavailable_counts[key] = unavailable_counts.get(key, 0) + 1

    pairs_out: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    for key in sorted(pair_map.keys()) or sorted(unavailable_counts.keys()):
        vals = pair_map.get(key, [])
        mean_c = float(np.mean(vals)) if vals else None
        med_c = float(np.median(vals)) if vals else None
        std_c = float(np.std(vals, ddof=1)) if len(vals) >= 2 else None
        mean_abs = float(np.mean(np.abs(vals))) if vals else None
        item = {
            "factor_a": key[0],
            "factor_b": key[1],
            "mean_correlation": mean_c,
            "median_correlation": med_c,
            "correlation_volatility": std_c,
            "mean_absolute_correlation": mean_abs,
            "available_date_count": len(vals),
            "unavailable_date_count": unavailable_counts.get(key, 0),
        }
        pairs_out.append(item)
        if mean_abs is not None and mean_abs >= float(warning_threshold):
            warnings.append(
                {
                    "factor_a": key[0],
                    "factor_b": key[1],
                    "mean_absolute_correlation": mean_abs,
                    "threshold": float(warning_threshold),
                    "note": "Descriptive redundancy warning only; factors are not removed.",
                }
            )

    # Include pairs that never had available correlations
    for key, count in unavailable_counts.items():
        if key in pair_map:
            continue
        pairs_out.append(
            {
                "factor_a": key[0],
                "factor_b": key[1],
                "mean_correlation": None,
                "median_correlation": None,
                "correlation_volatility": None,
                "mean_absolute_correlation": None,
                "available_date_count": 0,
                "unavailable_date_count": count,
            }
        )
    pairs_out.sort(key=lambda r: (r["factor_a"], r["factor_b"]))
    return {
        "pairs": pairs_out,
        "redundancy_warnings": warnings,
        "warning_threshold": float(warning_threshold),
        "note": "Diagonal omitted; mirrored pairs collapsed to factor_a < factor_b.",
    }
