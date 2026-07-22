"""Chronological ML vs rule-strategy comparison on a shared OOS window.

Does not reimplement return/drawdown math — only orchestrates features,
estimators, ``apply_position_and_returns``, and existing metric helpers.
"""

from __future__ import annotations

from typing import Any, Optional, Sequence

import math

import pandas as pd
from sklearn.metrics import accuracy_score

from app.backtest.compare import _build_summary
from app.backtest.engine import (
    apply_position_and_returns,
    run_combined_signal_backtest,
    run_ma_crossover_backtest,
    run_momentum_backtest,
)
from app.backtest.metrics import calculate_backtest_metrics, calculate_buy_and_hold_metrics
from app.backtest.oos import _rebase_segment_for_metrics
from app.models.features import FEATURE_COLUMNS, build_feature_frame
from app.models.model_registry import build_model, feature_importance, get_model_constructors

MIN_SPLIT_ROWS = 60

MODEL_LABELS: dict[str, str] = {
    "logistic": "Logistic Regression",
    "random_forest": "Random Forest",
    "xgboost": "XGBoost",
    "lightgbm": "LightGBM",
}

MODEL_COMPARISON_INTERPRETATION = [
    "ML models are not guaranteed to beat simple rules on this out-of-sample window.",
    "Compare strategies only on the shared out-of-sample interval after the split date.",
    "Directional accuracy measures next-day up/down hit rate — it is not a return promise.",
    "Review costs and turnover together with return and drawdown; frequent signals can erode edge.",
]


def _normalize_split_ts(split_date: str) -> pd.Timestamp:
    return pd.to_datetime(split_date)


def _ensure_datetime_dates(aligned: pd.DataFrame) -> pd.Series:
    return pd.to_datetime(aligned["date"])


def _predict_signal(model: Any, X_test: pd.DataFrame) -> pd.Series:
    """Binary next-day-up signal (1 = predicted up). Prefer proba when available."""
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X_test)
        if getattr(proba, "ndim", 1) == 2 and proba.shape[1] >= 2:
            signal = (proba[:, 1] >= 0.5).astype(int)
        else:
            signal = (proba.ravel() >= 0.5).astype(int)
    else:
        signal = model.predict(X_test).astype(int)
    return pd.Series(signal, index=X_test.index, name="model_signal")


def _slice_to_test_window(
    backtest_df: pd.DataFrame,
    *,
    test_start: pd.Timestamp,
    test_end: pd.Timestamp,
) -> pd.DataFrame:
    dates = pd.to_datetime(backtest_df["date"])
    return backtest_df.loc[(dates >= test_start) & (dates <= test_end)].copy()


def _metrics_for_test_segment(segment_df: pd.DataFrame) -> dict[str, Any]:
    if segment_df.empty:
        raise ValueError(
            "Test window is empty after aligning rule-strategy results to the ML evaluation range."
        )
    rebased = _rebase_segment_for_metrics(segment_df)
    return calculate_backtest_metrics(rebased)


def _buy_and_hold_metrics_for_test_segment(segment_df: pd.DataFrame) -> dict[str, Any]:
    if segment_df.empty:
        raise ValueError(
            "Test window is empty after aligning buy-and-hold to the ML evaluation range."
        )
    rebased = _rebase_segment_for_metrics(segment_df)
    return calculate_buy_and_hold_metrics(rebased)


def _resolve_model_names(models: Optional[Sequence[str]]) -> list[str]:
    available = get_model_constructors()
    if models is None:
        return list(available.keys())
    names = list(models)
    unknown = [name for name in names if name not in available]
    if unknown:
        raise ValueError(
            "Unknown model(s): "
            + ", ".join(unknown)
            + f". Allowed: {', '.join(sorted(available))}."
        )
    return names


