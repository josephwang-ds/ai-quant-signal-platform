"""Chronological expanding/rolling walk-forward for fixed-parameter MA crossover.

Pure calculation module: no market-data I/O, no param retuning, no shuffle.
Consumes an already-computed full-history MA backtest frame and slices OOS
folds chronologically (same boundary convention as single-split OOS).
"""

from __future__ import annotations

import hashlib
import json
import math
from statistics import median
from typing import Any

import pandas as pd

from app.research_execution.calculations import (
    metrics_to_dict,
    summarize_return_segment,
)
from app.research_validation.walk_forward_config import (
    WALK_FORWARD_CONFIG,
    walk_forward_config_snapshot,
)


def _split_oos_sizes(n_oos: int, n_folds: int) -> list[int]:
    if n_folds < 1:
        raise ValueError("n_folds must be >= 1")
    if n_oos < n_folds:
        raise ValueError(
            f"Not enough OOS rows ({n_oos}) to form {n_folds} folds."
        )
    base = n_oos // n_folds
    rem = n_oos % n_folds
    return [base + (1 if i < rem else 0) for i in range(n_folds)]


def _date_text(value: Any) -> str:
    return pd.Timestamp(value).date().isoformat()


def _finite_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _protocol_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_walk_forward_fold_specs(
    valid_frame: pd.DataFrame,
    *,
    n_folds: int,
    scheme: str,
    min_train_rows: int,
    min_oos_rows_per_fold: int,
    long_window: int,
    rolling_train_rows: int | None = None,
) -> dict[str, Any]:
    """Build chronological fold date bounds over valid return rows."""
    if scheme not in {"expanding", "rolling"}:
        return {
            "status": "unavailable",
            "reason_code": "invalid_scheme",
            "reason": f'scheme must be "expanding" or "rolling"; got {scheme!r}.',
            "folds": [],
        }
    if n_folds < 1:
        return {
            "status": "unavailable",
            "reason_code": "invalid_n_folds",
            "reason": "n_folds must be >= 1.",
            "folds": [],
        }

    n = len(valid_frame)
    min_needed = min_train_rows + n_folds * min_oos_rows_per_fold
    if n < min_needed:
        return {
            "status": "unavailable",
            "reason_code": "insufficient_data",
            "reason": (
                f"Insufficient valid return rows for walk-forward: need at least "
                f"{min_needed} ({min_train_rows} train + {n_folds}×"
                f"{min_oos_rows_per_fold} OOS); got {n}."
            ),
            "folds": [],
            "observation_count": n,
            "minimum_required_rows": min_needed,
        }

    oos_start_pos = min_train_rows
    fold_sizes = _split_oos_sizes(n - oos_start_pos, n_folds)
    if any(size < min_oos_rows_per_fold for size in fold_sizes):
        return {
            "status": "unavailable",
            "reason_code": "insufficient_data",
            "reason": (
                f"Insufficient OOS rows to give every fold at least "
                f"{min_oos_rows_per_fold} observations after chronological split."
            ),
            "folds": [],
            "observation_count": n,
            "fold_sizes": fold_sizes,
        }

    rolling_len = (
        rolling_train_rows if rolling_train_rows is not None else oos_start_pos
    )
    rolling_len = max(rolling_len, min_train_rows)

    dates = pd.to_datetime(valid_frame["date"])
    # Structural MA warm-up precedes the first valid return row in the full run.
    first_valid = dates.iloc[0]
    warmup_start_estimate = (
        first_valid - pd.tseries.offsets.BDay(long_window)
    ).date().isoformat()

    specs: list[dict[str, Any]] = []
    pos = oos_start_pos
    for index, size in enumerate(fold_sizes):
        oos_end_pos = pos + size  # exclusive
        if scheme == "expanding":
            train_start_pos = 0
            train_end_pos = pos  # exclusive; last train row is pos-1
        else:
            train_start_pos = max(0, pos - rolling_len)
            train_end_pos = pos

        train_start = _date_text(dates.iloc[train_start_pos])
        train_end = _date_text(dates.iloc[train_end_pos - 1])
        oos_start = _date_text(dates.iloc[pos])
        oos_end = _date_text(dates.iloc[oos_end_pos - 1])
        # Warm-up for the fold: long_window lookback ending at train_start.
        warmup_end = train_start
        warmup_start = (
            warmup_start_estimate
            if train_start_pos == 0
            else _date_text(
                dates.iloc[train_start_pos]
                - pd.tseries.offsets.BDay(long_window)
            )
        )

        specs.append(
            {
                "fold_index": index,
                "warmup_start": warmup_start,
                "warmup_end": warmup_end,
                "train_start": train_start,
                "train_end": train_end,
                "oos_start": oos_start,
                "oos_end": oos_end,
                "oos_start_pos": pos,
                "oos_end_pos": oos_end_pos,
                "train_start_pos": train_start_pos,
                "train_end_pos": train_end_pos,
                "oos_observation_count": size,
                "train_observation_count": train_end_pos - train_start_pos,
            }
        )
        pos = oos_end_pos

    return {
        "status": "ok",
        "reason_code": None,
        "reason": None,
        "folds": specs,
        "observation_count": n,
        "oos_start_pos": oos_start_pos,
        "rolling_train_rows": rolling_len,
        "fold_sizes": fold_sizes,
    }


