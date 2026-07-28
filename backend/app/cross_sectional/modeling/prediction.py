"""Daily cross-sectional score / percentile / rank contract."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def add_cross_sectional_scores(
    predictions: pd.DataFrame,
    *,
    prediction_col: str = "raw_prediction",
) -> pd.DataFrame:
    """
    Within each (as_of_date, model_name):

    - percentile_score: average-rank scaled to [0, 1] (lowest → 0, highest → 1)
    - rank: 1 = highest predicted score (descending). Differs from Phase 2 Q1=low.
    - score: equals raw_prediction in Phase 3 v1 (separate field for future calibration).

    Dates are never pooled. Models are never pooled.
    """
    if predictions.empty:
        out = predictions.copy()
        for col in ("score", "percentile_score", "rank", "eligible_symbol_count"):
            if col not in out.columns:
                out[col] = pd.Series(dtype=float)
        return out

    frame = predictions.copy()
    frame["score"] = pd.to_numeric(frame[prediction_col], errors="coerce")
    parts: list[pd.DataFrame] = []
    for (_date, _model), group in frame.groupby(["as_of_date", "model_name"], sort=True):
        g = group.copy()
        vals = pd.to_numeric(g["score"], errors="coerce")
        n = int(vals.notna().sum())
        g["eligible_symbol_count"] = n
        avg_rank = vals.rank(method="average", ascending=True)
        if n <= 1 or float(vals.std(ddof=0) or 0.0) == 0.0:
            g["percentile_score"] = 0.5 if n >= 1 else np.nan
        else:
            g["percentile_score"] = (avg_rank - 1.0) / (n - 1.0)
        # Rank 1 = highest prediction (min method for ties sharing best rank).
        g["rank"] = vals.rank(method="min", ascending=False)
        parts.append(g)
    return (
        pd.concat(parts, axis=0)
        .sort_values(["as_of_date", "model_name", "rank", "symbol"])
        .reset_index(drop=True)
    )


def predictions_to_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        rows.append(
            {
                "as_of_date": str(row["as_of_date"]),
                "symbol": str(row["symbol"]),
                "label": str(row["label"]),
                "horizon": int(row["horizon"]),
                "model_name": str(row["model_name"]),
                "model_version": str(row.get("model_version") or ""),
                "fit_id": str(row["fit_id"]),
                "fold_id": str(row["fold_id"]),
                "training_cutoff": str(row["training_cutoff"]),
                "raw_prediction": _f(row["raw_prediction"]),
                "score": _f(row["score"]),
                "percentile_score": _f(row["percentile_score"]),
                "rank": int(row["rank"]) if pd.notna(row["rank"]) else None,
                "eligible_symbol_count": int(row["eligible_symbol_count"]),
                "actual_forward_return": _f(row["actual_forward_return"]),
                "prediction_status": str(row.get("prediction_status") or "available"),
            }
        )
    return rows


def _f(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if np.isfinite(out) else None
