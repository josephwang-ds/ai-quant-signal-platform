"""Calendar-year RankIC / spread stability summaries."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.cross_sectional.research.rank_ic import STATUS_AVAILABLE, STATUS_UNAVAILABLE


def summarize_stability(
    daily_ic: list[dict[str, Any]],
    daily_spreads: list[dict[str, Any]],
    *,
    minimum_period_dates: int,
) -> dict[str, Any]:
    """
    Group available daily RankIC by calendar year.

    Periods below minimum available dates → unavailable (not zero metrics).
    """
    ic_by_year: dict[str, list[float]] = {}
    for row in daily_ic:
        if row.get("status") != STATUS_AVAILABLE or row.get("rank_ic") is None:
            continue
        year = str(row["date"])[:4]
        ic_by_year.setdefault(year, []).append(float(row["rank_ic"]))

    spread_by_year: dict[str, list[float]] = {}
    for row in daily_spreads:
        if row.get("status") != STATUS_AVAILABLE or row.get("top_minus_bottom") is None:
            continue
        year = str(row["date"])[:4]
        spread_by_year.setdefault(year, []).append(float(row["top_minus_bottom"]))

    years = sorted(set(ic_by_year) | set(spread_by_year))
    periods: list[dict[str, Any]] = []
    for year in years:
        vals = ic_by_year.get(year, [])
        spreads = spread_by_year.get(year, [])
        if len(vals) < int(minimum_period_dates):
            periods.append(
                {
                    "period": year,
                    "status": STATUS_UNAVAILABLE,
                    "unavailable_reason": "below_minimum_period_dates",
                    "available_date_count": len(vals),
                    "mean_rank_ic": None,
                    "median_rank_ic": None,
                    "icir": None,
                    "positive_ic_ratio": None,
                    "mean_top_minus_bottom": None,
                }
            )
            continue
        arr = np.asarray(vals, dtype=float)
        mean_ic = float(arr.mean())
        std = float(arr.std(ddof=1)) if len(arr) >= 2 else float("nan")
        icir = (
            float(mean_ic / std)
            if len(arr) >= 2 and np.isfinite(std) and std != 0.0
            else None
        )
        periods.append(
            {
                "period": year,
                "status": STATUS_AVAILABLE,
                "unavailable_reason": None,
                "available_date_count": len(vals),
                "mean_rank_ic": mean_ic,
                "median_rank_ic": float(np.median(arr)),
                "icir": icir,
                "positive_ic_ratio": float((arr > 0).sum() / len(arr)),
                "mean_top_minus_bottom": float(np.mean(spreads)) if spreads else None,
            }
        )

    available_periods = [p for p in periods if p["status"] == STATUS_AVAILABLE]
    means = [p["mean_rank_ic"] for p in available_periods if p["mean_rank_ic"] is not None]
    periods_positive = sum(1 for m in means if m > 0)
    periods_negative = sum(1 for m in means if m < 0)
    n_p = len(means)
    return {
        "periods": periods,
        "periods_positive": periods_positive if n_p else None,
        "periods_negative": periods_negative if n_p else None,
        "sign_consistency_ratio": (
            float(max(periods_positive, periods_negative) / n_p) if n_p else None
        ),
        "worst_period_mean_ic": float(min(means)) if means else None,
        "best_period_mean_ic": float(max(means)) if means else None,
        "grouping": "calendar_year",
        "minimum_period_dates": int(minimum_period_dates),
        "note": "Descriptive stability only; no confidence label.",
    }
