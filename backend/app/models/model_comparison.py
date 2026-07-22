"""Chronological ML vs rule-strategy comparison on a shared OOS window.

Does not reimplement return/drawdown math — only orchestrates features,
estimators, ``apply_position_and_returns``, and existing metric helpers.
"""

from __future__ import annotations

import json
from pathlib import Path
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

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"

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

WALK_FORWARD_INTERPRETATION_EXTRA = (
    "Walk-forward multi-fold OOS is more informative about robustness than a single split date."
)

LSTM_OFFLINE_INTERPRETATION = (
    "LSTM is offline-trained and loaded from a committed artifact — not trained at request time."
)


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


def _lstm_artifact_path(ticker: str) -> Path:
    safe = ticker.upper().strip()
    return ARTIFACTS_DIR / f"lstm_{safe}.json"


def _load_lstm_artifact(ticker: str) -> Optional[dict[str, Any]]:
    """Read offline LSTM JSON only — never imports torch."""
    path = _lstm_artifact_path(ticker)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _normalize_date_str(value: Any) -> Optional[str]:
    if value is None or value == "":
        return None
    try:
        return pd.to_datetime(value).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return str(value).strip() or None


def _lstm_artifact_is_compatible(
    artifact: dict[str, Any],
    *,
    ticker: str,
    start_date: str,
    split_date: Optional[str],
    oos_start: Optional[str],
    oos_end: Optional[str],
) -> bool:
    """
    Compatible when ticker + start_date match, and either:
    - single-split: artifact.split_date == request split_date, or
    - walk-forward: artifact OOS window equals payload oos_start/oos_end.
    """
    art_ticker = str(artifact.get("ticker") or "").upper().strip()
    if art_ticker != ticker.upper().strip():
        return False

    art_start = _normalize_date_str(artifact.get("start_date"))
    req_start = _normalize_date_str(start_date)
    if art_start and req_start and art_start != req_start:
        return False

    art_split = _normalize_date_str(artifact.get("split_date"))
    req_split = _normalize_date_str(split_date)
    if req_split:
        return bool(art_split and art_split == req_split)

    art_oos_start = _normalize_date_str(
        artifact.get("test_start") or artifact.get("oos_start")
    )
    art_oos_end = _normalize_date_str(
        artifact.get("test_end") or artifact.get("oos_end")
    )
    req_oos_start = _normalize_date_str(oos_start)
    req_oos_end = _normalize_date_str(oos_end)
    if not (art_oos_start and art_oos_end and req_oos_start and req_oos_end):
        return False
    return art_oos_start == req_oos_start and art_oos_end == req_oos_end


def _artifact_equity_series(artifact: dict[str, Any], label: str) -> Optional[pd.Series]:
    curve = artifact.get("equity_curve")
    if not isinstance(curve, list) or not curve:
        return None
    dates: list[str] = []
    values: list[float] = []
    for item in curve:
        if not isinstance(item, dict) or label not in item:
            continue
        date = _normalize_date_str(item.get("date"))
        if not date:
            continue
        try:
            values.append(float(item[label]))
        except (TypeError, ValueError):
            continue
        dates.append(date)
    if not dates:
        return None
    series = pd.Series(values, index=dates, dtype=float)
    return series[~series.index.duplicated(keep="last")].dropna()


