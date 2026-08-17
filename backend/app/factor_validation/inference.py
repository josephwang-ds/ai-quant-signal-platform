"""Inferential statistics for research verdicts.

Every verdict in this platform was, until now, a point estimate compared to a
threshold. A mean RankIC of 0.03 could earn a ``pass`` whether it came from
600 periods or from six.

This module supplies the missing question: *is the estimate distinguishable
from zero once serial correlation is accounted for?*

Newey-West (HAC) rather than an iid t-test, because overlapping forward
returns and persistent factor exposures make research series autocorrelated by
construction. An iid t-statistic on such a series is systematically too large,
which is exactly the direction that manufactures false discoveries.
"""

from __future__ import annotations

import warnings
from collections.abc import Sequence

import numpy as np
import pandas as pd

#: Below this many observations, no HAC claim is made at all.
MIN_OBSERVATIONS_FOR_INFERENCE = 12


def newey_west_lag(n: int, holding_periods: int = 1) -> int:
    """Bandwidth: ``max(floor(4 * (n/100)^(2/9)), holding_periods - 1)``.

    Two constraints, both binding.

    The Newey-West (1994) rule of thumb handles generic serial correlation and
    is deterministic in ``n``, so a reported t-statistic is reproducible from
    the sample size alone.

    The holding-period floor handles the correlation this design *creates*:
    with ``h``-period forward returns sampled every period, consecutive
    observations share ``h-1`` periods of return by construction. A bandwidth
    below ``h-1`` cannot see that overlap and will overstate significance no
    matter how well specified the rest of the model is.

    ``holding_periods`` must be pre-registered with the hypothesis. Tuning the
    lag until ``t > 2`` is p-hacking with extra steps.
    """
    if n < 1:
        return 0
    if holding_periods < 1:
        raise ValueError("holding_periods must be >= 1")
    automatic = int(np.floor(4.0 * (n / 100.0) ** (2.0 / 9.0)))
    return max(automatic, holding_periods - 1)


def _empty_result(n: int, reason: str) -> dict[str, float | int | str | None]:
    return {
        "mean": None,
        "se": None,
        "tstat": None,
        "lags": None,
        "n_observations": n,
        "method": "newey_west",
        "unavailable_reason": reason,
    }


def newey_west_mean_tstat(
    series: pd.Series | np.ndarray,
    *,
    holding_periods: int = 1,
    lags: int | None = None,
) -> dict:
    """HAC t-statistic for the null that the mean of ``series`` is zero.

    ``holding_periods`` is the forward-return horizon that generated the
    series; it sets the minimum bandwidth (see :func:`newey_west_lag`).
    ``lags`` overrides the rule entirely and is recorded as such, so a
    hand-chosen bandwidth is always visible in the evidence package.

    Returns a dict rather than a bare float so that an unavailable result
    carries its reason instead of silently becoming ``0.0`` or ``NaN``.
    """
    values = pd.Series(series).dropna().astype(float)
    n = int(len(values))

    if n == 0:
        return _empty_result(0, "no observations")
    if n < MIN_OBSERVATIONS_FOR_INFERENCE:
        return _empty_result(
            n, f"fewer than {MIN_OBSERVATIONS_FOR_INFERENCE} observations"
        )
    if float(values.std(ddof=1)) == 0.0:
        return _empty_result(n, "zero variance")

    if lags is None:
        lags = newey_west_lag(n, holding_periods)
        lag_rule = f"auto:max(nw1994, holding-1) h={holding_periods}"
    else:
        if lags < 0:
            raise ValueError("lags must be non-negative")
        lag_rule = "explicit override"

    try:
        import statsmodels.api as sm

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = sm.OLS(values.to_numpy(), np.ones(n)).fit(
                cov_type="HAC", cov_kwds={"maxlags": lags}
            )
        mean = float(model.params[0])
        se = float(model.bse[0])
        tstat = float(model.tvalues[0])
    except ImportError:
        return _empty_result(n, "statsmodels unavailable")

    if not np.isfinite(se) or se == 0.0 or not np.isfinite(tstat):
        return _empty_result(n, "degenerate standard error")

    return {
        "mean": mean,
        "se": se,
        "tstat": tstat,
        "lags": lags,
        "lag_rule": lag_rule,
        "holding_periods": holding_periods,
        "n_observations": n,
        "method": "newey_west",
        "unavailable_reason": None,
    }


