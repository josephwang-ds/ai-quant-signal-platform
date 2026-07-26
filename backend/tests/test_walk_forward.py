"""Deterministic synthetic-series tests for canonical trend walk-forward."""

from __future__ import annotations

from statistics import median

import numpy as np
import pandas as pd
import pytest

from app.research_execution.calculations import run_ma_crossover_research
from app.research_validation.walk_forward import (
    build_walk_forward_fold_specs,
    run_rolling_walk_forward,
)
from app.research_validation.walk_forward_config import (
    WALK_FORWARD_METHODOLOGY_ID,
    WALK_FORWARD_METHODOLOGY_VERSION,
)


def _synthetic_prices(n: int, *, seed: int = 7, start: str = "2015-01-02") -> pd.DataFrame:
    """Deterministic OHLC path — no live provider."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(start=start, periods=n)
    # Mild upward drift with controlled noise so MA crossover is well-defined.
    shocks = rng.normal(loc=0.0004, scale=0.008, size=n)
    close = 100.0 * np.cumprod(1.0 + shocks)
    frame = pd.DataFrame(
        {
            "date": dates,
            "open": close * (1.0 - 0.001),
            "high": close * (1.0 + 0.002),
            "low": close * (1.0 - 0.002),
            "close": close,
            "adjusted_close": close,
            "volume": np.full(n, 1_000_000),
        }
    )
    return frame


def _valid_frame(n: int = 900) -> pd.DataFrame:
    prices = _synthetic_prices(n)
    result = run_ma_crossover_research(
        prices,
        short_window=20,
        long_window=60,
        transaction_cost=0.001,
    )
    return result.frame


def test_insufficient_data_returns_unavailable() -> None:
    frame = _valid_frame(n=200)
    out = run_rolling_walk_forward(
        frame,
        short_window=20,
        long_window=60,
        transaction_cost=0.001,
        n_folds=4,
        scheme="expanding",
    )
    assert out["status"] == "unavailable"
    assert out["reason_code"] == "insufficient_data"
    assert out["folds"] == []
    assert out["aggregate"] is None


def test_fold_dates_have_no_oos_overlap_and_time_strictly_increasing() -> None:
    frame = _valid_frame(n=900)
    out = run_rolling_walk_forward(
        frame,
        short_window=20,
        long_window=60,
        transaction_cost=0.001,
        n_folds=4,
        scheme="expanding",
    )
    assert out["status"] == "completed"
    folds = out["folds"]
    assert len(folds) == 4

    previous_oos_end = None
    previous_oos_start = None
    for fold in folds:
        assert fold["status"] == "completed"
        train_start = pd.Timestamp(fold["train_start"])
        train_end = pd.Timestamp(fold["train_end"])
        oos_start = pd.Timestamp(fold["oos_start"])
        oos_end = pd.Timestamp(fold["oos_end"])
        assert train_start <= train_end
        assert oos_start <= oos_end
        assert train_end < oos_start
        if previous_oos_end is not None:
            assert oos_start > previous_oos_end
        if previous_oos_start is not None:
            assert oos_start > previous_oos_start
        previous_oos_end = oos_end
        previous_oos_start = oos_start


def test_fixed_parameters_are_identical_across_folds() -> None:
    frame = _valid_frame(n=900)
    out = run_rolling_walk_forward(
        frame,
        short_window=20,
        long_window=60,
        transaction_cost=0.001,
        n_folds=3,
        scheme="rolling",
    )
    assert out["status"] == "completed"
    assert out["fixed_parameters"]["short_window"] == 20
    assert out["fixed_parameters"]["long_window"] == 60
    assert out["fixed_parameters"]["transaction_cost"] == 0.001
    assert out["fixed_parameters"]["per_fold_param_retuning"] is False
    for fold in out["folds"]:
        assert fold["fixed_parameters"]["short_window"] == 20
        assert fold["fixed_parameters"]["long_window"] == 60
        assert fold["fixed_parameters"]["transaction_cost"] == 0.001


def test_aggregation_matches_completed_fold_metrics() -> None:
    frame = _valid_frame(n=900)
    out = run_rolling_walk_forward(
        frame,
        short_window=20,
        long_window=60,
        transaction_cost=0.001,
        n_folds=4,
        scheme="expanding",
    )
    folds = out["folds"]
    aggregate = out["aggregate"]
    assert aggregate is not None
    assert aggregate["completed_fold_count"] == 4
    assert aggregate["failed_fold_count"] == 0
    assert aggregate["requested_fold_count"] == 4

    returns = [fold["strategy_return"] for fold in folds]
    sharpes = [fold["sharpe_ratio"] for fold in folds]
    drawdowns = [fold["maximum_drawdown"] for fold in folds]
    assert aggregate["median_oos_return"] == pytest.approx(median(returns))
    assert aggregate["median_oos_sharpe"] == pytest.approx(median(sharpes))
    assert aggregate["worst_oos_drawdown"] == pytest.approx(min(drawdowns))

    positive_ratio = sum(1 for value in returns if value > 0) / len(returns)
    outperform_ratio = sum(
        1
        for fold in folds
        if fold["strategy_return"] > fold["benchmark_return"]
    ) / len(folds)
    assert aggregate["positive_return_fold_ratio"] == pytest.approx(positive_ratio)
    assert aggregate["benchmark_outperformance_fold_ratio"] == pytest.approx(
        outperform_ratio
    )


def test_one_fold_failure_marks_overall_failed_and_retains_fold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = _valid_frame(n=900)
    specs = build_walk_forward_fold_specs(
        frame,
        n_folds=3,
        scheme="expanding",
        min_train_rows=252,
        min_oos_rows_per_fold=60,
        long_window=60,
    )
    assert specs["status"] == "ok"
    failing_start = pd.Timestamp(specs["folds"][1]["oos_start"]).date().isoformat()

    import app.research_validation.walk_forward as walk_forward_mod
    from app.research_execution.calculations import summarize_return_segment as real_summarize

    def _flaky_summarize(segment_frame, *, risk_free_rate=0.0):
        start = pd.Timestamp(segment_frame["date"].iloc[0]).date().isoformat()
        if start == failing_start:
            raise ValueError("synthetic fold calculation failure")
        return real_summarize(segment_frame, risk_free_rate=risk_free_rate)

    monkeypatch.setattr(walk_forward_mod, "summarize_return_segment", _flaky_summarize)

    out = run_rolling_walk_forward(
        frame,
        short_window=20,
        long_window=60,
        transaction_cost=0.001,
        n_folds=3,
        scheme="expanding",
    )
    assert out["status"] == "failed"
    assert out["reason_code"] == "fold_failure"
    assert len(out["folds"]) == 3
    failed = [fold for fold in out["folds"] if fold["status"] == "failed"]
    assert len(failed) == 1
    assert failed[0]["fold_index"] == 1
    assert failed[0]["failure_reason"]
    assert out["aggregate"]["failed_fold_count"] == 1
    assert out["aggregate"]["completed_fold_count"] == 2
    assert out["failed_fold_reasons"]


def test_provenance_and_protocol_hash_present() -> None:
    frame = _valid_frame(n=900)
    out = run_rolling_walk_forward(
        frame,
        short_window=20,
        long_window=60,
        transaction_cost=0.001,
        n_folds=4,
        scheme="expanding",
    )
    assert out["methodology_id"] == WALK_FORWARD_METHODOLOGY_ID
    assert out["methodology_version"] == WALK_FORWARD_METHODOLOGY_VERSION
    provenance = out["provenance"]
    assert provenance["protocol_hash"]
    assert len(provenance["protocol_hash"]) == 64
    assert provenance["methodology_id"] == WALK_FORWARD_METHODOLOGY_ID
    assert "thresholds" in out
    assert "min_positive_return_fold_ratio" in out["thresholds"]


def test_non_monotonic_dates_fail_closed() -> None:
    frame = _valid_frame(n=900)
    shuffled = frame.sample(frac=1.0, random_state=1).reset_index(drop=True)
    out = run_rolling_walk_forward(
        shuffled,
        short_window=20,
        long_window=60,
        transaction_cost=0.001,
        n_folds=4,
        scheme="expanding",
    )
    assert out["status"] == "failed"
    assert out["reason_code"] == "non_monotonic_dates"


def test_rolling_scheme_builds_bounded_train_windows() -> None:
    frame = _valid_frame(n=900)
    out = run_rolling_walk_forward(
        frame,
        short_window=20,
        long_window=60,
        transaction_cost=0.001,
        n_folds=3,
        scheme="rolling",
    )
    assert out["status"] == "completed"
    assert out["scheme"] == "rolling"
    train_lengths = []
    for fold in out["folds"]:
        train_start = pd.Timestamp(fold["train_start"])
        train_end = pd.Timestamp(fold["train_end"])
        mask = (pd.to_datetime(frame["date"]) >= train_start) & (
            pd.to_datetime(frame["date"]) <= train_end
        )
        train_lengths.append(int(mask.sum()))
    # Rolling windows should stay near the configured train length.
    assert max(train_lengths) - min(train_lengths) <= 1
