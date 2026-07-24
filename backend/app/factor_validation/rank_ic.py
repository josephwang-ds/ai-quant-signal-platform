"""Deterministic RankIC / ICIR engine — no market data, no FastAPI."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

ROLLING_IC_WINDOW = 12
_MIN_CROSS_SECTION = 3


def _spearman_rank_ic(factor: pd.Series, forward: pd.Series) -> float | None:
    """Spearman correlation via ranked Pearson; pairwise dropna."""
    aligned = pd.concat([factor, forward], axis=1, join="inner").dropna()
    if len(aligned) < _MIN_CROSS_SECTION:
        return None
    x = aligned.iloc[:, 0].rank(method="average")
    y = aligned.iloc[:, 1].rank(method="average")
    if float(x.std(ddof=0)) == 0.0 or float(y.std(ddof=0)) == 0.0:
        return None
    corr = float(x.corr(y, method="pearson"))
    if not np.isfinite(corr):
        return None
    return corr


def compute_rank_ic_series(
    factor_panel: pd.DataFrame,
    forward_return_panel: pd.DataFrame,
) -> pd.Series:
    """
    Cross-sectional RankIC per period index shared by both panels.

    ``factor_panel`` and ``forward_return_panel`` are wide frames
    (index = period, columns = symbols).
    """
    if factor_panel.empty or forward_return_panel.empty:
        return pd.Series(dtype=float)

    periods = factor_panel.index.intersection(forward_return_panel.index)
    values: list[float] = []
    index: list[Any] = []
    for period in periods:
        ic = _spearman_rank_ic(factor_panel.loc[period], forward_return_panel.loc[period])
        if ic is None:
            continue
        index.append(period)
        values.append(ic)
    return pd.Series(values, index=pd.Index(index), dtype=float, name="rank_ic")


def summarize_ic(rank_ic: pd.Series) -> dict[str, float | None]:
    """Mean / median RankIC, positive IC ratio, ICIR."""
    clean = rank_ic.dropna().astype(float)
    n = int(len(clean))
    if n == 0:
        return {
            "mean_rank_ic": None,
            "median_rank_ic": None,
            "positive_ic_ratio": None,
            "icir": None,
            "n_periods": 0,
        }

    mean_ic = float(clean.mean())
    median_ic = float(clean.median())
    positive_ratio = float((clean > 0).sum() / n)
    std = float(clean.std(ddof=1)) if n >= 2 else float("nan")
    icir: float | None
    if n < 2 or not np.isfinite(std) or std == 0.0:
        icir = None
    else:
        icir = float(mean_ic / std)

    return {
        "mean_rank_ic": mean_ic,
        "median_rank_ic": median_ic,
        "positive_ic_ratio": positive_ratio,
        "icir": icir,
        "n_periods": n,
    }


def rolling_ic(
    rank_ic: pd.Series,
    *,
    window: int = ROLLING_IC_WINDOW,
) -> pd.Series:
    """Trailing mean of RankIC (min_periods = window)."""
    if window < 1:
        raise ValueError("window must be >= 1")
    clean = rank_ic.dropna().astype(float)
    if clean.empty:
        return pd.Series(dtype=float, name="rolling_ic")
    rolled = clean.rolling(window=window, min_periods=window).mean()
    rolled.name = "rolling_ic"
    return rolled.dropna()