def attach_lstm_offline_artifact(
    payload: dict[str, Any],
    *,
    ticker: str,
    start_date: str,
    include_lstm: bool = True,
) -> dict[str, Any]:
    """
    Optionally append an offline LSTM row from a committed JSON artifact.

    Skips silently when missing or incompatible. Never imports torch.
    """
    if not include_lstm:
        return payload

    artifact = _load_lstm_artifact(ticker)
    if artifact is None:
        return payload

    split_date = payload.get("split_date")
    oos_start = payload.get("oos_start") or payload.get("test_start")
    oos_end = payload.get("oos_end") or payload.get("test_end")
    if not _lstm_artifact_is_compatible(
        artifact,
        ticker=ticker,
        start_date=start_date,
        split_date=split_date if isinstance(split_date, str) else None,
        oos_start=oos_start if isinstance(oos_start, str) else None,
        oos_end=oos_end if isinstance(oos_end, str) else None,
    ):
        return payload

    label = str(artifact.get("label") or "LSTM")
    metrics = artifact.get("metrics")
    if not isinstance(metrics, dict):
        return payload

    results = list(payload.get("results") or [])
    if any(row.get("strategy") == "lstm" for row in results):
        return payload

    row: dict[str, Any] = {
        "label": label,
        "kind": "ml",
        "strategy": "lstm",
        "metrics": metrics,
        "directional_accuracy": artifact.get("directional_accuracy"),
        "directional_accuracy_note": artifact.get(
            "directional_accuracy_note",
            "directional accuracy — next-day up/down hit rate, not a return promise",
        ),
        "source": "offline_artifact",
        "trained_at": artifact.get("trained_at"),
        "test_start": payload.get("test_start"),
        "test_end": payload.get("test_end"),
    }

    insert_at = next(
        (i for i, item in enumerate(results) if item.get("kind") == "rule"),
        len(results),
    )
    results.insert(insert_at, row)
    payload["results"] = results
    payload["summary"] = _build_summary(results)

    interpretation = list(payload.get("interpretation") or [])
    if LSTM_OFFLINE_INTERPRETATION not in interpretation:
        interpretation.append(LSTM_OFFLINE_INTERPRETATION)
    payload["interpretation"] = interpretation

    # Merge equity onto the intersection of existing OOS dates when possible.
    labels = list(payload.get("equity_curve_labels") or [])
    rows = list(payload.get("equity_curve_rows") or [])
    art_series = _artifact_equity_series(artifact, label)
    if art_series is not None and rows and label not in labels:
        merged_rows: list[dict[str, Any]] = []
        for item in rows:
            date = str(item.get("date") or "")
            if date not in art_series.index:
                continue
            merged = dict(item)
            merged[label] = float(art_series.loc[date])
            merged_rows.append(merged)
        if merged_rows:
            payload["equity_curve_labels"] = labels + [label]
            payload["equity_curve_rows"] = merged_rows

    return payload


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


def _split_oos_positions(n_oos: int, n_folds: int) -> list[int]:
    """Return per-fold lengths that sum to ``n_oos`` (earlier folds get the remainder)."""
    if n_folds < 2:
        raise ValueError("n_folds must be >= 2")
    if n_oos < n_folds:
        raise ValueError(
            f"Not enough out-of-sample rows ({n_oos}) to form {n_folds} folds."
        )
    base = n_oos // n_folds
    rem = n_oos % n_folds
    return [base + (1 if i < rem else 0) for i in range(n_folds)]


def _build_walk_forward_fold_specs(
    aligned: pd.DataFrame,
    *,
    n_folds: int,
    scheme: str,
) -> list[dict[str, Any]]:
    """
    Build chronological fold specs over the OOS region after an initial train prefix.

    Expanding: train = series start .. day before fold test (then embargo).
    Rolling: fixed-length train window ending at the day before fold test (then embargo).
    """
    if scheme not in {"expanding", "rolling"}:
        raise ValueError('scheme must be "expanding" or "rolling"')

    n = len(aligned)
    # Prefix so fold-0 train still has MIN_SPLIT_ROWS after dropping the embargo row.
    min_prefix = MIN_SPLIT_ROWS + 1
    if n <= min_prefix + n_folds:
        raise ValueError(
            f"Not enough aligned rows for walk-forward "
            f"(n={n}; need more than {min_prefix + n_folds} for {n_folds} folds)."
        )

    oos_start_pos = min_prefix
    fold_sizes = _split_oos_positions(n - oos_start_pos, n_folds)
    # Rolling window length matches the initial expanding train length (pre-embargo).
    rolling_train_len = oos_start_pos

    index = aligned.index.to_numpy()
    dates = _ensure_datetime_dates(aligned)
    specs: list[dict[str, Any]] = []
    pos = oos_start_pos
    for k, size in enumerate(fold_sizes):
        test_start_pos = pos
        test_end_pos = pos + size  # exclusive
        test_positions = list(range(test_start_pos, test_end_pos))

        if scheme == "expanding":
            raw_train_positions = list(range(0, test_start_pos))
        else:
            train_start_pos = max(0, test_start_pos - rolling_train_len)
            raw_train_positions = list(range(train_start_pos, test_start_pos))

        # Embargo: drop the last training row whose label uses the first test-day close.
        train_positions = raw_train_positions[:-1] if raw_train_positions else []

        train_index = index[train_positions] if train_positions else index[:0]
        test_index = index[test_positions]

        skipped = False
        skip_reason: str | None = None
        if len(train_index) < MIN_SPLIT_ROWS or len(test_index) < MIN_SPLIT_ROWS:
            skipped = True
            skip_reason = (
                f"train={len(train_index)}, test={len(test_index)} "
                f"(need >= {MIN_SPLIT_ROWS} each)"
            )

        if len(raw_train_positions) == 0:
            train_start_str = None
            train_end_str = None
        else:
            train_start_str = pd.to_datetime(dates.iloc[raw_train_positions[0]]).strftime(
                "%Y-%m-%d"
            )
            # Report train_end as last *usable* train day after embargo when possible.
            end_pos = (
                train_positions[-1]
                if train_positions
                else raw_train_positions[-1]
            )
            train_end_str = pd.to_datetime(dates.iloc[end_pos]).strftime("%Y-%m-%d")

        test_start_str = pd.to_datetime(dates.iloc[test_positions[0]]).strftime("%Y-%m-%d")
        test_end_str = pd.to_datetime(dates.iloc[test_positions[-1]]).strftime("%Y-%m-%d")

        specs.append(
            {
                "index": k,
                "train_index": train_index,
                "test_index": test_index,
                "train_start": train_start_str,
                "train_end": train_end_str,
                "test_start": test_start_str,
                "test_end": test_end_str,
                "skipped": skipped,
                "skip_reason": skip_reason,
            }
        )
        pos = test_end_pos

    return specs


