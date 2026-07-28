"""Daily cross-sectional Spearman RankIC for long factor panels."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.cross_sectional.research.eligibility import slice_eligible

STATUS_AVAILABLE = "available"
STATUS_UNAVAILABLE = "unavailable"


def _spearman(x: pd.Series, y: pd.Series) -> float | None:
    """Spearman via average ranks + Pearson; None if degenerate."""
    aligned = pd.concat([x, y], axis=1, join="inner").dropna()
    if len(aligned) < 2:
        return None
    rx = aligned.iloc[:, 0].rank(method="average")
    ry = aligned.iloc[:, 1].rank(method="average")
    if float(rx.std(ddof=0)) == 0.0 or float(ry.std(ddof=0)) == 0.0:
        return None
    corr = float(rx.corr(ry, method="pearson"))
    if not np.isfinite(corr):
        return None
    return corr


def compute_daily_rank_ic(
    panel: pd.DataFrame,
    *,
    factor: str,
    label: str,
    horizon: int,
    minimum_cross_section_size: int,
    apply_liquidity_filter: bool,
) -> list[dict[str, Any]]:
    """
    Cross-sectional RankIC per date for one factor × label.

    Does not pool dates before correlation. Missing → unavailable (not zero).
    """
    if panel.empty:
        return []
    work = panel.sort_values(["date", "symbol"]).copy()
    work["date"] = pd.to_datetime(work["date"])
    dates = sorted(work["date"].dropna().unique())
    rows: list[dict[str, Any]] = []

    for dt in dates:
        eligible, meta = slice_eligible(
            work,
            date_value=dt,
            factor=factor,
            label=label,
            apply_liquidity_filter=apply_liquidity_filter,
        )
        base = {
            "date": str(pd.Timestamp(dt).date()),
            "factor": factor,
            "label": label,
            "horizon": int(horizon),
            "eligible_count": meta["eligible_count"],
            "excluded_count": meta["excluded_count"],
            "exclusion_reasons": meta["exclusion_reasons"],
        }
        if meta["eligible_count"] < int(minimum_cross_section_size):
            rows.append(
                {
                    **base,
                    "rank_ic": None,
                    "status": STATUS_UNAVAILABLE,
                    "unavailable_reason": "below_minimum_cross_section",
                }
            )
            continue
        factor_vals = pd.to_numeric(eligible[factor], errors="coerce")
        label_vals = pd.to_numeric(eligible[label], errors="coerce")
        if float(factor_vals.std(ddof=0)) == 0.0:
            rows.append(
                {
                    **base,
                    "rank_ic": None,
                    "status": STATUS_UNAVAILABLE,
                    "unavailable_reason": "constant_factor",
                }
            )
            continue
        if float(label_vals.std(ddof=0)) == 0.0:
            rows.append(
                {
                    **base,
                    "rank_ic": None,
                    "status": STATUS_UNAVAILABLE,
                    "unavailable_reason": "constant_label",
                }
            )
            continue
        ic = _spearman(factor_vals, label_vals)
        if ic is None:
            rows.append(
                {
                    **base,
                    "rank_ic": None,
                    "status": STATUS_UNAVAILABLE,
                    "unavailable_reason": "degenerate_correlation",
                }
            )
            continue
        rows.append(
            {
                **base,
                "rank_ic": float(ic),
                "status": STATUS_AVAILABLE,
                "unavailable_reason": None,
            }
        )
    return rows


def summarize_rank_ic(daily: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Aggregate daily RankIC.

    ICIR convention: mean(RankIC) / std(RankIC, ddof=1). Not annualized.
    When std is 0 or unavailable, ICIR is null.
    """
    available = [r for r in daily if r.get("status") == STATUS_AVAILABLE]
    unavailable = [r for r in daily if r.get("status") != STATUS_AVAILABLE]
    values = [float(r["rank_ic"]) for r in available if r.get("rank_ic") is not None]
    n = len(values)
    if n == 0:
        return {
            "observation_count": 0,
            "available_date_count": 0,
            "unavailable_date_count": len(unavailable),
            "mean_rank_ic": None,
            "median_rank_ic": None,
            "rank_ic_std": None,
            "icir": None,
            "positive_ic_ratio": None,
            "negative_ic_ratio": None,
            "min_ic": None,
            "max_ic": None,
            "icir_convention": "mean_rank_ic / std(rank_ic, ddof=1); not annualized",
        }

    arr = np.asarray(values, dtype=float)
    mean_ic = float(arr.mean())
    median_ic = float(np.median(arr))
    std = float(arr.std(ddof=1)) if n >= 2 else float("nan")
    icir = None
    if n >= 2 and np.isfinite(std) and std != 0.0:
        icir = float(mean_ic / std)
    return {
        "observation_count": n,
        "available_date_count": n,
        "unavailable_date_count": len(unavailable),
        "mean_rank_ic": mean_ic,
        "median_rank_ic": median_ic,
        "rank_ic_std": float(std) if np.isfinite(std) else None,
        "icir": icir,
        "positive_ic_ratio": float((arr > 0).sum() / n),
        "negative_ic_ratio": float((arr < 0).sum() / n),
        "min_ic": float(arr.min()),
        "max_ic": float(arr.max()),
        "icir_convention": "mean_rank_ic / std(rank_ic, ddof=1); not annualized",
    }
