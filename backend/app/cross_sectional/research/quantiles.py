"""Equal-weight quantile portfolios and top-minus-bottom spreads."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.cross_sectional.research.eligibility import slice_eligible
from app.cross_sectional.research.rank_ic import STATUS_AVAILABLE, STATUS_UNAVAILABLE


def assign_quantiles(
    symbols: list[str],
    factor_values: list[float],
    *,
    quantile_count: int,
) -> dict[str, list[str]]:
    """
    Q1 = lowest factor … Q{n} = highest factor.

    Ties broken by symbol ascending. Remainder names distributed from Q1 upward.
    Each symbol appears in exactly one quantile.
    """
    labels = tuple(f"Q{i}" for i in range(1, quantile_count + 1))
    if len(symbols) < quantile_count:
        return {label: [] for label in labels}

    ordered = sorted(
        zip(symbols, factor_values),
        key=lambda item: (float(item[1]), str(item[0])),
    )
    names = [s for s, _ in ordered]
    n = len(names)
    base = n // quantile_count
    rem = n % quantile_count
    sizes = [base + (1 if i < rem else 0) for i in range(quantile_count)]
    buckets: dict[str, list[str]] = {}
    cursor = 0
    for label, size in zip(labels, sizes):
        buckets[label] = names[cursor : cursor + size]
        cursor += size
    return buckets


def compute_daily_quantiles(
    panel: pd.DataFrame,
    *,
    factor: str,
    label: str,
    horizon: int,
    quantile_count: int,
    minimum_cross_section_size: int,
    minimum_quantile_size: int,
    apply_liquidity_filter: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (quantile rows, spread rows) per date."""
    if panel.empty:
        return [], []
    work = panel.sort_values(["date", "symbol"]).copy()
    work["date"] = pd.to_datetime(work["date"])
    q_rows: list[dict[str, Any]] = []
    spread_rows: list[dict[str, Any]] = []
    labels = tuple(f"Q{i}" for i in range(1, quantile_count + 1))
    top_label = labels[-1]
    bottom_label = labels[0]

    for dt in sorted(work["date"].dropna().unique()):
        eligible, meta = slice_eligible(
            work,
            date_value=dt,
            factor=factor,
            label=label,
            apply_liquidity_filter=apply_liquidity_filter,
        )
        date_str = str(pd.Timestamp(dt).date())
        base = {
            "date": date_str,
            "factor": factor,
            "label": label,
            "horizon": int(horizon),
            "eligible_count": meta["eligible_count"],
        }
        min_needed = max(
            int(minimum_cross_section_size),
            int(quantile_count) * int(minimum_quantile_size),
        )
        if meta["eligible_count"] < min_needed:
            spread_rows.append(
                {
                    **base,
                    "top_quantile_return": None,
                    "bottom_quantile_return": None,
                    "top_minus_bottom": None,
                    "status": STATUS_UNAVAILABLE,
                    "unavailable_reason": "below_minimum_cross_section",
                }
            )
            continue

        symbols = eligible["symbol"].astype(str).tolist()
        factor_vals = pd.to_numeric(eligible[factor], errors="coerce").tolist()
        buckets = assign_quantiles(symbols, factor_vals, quantile_count=quantile_count)
        if any(len(buckets[q]) < int(minimum_quantile_size) for q in labels):
            spread_rows.append(
                {
                    **base,
                    "top_quantile_return": None,
                    "bottom_quantile_return": None,
                    "top_minus_bottom": None,
                    "status": STATUS_UNAVAILABLE,
                    "unavailable_reason": "below_minimum_quantile_size",
                }
            )
            continue

        fwd = eligible.set_index("symbol")[label]
        q_means: dict[str, float] = {}
        ok = True
        for q in labels:
            members = buckets[q]
            vals = pd.to_numeric(fwd.reindex(members), errors="coerce")
            if vals.isna().any() or len(vals) != len(members):
                ok = False
                break
            mean_ret = float(vals.mean())
            q_means[q] = mean_ret
            q_rows.append(
                {
                    "date": date_str,
                    "factor": factor,
                    "label": label,
                    "horizon": int(horizon),
                    "quantile": q,
                    "mean_forward_return": mean_ret,
                    "symbol_count": int(len(members)),
                    "status": STATUS_AVAILABLE,
                }
            )
        if not ok:
            spread_rows.append(
                {
                    **base,
                    "top_quantile_return": None,
                    "bottom_quantile_return": None,
                    "top_minus_bottom": None,
                    "status": STATUS_UNAVAILABLE,
                    "unavailable_reason": "missing_quantile_labels",
                }
            )
            continue

        top = q_means[top_label]
        bottom = q_means[bottom_label]
        spread_rows.append(
            {
                **base,
                "top_quantile_return": top,
                "bottom_quantile_return": bottom,
                "top_minus_bottom": float(top - bottom),
                "status": STATUS_AVAILABLE,
                "unavailable_reason": None,
            }
        )
    return q_rows, spread_rows


def summarize_quantiles(
    q_rows: list[dict[str, Any]],
    spread_rows: list[dict[str, Any]],
    *,
    quantile_count: int,
) -> dict[str, Any]:
    labels = tuple(f"Q{i}" for i in range(1, quantile_count + 1))
    by_q: dict[str, Any] = {}
    for q in labels:
        vals = [
            float(r["mean_forward_return"])
            for r in q_rows
            if r.get("quantile") == q and r.get("status") == STATUS_AVAILABLE
        ]
        by_q[q] = {
            "mean_return": float(np.mean(vals)) if vals else None,
            "median_return": float(np.median(vals)) if vals else None,
            "available_date_count": len(vals),
        }

    spreads = [
        float(r["top_minus_bottom"])
        for r in spread_rows
        if r.get("status") == STATUS_AVAILABLE and r.get("top_minus_bottom") is not None
    ]
    n = len(spreads)
    spread_std = float(np.std(spreads, ddof=1)) if n >= 2 else None
    # Monotonicity: Spearman between quantile number and average quantile return.
    q_nums = []
    q_avgs = []
    for i, q in enumerate(labels, start=1):
        avg = by_q[q]["mean_return"]
        if avg is not None:
            q_nums.append(float(i))
            q_avgs.append(float(avg))
    mono = None
    if len(q_nums) >= 3:
        mono = float(pd.Series(q_nums).corr(pd.Series(q_avgs), method="spearman"))
        if not np.isfinite(mono):
            mono = None

    return {
        "by_quantile": by_q,
        "available_date_count": n,
        "unavailable_date_count": sum(
            1 for r in spread_rows if r.get("status") != STATUS_AVAILABLE
        ),
        "mean_top_minus_bottom": float(np.mean(spreads)) if spreads else None,
        "spread_volatility": spread_std,
        "positive_spread_ratio": float(sum(1 for s in spreads if s > 0) / n) if n else None,
        "monotonicity_spearman": mono,
        "quantile_convention": "Q1=lowest factor … Qn=highest factor; equal-weight forward returns",
    }