def _normalized_equity_series(
    segment_df: pd.DataFrame,
    *,
    value_col: str = "cumulative_strategy",
) -> pd.Series:
    """
    OOS equity curve rebased to 1.0 at the first shared bar.

    Uses existing engine/oos cumulative columns — does not recompute returns.
    """
    if segment_df.empty or value_col not in segment_df.columns:
        return pd.Series(dtype=float)

    rebased = _rebase_segment_for_metrics(segment_df)
    dates = pd.to_datetime(rebased["date"]).dt.strftime("%Y-%m-%d")
    values = pd.to_numeric(rebased[value_col], errors="coerce")
    series = pd.Series(values.to_numpy(), index=dates, dtype=float)
    series = series[~series.index.duplicated(keep="last")].dropna()
    if series.empty:
        return series
    start = float(series.iloc[0])
    if start == 0 or not math.isfinite(start):
        return series
    return series / start


def _build_equity_curve_rows(
    equity_by_label: dict[str, pd.Series],
    labels: Sequence[str],
) -> list[dict[str, Any]]:
    """Align equity curves on the intersection of OOS trading days."""
    if not labels:
        return []

    common_dates: set[str] | None = None
    for label in labels:
        series = equity_by_label.get(label)
        if series is None or series.empty:
            return []
        dates = set(series.index.astype(str))
        common_dates = dates if common_dates is None else (common_dates & dates)

    if not common_dates:
        return []

    ordered_dates = sorted(common_dates)
    rows: list[dict[str, Any]] = []
    for date in ordered_dates:
        row: dict[str, Any] = {"date": date}
        for label in labels:
            row[label] = float(equity_by_label[label].loc[date])
        rows.append(row)
    return rows