def lag_sensitivity(
    series: pd.Series | np.ndarray,
    lag_grid: Sequence[int],
    *,
    holding_periods: int = 1,
) -> list[dict]:
    """Report the t-statistic across a grid of bandwidths.

    Not for choosing a lag — the lag is pre-registered. This exists so the
    reader can see how much the conclusion depends on that choice. A result
    that is significant only at the smallest bandwidth is a result about the
    bandwidth.
    """
    out = []
    for lag in lag_grid:
        result = newey_west_mean_tstat(
            series, holding_periods=holding_periods, lags=lag
        )
        out.append(
            {
                "lags": lag,
                "tstat": result["tstat"],
                "se": result["se"],
                "unavailable_reason": result["unavailable_reason"],
            }
        )
    return out


def incremental_signal_value(
    enriched: pd.Series | np.ndarray,
    baseline: pd.Series | np.ndarray,
    *,
    holding_periods: int = 1,
) -> dict:
    """Paired HAC test on ``enriched - baseline``.

    The platform's central statistic. This is deliberately **not** called
    alpha: alpha is the intercept of a portfolio return regressed on a stated
    risk model. What this measures is incremental signal value — how much
    out-of-sample skill the enriched model has that the baseline did not
    already have. Both arms span the same periods and carry the same trading
    assumptions, so the difference isolates the information contribution.

    Portfolio alpha, if wanted, is computed separately and afterwards.

    A positive mean with ``|t| < 2`` is not a finding. It is a shrug.
    """
    left = pd.Series(enriched).astype(float)
    right = pd.Series(baseline).astype(float)

    aligned = pd.concat([left, right], axis=1, join="inner").dropna()
    if aligned.empty:
        return _empty_result(0, "no overlapping observations")

    difference = aligned.iloc[:, 0] - aligned.iloc[:, 1]
    result = newey_west_mean_tstat(difference, holding_periods=holding_periods)
    result["baseline_mean"] = float(aligned.iloc[:, 1].mean())
    result["enriched_mean"] = float(aligned.iloc[:, 0].mean())
    return result


def net_economic_value_bps(
    gross_excess_return_bps: float,
    trading_cost_bps: float,
    inference_cost_currency: float,
    capital_under_management: float,
) -> dict[str, float | None]:
    """Put every term in basis points before subtracting.

    Inference cost arrives in currency per period; excess return arrives in
    basis points. Subtracting one from the other is dimensionally invalid, and
    the fix is not cosmetic: because inference cost is fixed while capital is
    the denominator, **net value is a function of AUM**. The interesting
    question is therefore not which model tier wins, but above what capital
    base an expensive tier begins to pay for itself.
    """
    if capital_under_management <= 0:
        return {
            "net_economic_value_bps": None,
            "inference_cost_bps": None,
            "unavailable_reason": "capital_under_management must be positive",
        }
    inference_cost_bps = (
        inference_cost_currency / capital_under_management
    ) * 10_000.0
    return {
        "net_economic_value_bps": gross_excess_return_bps
        - trading_cost_bps
        - inference_cost_bps,
        "inference_cost_bps": inference_cost_bps,
        "unavailable_reason": None,
    }


def breakeven_capital(
    gross_excess_return_bps: float,
    trading_cost_bps: float,
    inference_cost_currency: float,
) -> float | None:
    """Capital at which a tier's net economic value crosses zero.

    The headline number for a model-tier comparison: below this AUM the tier
    destroys value, above it the tier pays. Returns ``None`` when the tier
    never breaks even because it is unprofitable before inference cost.
    """
    net_before_inference_bps = gross_excess_return_bps - trading_cost_bps
    if net_before_inference_bps <= 0:
        return None
    return inference_cost_currency * 10_000.0 / net_before_inference_bps


def naive_iid_tstat(series: pd.Series | np.ndarray) -> float | None:
    """Uncorrected t-statistic. Provided for contrast, never for verdicts.

    Reporting both makes the autocorrelation penalty visible: when the HAC
    statistic is materially smaller, that gap *is* the overstatement an iid
    test would have handed you.
    """
    values = pd.Series(series).dropna().astype(float)
    n = int(len(values))
    if n < 2:
        return None
    sd = float(values.std(ddof=1))
    if sd == 0.0:
        return None
    return float(values.mean() / (sd / np.sqrt(n)))
