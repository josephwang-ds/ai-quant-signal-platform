"""Risk/stability statistics for a realized period-return series.

Pure calculation — no market-data I/O, no FastAPI. These describe how stable
the long-short book's own realized returns are, independent of the market
regression in ``capm.py``.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.factor_validation.capm import period_return_series

_MIN_SHARPE_OBS = 2


def sharpe_ratio(
    period_returns: list[dict[str, Any]],
    *,
    periods_per_year: int = 12,
) -> float | None:
    """Annualized Sharpe ratio of a period-return series (no risk-free rate
    subtracted — returns are already net of transaction costs upstream).

    ``None`` when fewer than 2 observations or the sample has zero variance.
    """
    series = period_return_series(period_returns).dropna()
    n = int(len(series))
    if n < _MIN_SHARPE_OBS:
        return None
    std = float(series.std(ddof=1))
    if std == 0.0 or not np.isfinite(std):
        return None
    mean = float(series.mean())
    return float((mean / std) * np.sqrt(periods_per_year))


def max_drawdown(cumulative_returns: list[dict[str, Any]]) -> float | None:
    """Maximum peak-to-trough drawdown of an equity curve built from a
    cumulative-return series, expressed as a negative fraction (e.g. -0.18
    for an 18% drawdown). ``None`` when the series is empty.
    """
    series = period_return_series(cumulative_returns).dropna()
    if series.empty:
        return None
    equity = 1.0 + series.astype(float)
    running_max = equity.cummax()
    drawdown = equity / running_max - 1.0
    return float(drawdown.min())


__all__ = ["sharpe_ratio", "max_drawdown"]