def run_model_comparison(
    price_df: pd.DataFrame,
    *,
    split_date: str,
    transaction_cost: float,
    short_window: int,
    long_window: int,
    momentum_window: int,
    models: Optional[Sequence[str]] = None,
) -> dict[str, Any]:
    """
    Fit ML models on a chronological train split and compare OOS metrics
    against rule strategies on the same test window.
    """
    X, y, aligned = build_feature_frame(price_df)
    if aligned.empty:
        raise ValueError("Not enough data to build a feature frame for model comparison.")

    split_ts = _normalize_split_ts(split_date)
    dates = _ensure_datetime_dates(aligned)
    train_mask = dates < split_ts
    test_mask = dates >= split_ts

    n_train = int(train_mask.sum())
    n_test = int(test_mask.sum())
    if n_train < MIN_SPLIT_ROWS or n_test < MIN_SPLIT_ROWS:
        raise ValueError(
            f"Train/test split is too small after feature alignment "
            f"(train={n_train}, test={n_test}; need at least {MIN_SPLIT_ROWS} rows each). "
            "Adjust split_date so both sides have enough history."
        )

    # Embargo: drop the last training row whose label uses the first test-day close.
    train_index = aligned.index[train_mask]
    train_index = train_index[:-1]
    test_index = aligned.index[test_mask]

    if len(train_index) == 0:
        raise ValueError(
            "Training set is empty after embargo. Adjust split_date."
        )

    X_train = X.loc[train_index]
    y_train = y.loc[train_index]
    X_test = X.loc[test_index]
    y_test = y.loc[test_index]

    test_aligned = aligned.loc[test_index]
    test_start = pd.to_datetime(test_aligned["date"].iloc[0])
    test_end = pd.to_datetime(test_aligned["date"].iloc[-1])

    test_start_str = test_start.strftime("%Y-%m-%d")
    test_end_str = test_end.strftime("%Y-%m-%d")

    results: list[dict[str, Any]] = []
    equity_by_label: dict[str, pd.Series] = {}
    equity_curve_labels: list[str] = []

    def _stamp_window(row: dict[str, Any]) -> dict[str, Any]:
        row["test_start"] = test_start_str
        row["test_end"] = test_end_str
        return row

    def _register_equity(label: str, segment_df: pd.DataFrame, *, value_col: str) -> None:
        equity_by_label[label] = _normalized_equity_series(
            segment_df, value_col=value_col
        )
        equity_curve_labels.append(label)

    for model_name in _resolve_model_names(models):
        model = build_model(model_name)
        model.fit(X_train, y_train)
        signal_test = _predict_signal(model, X_test)

        model_df = aligned.loc[test_index, ["date", "close", "daily_return"]].copy()
        model_df["model_signal"] = signal_test.reindex(model_df.index).astype(int)

        backtest_df = apply_position_and_returns(
            model_df,
            signal_col="model_signal",
            transaction_cost=transaction_cost,
            buy_reason="Model predicts next-day up",
            sell_reason="Model predicts next-day down",
        )
        metrics = calculate_backtest_metrics(backtest_df)
        directional_accuracy = float(accuracy_score(y_test, signal_test))
        label = MODEL_LABELS.get(model_name, model_name)
        _register_equity(label, backtest_df, value_col="cumulative_strategy")

        results.append(
            _stamp_window(
                {
                    "label": label,
                    "kind": "ml",
                    "strategy": model_name,
                    "metrics": metrics,
                    "directional_accuracy": directional_accuracy,
                    "directional_accuracy_note": (
                        "directional accuracy — next-day up/down hit rate, not a return promise"
                    ),
                    "feature_importance": feature_importance(model, FEATURE_COLUMNS),
                }
            )
        )

    # Rule baselines on the same OOS date window (full-history warm-up, then slice).
    ma_full = run_ma_crossover_backtest(
        price_df,
        short_window=short_window,
        long_window=long_window,
        transaction_cost=transaction_cost,
    )
    ma_test = _slice_to_test_window(ma_full, test_start=test_start, test_end=test_end)
    ma_label = f"MA Crossover {short_window}/{long_window}"
    _register_equity(ma_label, ma_test, value_col="cumulative_strategy")
    results.append(
        _stamp_window(
            {
                "label": ma_label,
                "kind": "rule",
                "strategy": "ma_crossover",
                "metrics": _metrics_for_test_segment(ma_test),
            }
        )
    )

    momentum_full = run_momentum_backtest(
        price_df,
        momentum_window=momentum_window,
        transaction_cost=transaction_cost,
    )
    momentum_test = _slice_to_test_window(
        momentum_full, test_start=test_start, test_end=test_end
    )
    momentum_label = f"Momentum {momentum_window}"
    _register_equity(momentum_label, momentum_test, value_col="cumulative_strategy")
    results.append(
        _stamp_window(
            {
                "label": momentum_label,
                "kind": "rule",
                "strategy": "momentum",
                "metrics": _metrics_for_test_segment(momentum_test),
            }
        )
    )

    combined_full = run_combined_signal_backtest(
        price_df,
        short_window=short_window,
        long_window=long_window,
        momentum_window=momentum_window,
        combined_mode="conservative",
        transaction_cost=transaction_cost,
    )
    combined_test = _slice_to_test_window(
        combined_full, test_start=test_start, test_end=test_end
    )
    combined_label = "Combined Conservative"
    _register_equity(combined_label, combined_test, value_col="cumulative_strategy")
    results.append(
        _stamp_window(
            {
                "label": combined_label,
                "kind": "rule",
                "strategy": "combined_signal",
                "metrics": _metrics_for_test_segment(combined_test),
            }
        )
    )

    buy_hold_label = "Buy & Hold"
    # Benchmark equity from the same OOS slice (rebased cumulative_benchmark).
    _register_equity(buy_hold_label, ma_test, value_col="cumulative_benchmark")
    results.append(
        _stamp_window(
            {
                "label": buy_hold_label,
                "kind": "rule",
                "strategy": "buy_and_hold",
                "metrics": _buy_and_hold_metrics_for_test_segment(ma_test),
            }
        )
    )

    equity_curve_rows = _build_equity_curve_rows(equity_by_label, equity_curve_labels)

    return {
        "split_date": split_ts.strftime("%Y-%m-%d"),
        "n_train": int(len(train_index)),
        "n_test": int(len(test_index)),
        "test_start": test_start_str,
        "test_end": test_end_str,
        "results": results,
        "summary": _build_summary(results),
        "interpretation": list(MODEL_COMPARISON_INTERPRETATION),
        "equity_curve_labels": list(equity_curve_labels),
        "equity_curve_rows": equity_curve_rows,
    }
