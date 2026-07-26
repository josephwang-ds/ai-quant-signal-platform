"""Versioned methodology config for canonical trend walk-forward evidence.

Thresholds and protocol defaults live here (and in the rulebook document),
not in React. UI may display reported status/checks but must not re-decide
pass/fail against local constants.
"""

from __future__ import annotations

from typing import Any, Literal

WalkForwardScheme = Literal["expanding", "rolling"]

# Stable methodology identity — bump version when protocol or thresholds change.
WALK_FORWARD_METHODOLOGY_ID = "wf.trend_ma_crossover.v1"
WALK_FORWARD_METHODOLOGY_VERSION = "v1"
WALK_FORWARD_KNOWLEDGE_ID = "kb.walk_forward.v1"

WALK_FORWARD_CONFIG: dict[str, Any] = {
    "methodology_id": WALK_FORWARD_METHODOLOGY_ID,
    "methodology_version": WALK_FORWARD_METHODOLOGY_VERSION,
    "knowledge_id": WALK_FORWARD_KNOWLEDGE_ID,
    "protocol": {
        "fixed_parameters": True,
        "short_window": 20,
        "long_window": 60,
        "transaction_cost": 0.001,
        "position_lag_days": 1,
        "shuffle_forbidden": True,
        "per_fold_param_retuning": False,
        "default_scheme": "expanding",
        "supported_schemes": ("expanding", "rolling"),
        "default_n_folds": 4,
        "min_n_folds": 3,
        "max_n_folds": 5,
        # Minimum valid return rows required in each OOS fold.
        "min_oos_rows_per_fold": 60,
        # Minimum train/history rows before the first OOS fold.
        "min_train_rows": 252,
        # Rolling train length equals the initial expanding train length when
        # unset at runtime; this is the floor for that window.
        "min_rolling_train_rows": 252,
        "aggregate_oos_only": True,
    },
    # Deterministic review thresholds consumed by the validation stage checks.
    # React must display backend-reported check outcomes, not re-apply these.
    "thresholds": {
        "min_completed_fold_ratio": 1.0,
        "min_positive_return_fold_ratio": 0.5,
        "min_benchmark_outperformance_fold_ratio": 0.5,
        "min_median_oos_sharpe": 0.0,
    },
    "limitations": (
        "Walk-forward reduces but does not eliminate overfitting risk.",
        "Walk-forward evidence is historical only and does not represent future returns.",
        "This protocol uses fixed MA20/MA60 parameters; it is not per-fold parameter tuning.",
        "Compare Models walk-forward is a separate ML evaluation path and is not "
        "substituted for this canonical trend robustness evidence.",
    ),
}


def walk_forward_config_snapshot() -> dict[str, Any]:
    """JSON-serializable copy of the versioned methodology config."""
    protocol = dict(WALK_FORWARD_CONFIG["protocol"])
    protocol["supported_schemes"] = list(protocol["supported_schemes"])
    return {
        "methodology_id": WALK_FORWARD_CONFIG["methodology_id"],
        "methodology_version": WALK_FORWARD_CONFIG["methodology_version"],
        "knowledge_id": WALK_FORWARD_CONFIG["knowledge_id"],
        "protocol": protocol,
        "thresholds": dict(WALK_FORWARD_CONFIG["thresholds"]),
        "limitations": list(WALK_FORWARD_CONFIG["limitations"]),
    }