def _evaluate_fold(
    valid_frame: pd.DataFrame,
    spec: dict[str, Any],
    *,
    risk_free_rate: float,
    fixed_parameters: dict[str, Any],
) -> dict[str, Any]:
    start = int(spec["oos_start_pos"])
    end = int(spec["oos_end_pos"])
    oos_frame = valid_frame.iloc[start:end]
    record: dict[str, Any] = {
        "fold_index": spec["fold_index"],
        "status": "completed",
        "failure_reason": None,
        "warmup_start": spec["warmup_start"],
        "warmup_end": spec["warmup_end"],
        "train_start": spec["train_start"],
        "train_end": spec["train_end"],
        "oos_start": spec["oos_start"],
        "oos_end": spec["oos_end"],
        "strategy_return": None,
        "benchmark_return": None,
        "sharpe_ratio": None,
        "maximum_drawdown": None,
        "trade_count": None,
        "observation_count": len(oos_frame),
        "fixed_parameters": dict(fixed_parameters),
    }
    if oos_frame.empty:
        record["status"] = "failed"
        record["failure_reason"] = "OOS segment is empty."
        return record
    try:
        segment = summarize_return_segment(
            oos_frame, risk_free_rate=risk_free_rate
        )
    except (ValueError, ArithmeticError) as exc:
        record["status"] = "failed"
        record["failure_reason"] = f"OOS metric calculation failed: {exc}"
        return record

    strategy = metrics_to_dict(segment.strategy_metrics)
    benchmark = metrics_to_dict(segment.benchmark_metrics)
    record["strategy_return"] = strategy.get("total_return")
    record["benchmark_return"] = benchmark.get("total_return")
    record["sharpe_ratio"] = strategy.get("sharpe_ratio")
    record["maximum_drawdown"] = strategy.get("maximum_drawdown")
    record["trade_count"] = strategy.get("trade_count")
    record["strategy_metrics"] = strategy
    record["benchmark_metrics"] = benchmark
    return record


