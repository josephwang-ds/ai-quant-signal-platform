"""Single-factor (market) alpha/beta regression and additive performance
decomposition for a long-short factor portfolio.

Pure calculation — no market-data I/O, no FastAPI. Benchmark forward returns
are built with the same monthly forward-return construction used for the
factor panel (see ``factors.build_monthly_forward_returns``) so the benchmark
series lines up period-for-period with the long-short portfolio it is
regressed against.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.factor_validation.factors import build_monthly_forward_returns

_MIN_REGRESSION_OBS = 3


def build_benchmark_period_returns(
    benchmark_close: pd.Series,
    *,
    holding_period_months: int,
    period_labels: list[str],
) -> pd.Series:
    """Forward returns for one benchmark symbol, aligned to the ``"%Y-%m"``
    period labels used throughout the factor/quantile pipeline.

    Periods present in ``period_labels`` but not in the benchmark's own price
    history are left as NaN (missing, not zero) — callers must treat them as
    unavailable rather than a realized zero return.
    """
    panel = benchmark_close.to_frame(name="__benchmark__")
    forward = build_monthly_forward_returns(
        panel, holding_period_months=holding_period_months
    )
    forward.index = pd.Index(
        [
            idx.strftime("%Y-%m") if hasattr(idx, "strftime") else str(idx)
            for idx in forward.index
        ]
    )
    series = forward["__benchmark__"].astype(float)
    return series.reindex(period_labels)


def period_return_series(period_returns: list[dict[str, Any]]) -> pd.Series:
    """Convert the ``[{"date": ..., "value": ...}, ...]`` payload shape used
    throughout ``quantile_portfolios.py`` into a date-indexed ``pd.Series``."""
    if not period_returns:
        return pd.Series(dtype=float)
    return pd.Series(
        [float(item["value"]) for item in period_returns],
        index=pd.Index([str(item["date"]) for item in period_returns]),
        dtype=float,
    )


def regress_alpha_beta(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
) -> dict[str, Any]:
    """OLS of portfolio period return on benchmark period return.

    Returns the per-period alpha (regression intercept), an annualized alpha
    (compounded assuming 12 periods/year) with a 95% confidence interval
    (normal approximation — z=1.96, not the exact t-distribution, since this
    is a descriptive interval rather than a formal hypothesis test), beta
    (slope), the t-stat for alpha, R-squared, and the number of paired
    observations used. Fields are ``None`` — never fabricated — when fewer
    than 3 paired observations are available, or when the alpha standard
    error cannot be computed.
    """
    aligned = pd.concat(
        [
            portfolio_returns.rename("portfolio"),
            benchmark_returns.rename("benchmark"),
        ],
        axis=1,
        join="inner",
    ).dropna()
    n = int(len(aligned))
    if n < _MIN_REGRESSION_OBS:
        return {
            "alpha": None,
            "alpha_annualized": None,
            "alpha_annualized_ci_low": None,
            "alpha_annualized_ci_high": None,
            "beta": None,
            "t_stat_alpha": None,
            "r_squared": None,
            "n_observations": n,
        }

    x = aligned["benchmark"].to_numpy(dtype=float)
    y = aligned["portfolio"].to_numpy(dtype=float)
    x_mean = float(x.mean())
    y_mean = float(y.mean())
    x_centered = x - x_mean
    y_centered = y - y_mean
    ss_xx = float(np.sum(x_centered**2))
    beta = float(np.sum(x_centered * y_centered) / ss_xx) if ss_xx > 0 else 0.0
    alpha = float(y_mean - beta * x_mean)

    residuals = y - (alpha + beta * x)
    ss_res = float(np.sum(residuals**2))
    ss_tot = float(np.sum(y_centered**2))
    r_squared = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else None

    dof = n - 2
    t_stat_alpha: float | None = None
    alpha_annualized_ci_low: float | None = None
    alpha_annualized_ci_high: float | None = None
    if dof > 0 and ss_xx > 0:
        residual_variance = ss_res / dof
        se_alpha_sq = residual_variance * (1.0 / n + (x_mean**2) / ss_xx)
        if se_alpha_sq > 0:
            se_alpha = float(np.sqrt(se_alpha_sq))
            t_stat_alpha = float(alpha / se_alpha)
            alpha_ci_low = alpha - 1.96 * se_alpha
            alpha_ci_high = alpha + 1.96 * se_alpha
            alpha_annualized_ci_low = float((1.0 + alpha_ci_low) ** 12 - 1.0)
            alpha_annualized_ci_high = float((1.0 + alpha_ci_high) ** 12 - 1.0)

    alpha_annualized = (
        float((1.0 + alpha) ** 12 - 1.0) if np.isfinite(alpha) else None
    )

    return {
        "alpha": alpha,
        "alpha_annualized": alpha_annualized,
        "alpha_annualized_ci_low": alpha_annualized_ci_low,
        "alpha_annualized_ci_high": alpha_annualized_ci_high,
        "beta": beta,
        "t_stat_alpha": t_stat_alpha,
        "r_squared": r_squared,
        "n_observations": n,
    }


def decompose_performance(
    *,
    gross_period_returns: list[dict[str, Any]],
    net_period_returns: list[dict[str, Any]],
    benchmark_returns: pd.Series,
    beta: float | None,
) -> dict[str, Any]:
    """Additive (not geometric) cumulative decomposition for the "where did
    performance come from" chart.

    Uses the single ``beta`` fitted on net (cost-adjusted) returns so the
    identity ``cumulative_beta_contribution + cumulative_residual_alpha ==
    cumulative net return`` holds exactly. ``cumulative_cost_drag`` is a
    separate, purely informational series (gross − net) showing how much of
    gross performance costs consumed — it is not a fourth additive term.

    This is an approximation for illustration, not a geometric return
    decomposition: cumulative components are running sums of each period's
    component rather than compounded wealth. See the returned
    ``methodology`` string.
    """
    gross = period_return_series(gross_period_returns)
    net = period_return_series(net_period_returns)
    if gross.empty or net.empty or beta is None:
        return {
            "dates": [],
            "cumulative_beta_contribution": [],
            "cumulative_residual_alpha": [],
            "cumulative_cost_drag": [],
            "methodology": (
                "Unavailable — requires long-short period returns and a "
                "fitted market beta."
            ),
        }

    bench = benchmark_returns.reindex(net.index)
    cost = (gross - net).fillna(0.0)
    beta_contribution = (float(beta) * bench).fillna(0.0)
    residual_alpha = (net - beta_contribution).where(bench.notna(), net)

    dates = [str(value) for value in net.index]
    cum_beta = np.cumsum(beta_contribution.to_numpy(dtype=float))
    cum_residual = np.cumsum(residual_alpha.to_numpy(dtype=float))
    cum_cost = np.cumsum(cost.to_numpy(dtype=float))

    def _series(values: np.ndarray) -> list[dict[str, Any]]:
        return [
            {"date": dates[i], "value": float(values[i])} for i in range(len(dates))
        ]

    return {
        "dates": dates,
        "cumulative_beta_contribution": _series(cum_beta),
        "cumulative_residual_alpha": _series(cum_residual),
        "cumulative_cost_drag": _series(cum_cost),
        "methodology": (
            "Additive approximation: each period's net (cost-adjusted) "
            "long-short return is split into beta x benchmark_return (beta "
            "contribution) and net return minus that contribution (residual "
            "alpha); their cumulative sums add up to the cumulative net "
            "return exactly. Cost drag (gross minus net) is shown as a "
            "separate, purely informational series, not a third additive "
            "term. These are running sums of return points, not geometric "
            "compounding, and should be read as a decomposition of "
            "performance drivers rather than compounded wealth."
        ),
    }
