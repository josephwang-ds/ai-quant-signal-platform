"""Out-of-sample and leakage invariant checks for Phase 3 predictions."""

from __future__ import annotations

from typing import Any

import pandas as pd


class LeakageInvariantError(ValueError):
    """Raised when a prediction row violates OOS / leakage invariants."""


def assert_prediction_oos_invariants(
    predictions: pd.DataFrame,
    fold_summaries: list[dict[str, Any]],
) -> None:
    """
    Every prediction row must:

    - have exactly one non-empty fold_id and fit_id
    - fall inside its fold's prediction window
    - have training_cutoff strictly before as_of_date
    - not share a date with the fold's purged training window
    """
    if predictions.empty:
        raise LeakageInvariantError("Prediction frame is empty.")

    folds = {str(f["fold_id"]): f for f in fold_summaries if f.get("fold_id")}
    required = (
        "as_of_date",
        "fold_id",
        "fit_id",
        "training_cutoff",
        "model_name",
    )
    missing_cols = [c for c in required if c not in predictions.columns]
    if missing_cols:
        raise LeakageInvariantError(f"Missing prediction columns: {missing_cols}")

    for idx, row in predictions.iterrows():
        fold_id = str(row["fold_id"] or "").strip()
        fit_id = str(row["fit_id"] or "").strip()
        if not fold_id or not fit_id:
            raise LeakageInvariantError(
                f"Row {idx}: fold_id and fit_id must both be non-empty "
                f"(fold_id={fold_id!r}, fit_id={fit_id!r})."
            )
        fold = folds.get(fold_id)
        if fold is None:
            raise LeakageInvariantError(f"Row {idx}: unknown fold_id {fold_id!r}.")

        as_of = str(row["as_of_date"])
        cutoff = str(row["training_cutoff"])
        pred_start = str(fold["prediction_start_date"])
        pred_end = str(fold["prediction_end_date"])
        purged_end = str(fold.get("effective_purged_train_end_date") or cutoff)

        if not (pred_start <= as_of <= pred_end):
            raise LeakageInvariantError(
                f"Row {idx}: as_of_date {as_of} outside prediction window "
                f"[{pred_start}, {pred_end}] for {fold_id}."
            )
        if not (cutoff < as_of):
            raise LeakageInvariantError(
                f"Row {idx}: training_cutoff {cutoff} is not strictly before "
                f"prediction date {as_of}."
            )
        if as_of <= purged_end:
            raise LeakageInvariantError(
                f"Row {idx}: prediction date {as_of} overlaps purged train "
                f"ending {purged_end}."
            )

    # Each (fold_id, model_name, as_of_date, symbol) maps to exactly one fit_id.
    keys = predictions.assign(
        _k=predictions["fold_id"].astype(str)
        + "|"
        + predictions["model_name"].astype(str)
        + "|"
        + predictions["as_of_date"].astype(str)
        + "|"
        + predictions["symbol"].astype(str)
    )
    grouped = keys.groupby("_k")["fit_id"].nunique()
    bad = grouped[grouped != 1]
    if not bad.empty:
        raise LeakageInvariantError(
            f"Multiple fit_ids for the same prediction key: {list(bad.index)[:5]}"
        )


def assert_purge_boundary(
    *,
    dates: list[pd.Timestamp],
    purged_train_end_date: str,
    boundary_start_date: str,
    label_horizon: int,
) -> None:
    """
    Prove Phase 1 trading-row label windows cannot reach boundary_start.

    Phase 1: forward_return_Nd[t] = P[t+N]/P[t]-1 on the sorted trading calendar.
    Label at index i uses price through index i+N.
    Require i_end + N < boundary_idx.
    """
    indexed = {str(pd.Timestamp(d).date()): i for i, d in enumerate(dates)}
    if purged_train_end_date not in indexed:
        raise LeakageInvariantError(
            f"purged_train_end_date {purged_train_end_date} not in calendar."
        )
    if boundary_start_date not in indexed:
        raise LeakageInvariantError(
            f"boundary_start_date {boundary_start_date} not in calendar."
        )
    i_end = indexed[purged_train_end_date]
    b_start = indexed[boundary_start_date]
    if i_end + int(label_horizon) >= b_start:
        raise LeakageInvariantError(
            f"Label window crosses boundary: train_end_idx={i_end}, "
            f"horizon={label_horizon}, last_label_price_idx={i_end + label_horizon}, "
            f"boundary_idx={b_start}."
        )