def _aggregate_folds(
    folds: list[dict[str, Any]],
    *,
    thresholds: dict[str, Any],
) -> dict[str, Any]:
    completed = [fold for fold in folds if fold.get("status") == "completed"]
    failed = [fold for fold in folds if fold.get("status") == "failed"]
    completed_count = len(completed)
    total = len(folds)
    completed_ratio = (completed_count / total) if total else 0.0

    returns = [
        _finite_or_none(fold.get("strategy_return")) for fold in completed
    ]
    returns = [value for value in returns if value is not None]
    sharpes = [
        _finite_or_none(fold.get("sharpe_ratio")) for fold in completed
    ]
    sharpes = [value for value in sharpes if value is not None]
    drawdowns = [
        _finite_or_none(fold.get("maximum_drawdown")) for fold in completed
    ]
    drawdowns = [value for value in drawdowns if value is not None]

    positive_count = sum(1 for value in returns if value > 0)
    outperform_count = 0
    for fold in completed:
        strategy_ret = _finite_or_none(fold.get("strategy_return"))
        benchmark_ret = _finite_or_none(fold.get("benchmark_return"))
        if (
            strategy_ret is not None
            and benchmark_ret is not None
            and strategy_ret > benchmark_ret
        ):
            outperform_count += 1

    positive_ratio = (
        positive_count / completed_count if completed_count else None
    )
    outperform_ratio = (
        outperform_count / completed_count if completed_count else None
    )
    median_return = median(returns) if returns else None
    median_sharpe = median(sharpes) if sharpes else None
    # Drawdowns are negative or zero; worst = minimum (most negative).
    worst_drawdown = min(drawdowns) if drawdowns else None

    checks = [
        {
            "check_id": "completed_fold_ratio",
            "observed_value": completed_ratio,
            "configured_threshold": thresholds["min_completed_fold_ratio"],
            "status": (
                "passed"
                if completed_ratio >= float(thresholds["min_completed_fold_ratio"])
                else "failed"
            ),
        },
        {
            "check_id": "positive_return_fold_ratio",
            "observed_value": positive_ratio,
            "configured_threshold": thresholds[
                "min_positive_return_fold_ratio"
            ],
            "status": (
                "unavailable"
                if positive_ratio is None
                else "passed"
                if positive_ratio
                >= float(thresholds["min_positive_return_fold_ratio"])
                else "failed"
            ),
        },
        {
            "check_id": "benchmark_outperformance_fold_ratio",
            "observed_value": outperform_ratio,
            "configured_threshold": thresholds[
                "min_benchmark_outperformance_fold_ratio"
            ],
            "status": (
                "unavailable"
                if outperform_ratio is None
                else "passed"
                if outperform_ratio
                >= float(thresholds["min_benchmark_outperformance_fold_ratio"])
                else "failed"
            ),
        },
        {
            "check_id": "median_oos_sharpe",
            "observed_value": median_sharpe,
            "configured_threshold": thresholds["min_median_oos_sharpe"],
            "status": (
                "unavailable"
                if median_sharpe is None
                else "passed"
                if median_sharpe >= float(thresholds["min_median_oos_sharpe"])
                else "failed"
            ),
        },
    ]

    return {
        "completed_fold_count": completed_count,
        "failed_fold_count": len(failed),
        "requested_fold_count": total,
        "positive_return_fold_ratio": positive_ratio,
        "benchmark_outperformance_fold_ratio": outperform_ratio,
        "median_oos_return": median_return,
        "median_oos_sharpe": median_sharpe,
        "worst_oos_drawdown": worst_drawdown,
        "checks": checks,
        "failed_fold_indexes": [fold["fold_index"] for fold in failed],
        "failed_fold_reasons": [
            {
                "fold_index": fold["fold_index"],
                "failure_reason": fold.get("failure_reason"),
            }
            for fold in failed
        ],
    }


