"""Golden tests for portfolio risk/stability statistics."""

from __future__ import annotations

import numpy as np
import pytest

from app.factor_validation.portfolio_stats import max_drawdown, sharpe_ratio


def _points(values: list[float]) -> list[dict[str, object]]:
    return [{"date": f"2020-{i + 1:02d}", "value": v} for i, v in enumerate(values)]


def test_sharpe_ratio_known_series():
    values = [0.02, -0.01, 0.03, 0.00, 0.015, -0.02]
    result = sharpe_ratio(_points(values))
    arr = np.array(values)
    expected = (arr.mean() / arr.std(ddof=1)) * np.sqrt(12)
    assert result == pytest.approx(expected)


def test_sharpe_ratio_insufficient_observations_is_none():
    assert sharpe_ratio(_points([0.01])) is None
    assert sharpe_ratio([]) is None


def test_sharpe_ratio_zero_variance_is_none():
    assert sharpe_ratio(_points([0.01, 0.01, 0.01])) is None


def test_max_drawdown_known_path():
    # Cumulative returns 10%, 20%, 5%, 15% -> equity path 1.10, 1.20, 1.05, 1.15.
    cumulative = [0.10, 0.20, 0.05, 0.15]
    result = max_drawdown(_points(cumulative))
    expected = 1.05 / 1.20 - 1.0
    assert result == pytest.approx(expected)
    assert result < 0


def test_max_drawdown_empty_is_none():
    assert max_drawdown([]) is None


def test_max_drawdown_monotonic_increasing_is_zero():
    cumulative = [0.01, 0.02, 0.03]
    result = max_drawdown(_points(cumulative))
    assert result == pytest.approx(0.0)
