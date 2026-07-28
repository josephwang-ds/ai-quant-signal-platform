"""Out-of-sample prediction evaluation (RankIC, errors, coverage)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.cross_sectional.research.rank_ic import (
    STATUS_AVAILABLE,
    STATUS_UNAVAILABLE,
    _spearman,
    summarize_rank_ic,
)


def evaluate_prediction_frame(
    predictions: pd.DataFrame,
    *,
    minimum_cross_section_size: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Daily prediction RankIC grouped by date (and caller scopes by model).

    Reuses Phase 2 Spearman primitive; does not import the Phase 2 service.
    """
    if predictions.empty:
        empty_summary = {
            **summarize_rank_ic([]),
            "mae": None,
            "rmse": None,
            "prediction_coverage": 0.0,
            "prediction_row_count": 0,
        }
        return [], empty_summary

    work = predictions.copy()
    work["as_of_date"] = pd.to_datetime(work["as_of_date"])
    daily: list[dict[str, Any]] = []
    abs_err: list[float] = []
    sq_err: list[float] = []

    for dt, group in work.groupby("as_of_date", sort=True):
        pred = pd.to_numeric(group["raw_prediction"], errors="coerce")
        actual = pd.to_numeric(group["actual_forward_return"], errors="coerce")
        mask = pred.notna() & actual.notna() & np.isfinite(pred) & np.isfinite(actual)
        eligible = int(mask.sum())
        base = {
            "date": str(pd.Timestamp(dt).date()),
            "factor": "raw_prediction",
            "label": str(group["label"].iloc[0]) if "label" in group.columns else "",
            "horizon": int(group["horizon"].iloc[0]) if "horizon" in group.columns else 0,
            "eligible_count": eligible,
            "excluded_count": int(len(group) - eligible),
            "exclusion_reasons": {},
        }
        if eligible < int(minimum_cross_section_size):
            daily.append(
                {
                    **base,
                    "rank_ic": None,
                    "status": STATUS_UNAVAILABLE,
                    "unavailable_reason": "below_minimum_cross_section",
                }
            )
            continue
        p = pred[mask]
        a = actual[mask]
        for pv, av in zip(p, a):
            abs_err.append(abs(float(pv) - float(av)))
            sq_err.append((float(pv) - float(av)) ** 2)
        if float(p.std(ddof=0)) == 0.0:
            daily.append(
                {
                    **base,
                    "rank_ic": None,
                    "status": STATUS_UNAVAILABLE,
                    "unavailable_reason": "constant_prediction",
                }
            )
            continue
        if float(a.std(ddof=0)) == 0.0:
            daily.append(
                {
                    **base,
                    "rank_ic": None,
                    "status": STATUS_UNAVAILABLE,
                    "unavailable_reason": "constant_label",
                }
            )
            continue
        ic = _spearman(p, a)
        if ic is None:
            daily.append(
                {
                    **base,
                    "rank_ic": None,
                    "status": STATUS_UNAVAILABLE,
                    "unavailable_reason": "degenerate_correlation",
                }
            )
            continue
        daily.append(
            {
                **base,
                "rank_ic": float(ic),
                "status": STATUS_AVAILABLE,
                "unavailable_reason": None,
            }
        )

    summary = summarize_rank_ic(daily)
    mae = float(np.mean(abs_err)) if abs_err else None
    rmse = float(np.sqrt(np.mean(sq_err))) if sq_err else None
    n_dates = len(daily)
    n_avail = sum(1 for r in daily if r.get("status") == STATUS_AVAILABLE)
    summary.update(
        {
            "mae": mae,
            "rmse": rmse,
            "prediction_coverage": float(n_avail / n_dates) if n_dates else 0.0,
            "prediction_row_count": int(len(predictions)),
            "prediction_date_count": n_dates,
        }
    )
    return daily, summary


def score_predictions_for_selection(
    preds: np.ndarray,
    validation: pd.DataFrame,
    *,
    label: str,
    horizon: int,
    minimum_cross_section_size: int,
) -> dict[str, Any]:
    """Build a temporary prediction frame and return selection metrics."""
    frame = pd.DataFrame(
        {
            "as_of_date": pd.to_datetime(validation["date"]).map(
                lambda d: str(pd.Timestamp(d).date())
            ),
            "symbol": validation["symbol"].astype(str).to_numpy(),
            "label": label,
            "horizon": horizon,
            "model_name": "_candidate",
            "raw_prediction": np.asarray(preds, dtype=float),
            "actual_forward_return": pd.to_numeric(
                validation[label], errors="coerce"
            ).to_numpy(dtype=float),
        }
    )
    _daily, summary = evaluate_prediction_frame(
        frame, minimum_cross_section_size=minimum_cross_section_size
    )
    return {
        "mean_rank_ic": summary.get("mean_rank_ic"),
        "median_rank_ic": summary.get("median_rank_ic"),
        "positive_ic_ratio": summary.get("positive_ic_ratio"),
        "mae": summary.get("mae"),
        "rmse": summary.get("rmse"),
        "available_date_count": summary.get("available_date_count"),
        "prediction_coverage": summary.get("prediction_coverage"),
    }