def run_rolling_walk_forward(
    valid_frame: pd.DataFrame,
    *,
    short_window: int,
    long_window: int,
    transaction_cost: float,
    risk_free_rate: float = 0.0,
    n_folds: int | None = None,
    scheme: str | None = None,
    min_train_rows: int | None = None,
    min_oos_rows_per_fold: int | None = None,
    rolling_train_rows: int | None = None,
) -> dict[str, Any]:
    """
    Run fixed-parameter chronological walk-forward over valid MA return rows.

    Parameters are fixed for every fold. Failed folds remain in the payload.
    Insufficient history returns status ``unavailable`` with reason_code
    ``insufficient_data``.
    """
    config = walk_forward_config_snapshot()
    protocol = config["protocol"]
    thresholds = config["thresholds"]

    resolved_scheme = scheme or protocol["default_scheme"]
    resolved_folds = (
        int(n_folds) if n_folds is not None else int(protocol["default_n_folds"])
    )
    min_folds = int(protocol["min_n_folds"])
    max_folds = int(protocol["max_n_folds"])
    resolved_min_train = (
        int(min_train_rows)
        if min_train_rows is not None
        else int(protocol["min_train_rows"])
    )
    resolved_min_oos = (
        int(min_oos_rows_per_fold)
        if min_oos_rows_per_fold is not None
        else int(protocol["min_oos_rows_per_fold"])
    )

    fixed_parameters = {
        "short_window": short_window,
        "long_window": long_window,
        "transaction_cost": transaction_cost,
        "risk_free_rate": risk_free_rate,
        "fixed_parameters": True,
        "per_fold_param_retuning": False,
    }

    base_payload: dict[str, Any] = {
        "type": "rolling_walk_forward",
        "methodology_id": config["methodology_id"],
        "methodology_version": config["methodology_version"],
        "knowledge_id": config["knowledge_id"],
        "scheme": resolved_scheme,
        "n_folds": resolved_folds,
        "fixed_parameters": fixed_parameters,
        "thresholds": thresholds,
        "limitations": list(config["limitations"]),
        "folds": [],
        "aggregate": None,
        "status": "unavailable",
        "reason_code": None,
        "reason": None,
        "provenance": {
            "methodology_id": config["methodology_id"],
            "methodology_version": config["methodology_version"],
            "knowledge_id": config["knowledge_id"],
            "protocol_hash": None,
            "config": {
                "scheme": resolved_scheme,
                "n_folds": resolved_folds,
                "min_train_rows": resolved_min_train,
                "min_oos_rows_per_fold": resolved_min_oos,
                "fixed_parameters": fixed_parameters,
            },
        },
    }

    if not (min_folds <= resolved_folds <= max_folds):
        base_payload["reason_code"] = "invalid_n_folds"
        base_payload["reason"] = (
            f"n_folds must be between {min_folds} and {max_folds} inclusive; "
            f"got {resolved_folds}."
        )
        return base_payload

    if valid_frame is None or valid_frame.empty:
        base_payload["reason_code"] = "insufficient_data"
        base_payload["reason"] = (
            "No valid return rows available after MA warm-up and position lag."
        )
        return base_payload

    required = {
        "date",
        "position",
        "daily_return",
        "net_strategy_return",
        "turnover",
        "transaction_cost",
    }
    missing = sorted(required.difference(valid_frame.columns))
    if missing:
        base_payload["reason_code"] = "invalid_frame"
        base_payload["reason"] = (
            f"Walk-forward frame missing columns: {missing}."
        )
        return base_payload

    dates = pd.to_datetime(valid_frame["date"])
    if not dates.is_monotonic_increasing:
        base_payload["status"] = "failed"
        base_payload["reason_code"] = "non_monotonic_dates"
        base_payload["reason"] = (
            "Walk-forward requires strictly increasing dates; shuffle is forbidden."
        )
        return base_payload
    if dates.duplicated().any():
        base_payload["status"] = "failed"
        base_payload["reason_code"] = "duplicate_dates"
        base_payload["reason"] = "Walk-forward requires unique chronological dates."
        return base_payload

    spec_result = build_walk_forward_fold_specs(
        valid_frame,
        n_folds=resolved_folds,
        scheme=resolved_scheme,
        min_train_rows=resolved_min_train,
        min_oos_rows_per_fold=resolved_min_oos,
        long_window=long_window,
        rolling_train_rows=rolling_train_rows
        if rolling_train_rows is not None
        else int(protocol["min_rolling_train_rows"]),
    )
    if spec_result["status"] != "ok":
        base_payload["status"] = "unavailable"
        base_payload["reason_code"] = spec_result.get("reason_code")
        base_payload["reason"] = spec_result.get("reason")
        base_payload["observation_count"] = spec_result.get("observation_count")
        base_payload["minimum_required_rows"] = spec_result.get(
            "minimum_required_rows"
        )
        return base_payload

    folds = [
        _evaluate_fold(
            valid_frame,
            spec,
            risk_free_rate=risk_free_rate,
            fixed_parameters=fixed_parameters,
        )
        for spec in spec_result["folds"]
    ]

    # Guard: OOS windows must not overlap and must be strictly increasing.
    overlap_errors: list[str] = []
    previous_end: pd.Timestamp | None = None
    for fold in folds:
        start = pd.Timestamp(fold["oos_start"])
        end = pd.Timestamp(fold["oos_end"])
        if start > end:
            overlap_errors.append(
                f"fold {fold['fold_index']}: oos_start after oos_end"
            )
        if previous_end is not None and start <= previous_end:
            overlap_errors.append(
                f"fold {fold['fold_index']}: OOS window overlaps prior fold"
            )
        previous_end = end
        # Train must end before OOS starts.
        if pd.Timestamp(fold["train_end"]) >= start:
            fold["status"] = "failed"
            fold["failure_reason"] = (
                fold.get("failure_reason")
                or "Train window overlaps OOS window."
            )

    aggregate = _aggregate_folds(folds, thresholds=thresholds)
    failed_count = aggregate["failed_fold_count"]
    if overlap_errors:
        status = "failed"
        reason_code = "fold_date_overlap"
        reason = "; ".join(overlap_errors)
    elif failed_count > 0:
        status = "failed"
        reason_code = "fold_failure"
        reason = (
            f"{failed_count} of {len(folds)} walk-forward folds failed; "
            "failed folds are retained in evidence."
        )
    else:
        status = "completed"
        reason_code = None
        reason = None

    public_folds = []
    for fold in folds:
        public_folds.append(
            {
                key: fold.get(key)
                for key in (
                    "fold_index",
                    "status",
                    "failure_reason",
                    "warmup_start",
                    "warmup_end",
                    "train_start",
                    "train_end",
                    "oos_start",
                    "oos_end",
                    "strategy_return",
                    "benchmark_return",
                    "sharpe_ratio",
                    "maximum_drawdown",
                    "trade_count",
                    "observation_count",
                    "fixed_parameters",
                )
            }
        )

    hash_payload = {
        "methodology_id": config["methodology_id"],
        "methodology_version": config["methodology_version"],
        "scheme": resolved_scheme,
        "n_folds": resolved_folds,
        "fixed_parameters": fixed_parameters,
        "fold_bounds": [
            {
                "fold_index": fold["fold_index"],
                "train_start": fold["train_start"],
                "train_end": fold["train_end"],
                "oos_start": fold["oos_start"],
                "oos_end": fold["oos_end"],
                "status": fold["status"],
            }
            for fold in public_folds
        ],
        "aggregate": {
            "completed_fold_count": aggregate["completed_fold_count"],
            "median_oos_return": aggregate["median_oos_return"],
            "median_oos_sharpe": aggregate["median_oos_sharpe"],
            "worst_oos_drawdown": aggregate["worst_oos_drawdown"],
        },
    }
    protocol_hash = _protocol_hash(hash_payload)

    base_payload.update(
        {
            "status": status,
            "reason_code": reason_code,
            "reason": reason,
            "folds": public_folds,
            "aggregate": {
                "completed_fold_count": aggregate["completed_fold_count"],
                "failed_fold_count": aggregate["failed_fold_count"],
                "requested_fold_count": aggregate["requested_fold_count"],
                "positive_return_fold_ratio": aggregate[
                    "positive_return_fold_ratio"
                ],
                "benchmark_outperformance_fold_ratio": aggregate[
                    "benchmark_outperformance_fold_ratio"
                ],
                "median_oos_return": aggregate["median_oos_return"],
                "median_oos_sharpe": aggregate["median_oos_sharpe"],
                "worst_oos_drawdown": aggregate["worst_oos_drawdown"],
            },
            "checks": aggregate["checks"],
            "failed_fold_reasons": aggregate["failed_fold_reasons"],
            "observation_count": spec_result.get("observation_count"),
            "rolling_train_rows": spec_result.get("rolling_train_rows"),
            "provenance": {
                **base_payload["provenance"],
                "protocol_hash": protocol_hash,
                "config": {
                    **base_payload["provenance"]["config"],
                    "rolling_train_rows": spec_result.get("rolling_train_rows"),
                    "min_train_rows": resolved_min_train,
                    "min_oos_rows_per_fold": resolved_min_oos,
                },
            },
        }
    )
    return base_payload


# Re-export for callers that want the frozen defaults without importing config.
DEFAULT_WALK_FORWARD_N_FOLDS = int(
    WALK_FORWARD_CONFIG["protocol"]["default_n_folds"]
)
DEFAULT_WALK_FORWARD_SCHEME = str(
    WALK_FORWARD_CONFIG["protocol"]["default_scheme"]
)
