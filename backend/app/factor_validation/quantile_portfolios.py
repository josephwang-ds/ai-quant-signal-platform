"""Equal-weight Q1–Q5 quantile portfolios + long–short — pure calculation."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

QUANTILE_COUNT = 5
_QUANTILE_LABELS = tuple(f"Q{i}" for i in range(1, QUANTILE_COUNT + 1))


def _assign_quantiles(factor_row: pd.Series) -> dict[str, list[str]]:
    """
    Sort by factor ascending, break ties by symbol; map to Q1 (low) … Q5 (high).

    Requires at least QUANTILE_COUNT non-null names. Remainder names are
    distributed from Q1 upward (one extra per bucket starting at Q1).
    """
    clean = factor_row.dropna()
    if len(clean) < QUANTILE_COUNT:
        return {label: [] for label in _QUANTILE_LABELS}

    ordered = sorted(clean.items(), key=lambda item: (float(item[1]), str(item[0])))
    symbols = [symbol for symbol, _ in ordered]
    n = len(symbols)
    base = n // QUANTILE_COUNT
    rem = n % QUANTILE_COUNT
    sizes = [base + (1 if i < rem else 0) for i in range(QUANTILE_COUNT)]

    buckets: dict[str, list[str]] = {}
    cursor = 0
    for label, size in zip(_QUANTILE_LABELS, sizes):
        buckets[label] = symbols[cursor : cursor + size]
        cursor += size
    return buckets


def _equal_weight(symbols: list[str], *, sign: float = 1.0) -> dict[str, float]:
    if not symbols:
        return {}
    w = sign / len(symbols)
    return {symbol: w for symbol in symbols}


def _turnover(prev: dict[str, float], curr: dict[str, float]) -> float:
    """0.5 * L1 distance; first book uses prev={} → 0.5 * Σ|w|."""
    keys = set(prev) | set(curr)
    return 0.5 * float(sum(abs(curr.get(k, 0.0) - prev.get(k, 0.0)) for k in keys))


def _compound(period_returns: list[float]) -> list[float]:
    equity = 1.0
    out: list[float] = []
    for r in period_returns:
        equity *= 1.0 + float(r)
        out.append(equity - 1.0)
    return out


def compute_quantile_portfolios(
    factor_panel: pd.DataFrame,
    forward_return_panel: pd.DataFrame,
    *,
    cost_rate: float = 0.001,
) -> dict[str, Any]:
    """
    Per-rebalance Q1–Q5 average forward returns, cumulatives, LS, turnover, cost.

    Long–short weights: +equal on Q5, −equal on Q1. Turnover and costs are
    computed on that LS book.
    """
    if cost_rate < 0 or not np.isfinite(cost_rate):
        raise ValueError("cost_rate must be a finite non-negative number")

    periods = factor_panel.index.intersection(forward_return_panel.index)
    period_returns: dict[str, list[float]] = {label: [] for label in _QUANTILE_LABELS}
    ls_period: list[float] = []
    ls_net_period: list[float] = []
    turnover_series: list[float] = []
    cost_series: list[float] = []
    dates: list[Any] = []
    prev_weights: dict[str, float] = {}

    for period in periods:
        buckets = _assign_quantiles(factor_panel.loc[period])
        if any(len(buckets[label]) == 0 for label in _QUANTILE_LABELS):
            continue

        fwd = forward_return_panel.loc[period]
        q_rets: dict[str, float] = {}
        ok = True
        for label in _QUANTILE_LABELS:
            members = buckets[label]
            vals = fwd.reindex(members)
            if vals.isna().any() or len(vals) != len(members):
                ok = False
                break
            q_rets[label] = float(vals.mean())
        if not ok:
            continue

        for label in _QUANTILE_LABELS:
            period_returns[label].append(q_rets[label])

        ls = q_rets["Q5"] - q_rets["Q1"]
        ls_period.append(ls)

        q5_w = _equal_weight(buckets["Q5"], sign=1.0)
        q1_w = _equal_weight(buckets["Q1"], sign=-1.0)
        curr_weights = {**q1_w, **q5_w}
        turn = _turnover(prev_weights, curr_weights)
        cost = turn * float(cost_rate)
        ls_net_period.append(ls - cost)
        turnover_series.append(turn)
        cost_series.append(cost)
        prev_weights = curr_weights
        dates.append(period)

    cumulatives = {
        label: _compound(period_returns[label]) for label in _QUANTILE_LABELS
    }
    ls_cumulative = _compound(ls_period)
    ls_net_cumulative = _compound(ls_net_period)

    def _series_payload(values: list[float]) -> list[dict[str, Any]]:
        return [
            {
                "date": str(dates[i]),
                "value": float(values[i]),
            }
            for i in range(len(dates))
        ]

    mean_turnover = (
        float(np.mean(turnover_series)) if turnover_series else None
    )
    total_cost = float(sum(cost_series)) if cost_series else None

    return {
        "dates": [str(d) for d in dates],
        "period_returns": {
            label: _series_payload(period_returns[label]) for label in _QUANTILE_LABELS
        },
        "cumulative_returns": {
            label: _series_payload(cumulatives[label]) for label in _QUANTILE_LABELS
        },
        "long_short": {
            "period_returns": _series_payload(ls_period),
            "cumulative_returns": _series_payload(ls_cumulative),
            "cumulative_final": float(ls_cumulative[-1]) if ls_cumulative else None,
            "period_returns_net_of_cost": _series_payload(ls_net_period),
            "cumulative_returns_net_of_cost": _series_payload(ls_net_cumulative),
            "cumulative_final_net_of_cost": (
                float(ls_net_cumulative[-1]) if ls_net_cumulative else None
            ),
            "note": (
                "Gross long–short is Q5−Q1 before costs. "
                "Net series subtracts turnover × cost_rate each rebalance."
            ),
        },
        "turnover": {
            "series": _series_payload(turnover_series),
            "mean": mean_turnover,
        },
        "transaction_cost": {
            "series": _series_payload(cost_series),
            "total": total_cost,
            "cost_rate": float(cost_rate),
        },
        "n_rebalances": len(dates),
    }
