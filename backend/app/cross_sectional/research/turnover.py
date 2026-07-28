"""Cross-sectional factor-rank turnover between adjacent research dates."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.cross_sectional.research.eligibility import eligible_mask
from app.cross_sectional.research.rank_ic import STATUS_AVAILABLE, STATUS_UNAVAILABLE


def _factor_ranks(day: pd.DataFrame, factor: str) -> pd.Series:
    vals = pd.to_numeric(day[factor], errors="coerce")
    # rank ascending; ties average — same convention as RankIC ranks
    return vals.rank(method="average")


def compute_factor_turnover(
    panel: pd.DataFrame,
    *,
    factor: str,
    label: str,
    apply_liquidity_filter: bool,
    minimum_overlap: int,
) -> list[dict[str, Any]]:
    """
    Adjacent-date turnover = 1 - Spearman(rank_t, rank_{t-1}) on overlapping symbols.

    Bounds: when correlation is defined on [-1, 1], turnover is on [0, 2].
    Insufficient overlap → unavailable (not zero).
    """
    if panel.empty:
        return []
    work = panel.sort_values(["date", "symbol"]).copy()
    work["date"] = pd.to_datetime(work["date"])
    dates = sorted(work["date"].dropna().unique())
    rows: list[dict[str, Any]] = []

    prev_date = None
    prev_ranks: pd.Series | None = None

    for dt in dates:
        day = work.loc[work["date"] == dt]
        mask, _ = eligible_mask(
            day,
            factor=factor,
            label=label,
            apply_liquidity_filter=apply_liquidity_filter,
        )
        # For turnover we need finite factor ranks; label still required for
        # research-date eligibility consistency with RankIC dates.
        eligible = day.loc[mask].set_index("symbol")
        ranks = _factor_ranks(eligible, factor) if not eligible.empty else pd.Series(dtype=float)

        if prev_date is None or prev_ranks is None:
            prev_date = dt
            prev_ranks = ranks
            continue

        overlap = sorted(set(prev_ranks.index) & set(ranks.index))
        date_str = str(pd.Timestamp(dt).date())
        prev_str = str(pd.Timestamp(prev_date).date())
        if len(overlap) < int(minimum_overlap):
            rows.append(
                {
                    "date": date_str,
                    "previous_date": prev_str,
                    "factor": factor,
                    "label": label,
                    "overlap_count": len(overlap),
                    "rank_correlation": None,
                    "turnover": None,
                    "status": STATUS_UNAVAILABLE,
                    "unavailable_reason": "insufficient_overlap",
                }
            )
            prev_date = dt
            prev_ranks = ranks
            continue

        left = prev_ranks.reindex(overlap)
        right = ranks.reindex(overlap)
        if float(left.std(ddof=0)) == 0.0 or float(right.std(ddof=0)) == 0.0:
            rows.append(
                {
                    "date": date_str,
                    "previous_date": prev_str,
                    "factor": factor,
                    "label": label,
                    "overlap_count": len(overlap),
                    "rank_correlation": None,
                    "turnover": None,
                    "status": STATUS_UNAVAILABLE,
                    "unavailable_reason": "constant_ranks",
                }
            )
            prev_date = dt
            prev_ranks = ranks
            continue

        corr = float(left.corr(right, method="pearson"))
        if not np.isfinite(corr):
            rows.append(
                {
                    "date": date_str,
                    "previous_date": prev_str,
                    "factor": factor,
                    "label": label,
                    "overlap_count": len(overlap),
                    "rank_correlation": None,
                    "turnover": None,
                    "status": STATUS_UNAVAILABLE,
                    "unavailable_reason": "degenerate_correlation",
                }
            )
        else:
            rows.append(
                {
                    "date": date_str,
                    "previous_date": prev_str,
                    "factor": factor,
                    "label": label,
                    "overlap_count": len(overlap),
                    "rank_correlation": corr,
                    "turnover": float(1.0 - corr),
                    "status": STATUS_AVAILABLE,
                    "unavailable_reason": None,
                }
            )
        prev_date = dt
        prev_ranks = ranks
    return rows


def summarize_turnover(daily: list[dict[str, Any]]) -> dict[str, Any]:
    available = [r for r in daily if r.get("status") == STATUS_AVAILABLE]
    unavailable = [r for r in daily if r.get("status") != STATUS_AVAILABLE]
    turns = [float(r["turnover"]) for r in available if r.get("turnover") is not None]
    persist = [
        float(r["rank_correlation"])
        for r in available
        if r.get("rank_correlation") is not None
    ]
    return {
        "mean_rank_persistence": float(np.mean(persist)) if persist else None,
        "mean_turnover": float(np.mean(turns)) if turns else None,
        "median_turnover": float(np.median(turns)) if turns else None,
        "available_comparisons": len(available),
        "insufficient_overlap_comparisons": sum(
            1
            for r in unavailable
            if r.get("unavailable_reason") == "insufficient_overlap"
        ),
        "formula": "turnover = 1 - Spearman(factor_rank_t, factor_rank_t-1) on overlap; range [0, 2]",
        "note": "High turnover is descriptive only; no cost interpretation in Phase 2.",
    }