def run_walk_forward_comparison(
    price_df: pd.DataFrame,
    *,
    n_folds: int = 4,
    transaction_cost: float,
    short_window: int,
    long_window: int,
    momentum_window: int,
    models: Optional[Sequence[str]] = None,
    scheme: str = "expanding",
) -> dict[str, Any]:
    """
    Multi-fold chronological walk-forward OOS comparison (expanding or rolling).

    Does not replace ``run_model_comparison`` — aggregates per-fold OOS signals into
    one continuous evaluation window per model, then scores rule baselines on the
    same concatenated OOS interval.
    """
    if n_folds < 2:
        raise ValueError("n_folds must be >= 2")
    if scheme not in {"expanding", "rolling"}:
        raise ValueError('scheme must be "expanding" or "rolling"')

    X, y, aligned = build_feature_frame(price_df)
    if aligned.empty:
        raise ValueError("Not enough data to build a feature frame for model comparison.")

    fold_specs = _build_walk_forward_fold_specs(
        aligned, n_folds=n_folds, scheme=scheme
    )
    active_specs = [spec for spec in fold_specs if not spec["skipped"]]
    if not active_specs:
        reasons = "; ".join(
            f"fold {spec['index']}: {spec['skip_reason']}" for spec in fold_specs
        )
        raise ValueError(
            "No walk-forward folds had enough train/test rows after embargo. " + reasons
        )

    model_names = _resolve_model_names(models)
    # Per model: chronological OOS signal + labels across active folds.
    oos_signals: dict[str, list[pd.Series]] = {name: [] for name in model_names}
    oos_labels: dict[str, list[pd.Series]] = {name: [] for name in model_names}
    importance_accum: dict[str, list[dict[str, float]]] = {
        name: [] for name in model_names
    }

    folds_out: list[dict[str, Any]] = []

    for spec in fold_specs:
        fold_record: dict[str, Any] = {
            "index": spec["index"],
            "train_start": spec["train_start"],
            "train_end": spec["train_end"],
            "test_start": spec["test_start"],
            "test_end": spec["test_end"],
            "per_model": [],
        }
        if spec["skipped"]:
            fold_record["skipped"] = True
            fold_record["skip_reason"] = spec["skip_reason"]
            folds_out.append(fold_record)
            continue

        train_index = spec["train_index"]
        test_index = spec["test_index"]
        X_train = X.loc[train_index]
        y_train = y.loc[train_index]
        X_test = X.loc[test_index]
        y_test = y.loc[test_index]

        for model_name in model_names:
            model = build_model(model_name)
            model.fit(X_train, y_train)
            signal_test = _predict_signal(model, X_test)
            oos_signals[model_name].append(signal_test)
            oos_labels[model_name].append(y_test)
            importance_accum[model_name].append(
                feature_importance(model, FEATURE_COLUMNS)
            )

            fold_df = aligned.loc[test_index, ["date", "close", "daily_return"]].copy()
            fold_df["model_signal"] = signal_test.reindex(fold_df.index).astype(int)
            fold_bt = apply_position_and_returns(
                fold_df,
                signal_col="model_signal",
                transaction_cost=transaction_cost,
                buy_reason="Model predicts next-day up",
                sell_reason="Model predicts next-day down",
            )
            fold_metrics = _metrics_for_test_segment(fold_bt)
            fold_record["per_model"].append(
                {
                    "label": MODEL_LABELS.get(model_name, model_name),
                    "strategy": model_name,
                    "directional_accuracy": float(accuracy_score(y_test, signal_test)),
                    "sharpe_ratio": fold_metrics.get("sharpe_ratio"),
                }
            )

        folds_out.append(fold_record)

    # Concatenated OOS index in chronological order (union of active fold tests).
    oos_index = pd.Index(
        [idx for spec in active_specs for idx in spec["test_index"]]
    )

    oos_aligned = aligned.loc[oos_index]
    oos_start = pd.to_datetime(oos_aligned["date"].iloc[0])
    oos_end = pd.to_datetime(oos_aligned["date"].iloc[-1])
    oos_start_str = oos_start.strftime("%Y-%m-%d")
    oos_end_str = oos_end.strftime("%Y-%m-%d")

    results: list[dict[str, Any]] = []
    equity_by_label: dict[str, pd.Series] = {}
    equity_curve_labels: list[str] = []

    def _stamp_window(row: dict[str, Any]) -> dict[str, Any]:
        row["test_start"] = oos_start_str
        row["test_end"] = oos_end_str
        return row

    def _register_equity(label: str, segment_df: pd.DataFrame, *, value_col: str) -> None:
        equity_by_label[label] = _normalized_equity_series(
            segment_df, value_col=value_col
        )
        equity_curve_labels.append(label)

    def _avg_importance(parts: list[dict[str, float]]) -> dict[str, float]:
        if not parts:
            return {}
        keys = parts[0].keys()
        return {
            key: float(sum(part.get(key, 0.0) for part in parts) / len(parts))
            for key in keys
        }

    for model_name in model_names:
        signal_oos = pd.concat(oos_signals[model_name], axis=0)
        y_oos = pd.concat(oos_labels[model_name], axis=0)
        model_df = aligned.loc[oos_index, ["date", "close", "daily_return"]].copy()
        model_df["model_signal"] = signal_oos.reindex(model_df.index).astype(int)

        backtest_df = apply_position_and_returns(
            model_df,
            signal_col="model_signal",
            transaction_cost=transaction_cost,
            buy_reason="Model predicts next-day up",
            sell_reason="Model predicts next-day down",
        )
        metrics = _metrics_for_test_segment(backtest_df)
        directional_accuracy = float(accuracy_score(y_oos, signal_oos))
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
                    "feature_importance": _avg_importance(importance_accum[model_name]),
                }
            )
        )

    # Rule baselines on the same concatenated OOS interval.
    ma_full = run_ma_crossover_backtest(
        price_df,
        short_window=short_window,
        long_window=long_window,
        transaction_cost=transaction_cost,
    )
    ma_test = _slice_to_test_window(ma_full, test_start=oos_start, test_end=oos_end)
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
        momentum_full, test_start=oos_start, test_end=oos_end
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
        combined_full, test_start=oos_start, test_end=oos_end
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
    interpretation = list(MODEL_COMPARISON_INTERPRETATION) + [
        WALK_FORWARD_INTERPRETATION_EXTRA
    ]

    return {
        "mode": "walk_forward",
        "n_folds": len(active_specs),
        "scheme": scheme,
        "folds": folds_out,
        "oos_start": oos_start_str,
        "oos_end": oos_end_str,
        "test_start": oos_start_str,
        "test_end": oos_end_str,
        "n_test": int(len(oos_index)),
        "results": results,
        "summary": _build_summary(results),
        "interpretation": interpretation,
        "equity_curve_labels": list(equity_curve_labels),
        "equity_curve_rows": equity_curve_rows,
    }
