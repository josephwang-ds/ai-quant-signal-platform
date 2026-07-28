"""Chronological expanding walk-forward splits with label-horizon purging."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class FoldSpec:
    fold_id: str
    raw_train_end_date: str
    effective_purged_train_end_date: str
    validation_start_date: str
    validation_end_date: str
    prediction_start_date: str
    prediction_end_date: str
    label_horizon: int
    purge_rows: int
    train_date_count: int
    validation_date_count: int
    prediction_date_count: int
    rows_removed_by_purging: int


def _sorted_dates(dates: pd.Series) -> list[pd.Timestamp]:
    return sorted(pd.to_datetime(dates.dropna().unique()))


def purged_train_end_index(val_or_pred_start_idx: int, label_horizon: int) -> int:
    """
    Last inclusive train index such that label window ends before start_idx.

    Label at index i uses prices through i + horizon (trading-row semantics).
    Require i + horizon < start_idx ⇒ i_max = start_idx - horizon - 1.
    Returns -1 when no training index remains.
    """
    return int(val_or_pred_start_idx) - int(label_horizon) - 1


def build_expanding_walk_forward_folds(
    unique_dates: list[pd.Timestamp],
    *,
    label_horizon: int,
    min_train_dates: int,
    validation_dates: int,
    prediction_block_dates: int,
) -> list[FoldSpec]:
    """
    Expanding walk-forward:

    train (purged) → validation → prediction block → expand → repeat.

    Dates are never shuffled. An entire calendar date belongs to one role.
    """
    dates = list(unique_dates)
    n = len(dates)
    h = int(label_horizon)
    folds: list[FoldSpec] = []
    # First validation starts after min_train_dates + purge buffer.
    cursor = int(min_train_dates) + h
    fold_no = 0
    while True:
        val_start = cursor
        val_end = val_start + int(validation_dates) - 1
        pred_start = val_end + 1
        pred_end = pred_start + int(prediction_block_dates) - 1
        if pred_end >= n or val_start >= n:
            break
        purge_idx = purged_train_end_index(val_start, h)
        if purge_idx + 1 < int(min_train_dates):
            break
        raw_train_end_idx = val_start - 1
        removed = max(0, raw_train_end_idx - purge_idx)
        fold_no += 1
        folds.append(
            FoldSpec(
                fold_id=f"fold-{fold_no:03d}",
                raw_train_end_date=str(dates[raw_train_end_idx].date()),
                effective_purged_train_end_date=str(dates[purge_idx].date()),
                validation_start_date=str(dates[val_start].date()),
                validation_end_date=str(dates[val_end].date()),
                prediction_start_date=str(dates[pred_start].date()),
                prediction_end_date=str(dates[pred_end].date()),
                label_horizon=h,
                purge_rows=h,
                train_date_count=purge_idx + 1,
                validation_date_count=val_end - val_start + 1,
                prediction_date_count=pred_end - pred_start + 1,
                rows_removed_by_purging=removed,
            )
        )
        # Expand: next validation starts after this prediction block.
        cursor = pred_end + 1
    return folds


def fold_masks(
    dates: pd.Series,
    fold: FoldSpec,
) -> dict[str, pd.Series]:
    """Boolean masks for purged train / validation / prediction date ranges."""
    d = pd.to_datetime(dates)
    train_end = pd.Timestamp(fold.effective_purged_train_end_date)
    val_start = pd.Timestamp(fold.validation_start_date)
    val_end = pd.Timestamp(fold.validation_end_date)
    pred_start = pd.Timestamp(fold.prediction_start_date)
    pred_end = pd.Timestamp(fold.prediction_end_date)
    return {
        "train": d <= train_end,
        "validation": (d >= val_start) & (d <= val_end),
        "prediction": (d >= pred_start) & (d <= pred_end),
    }


def folds_as_dicts(folds: list[FoldSpec]) -> list[dict[str, Any]]:
    return [asdict(f) for f in folds]


def collect_unique_dates(panel: pd.DataFrame) -> list[pd.Timestamp]:
    return _sorted_dates(panel["date"])
