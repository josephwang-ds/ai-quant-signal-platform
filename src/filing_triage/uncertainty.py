"""Intervals, because a point estimate is a claim with its error bar deleted.

This project's whole argument is that a number you are pleased with deserves
more suspicion than one you are not. It spent a while making that argument with
bare point estimates -- 0.366 average precision, 1.59x daily lift -- which is the
same failure one level up: a reader cannot tell 1.59x-plus-or-minus-0.05 from
1.59x-plus-or-minus-0.6, and only one of those is a result.

Two design choices, one of which turned out to matter much less than expected:

**Events are resampled by session, not by row.** Filings on the same morning
share a market and a macro tape, so a row-wise bootstrap that treats 9,729
events as 9,729 independent draws would understate the interval. That was the
reasoning. Measured, the correction is worth about 4% of the interval width on
the real sample -- far less than it sounds like it should be, and the reason is
worth stating: the label is already a *market-model residual*, so the common
factor that would have driven same-day correlation has been subtracted before
the metric ever sees it. The cluster bootstrap stays anyway. It is correct
whether or not clustering is present, the row bootstrap is correct only if it is
absent, and the cost of the safe one is a rounding error.

**The baselines are not a separate experiment.** Model and random see the same
sessions, so their difference is measured within a day and the comparison is
paired. Bootstrapping the two means separately throws that pairing away and
overstates the uncertainty of the difference. Resampling sessions once and
recomputing every rule on that same resample keeps it. This one does matter.

Percentile intervals throughout. BCa would be defensible and is not worth the
extra machinery at these sample sizes, where the bootstrap distributions are
close to symmetric.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from filing_triage.evaluate import BASELINES, daily_baseline_table

N_BOOTSTRAP = 2000
ALPHA = 0.05
SEED = 7


def _percentile_interval(draws: np.ndarray, alpha: float = ALPHA) -> tuple[float, float]:
    finite = draws[np.isfinite(draws)]
    if finite.size == 0:
        return float("nan"), float("nan")
    return (float(np.percentile(finite, 100 * alpha / 2)),
            float(np.percentile(finite, 100 * (1 - alpha / 2))))


def bootstrap_ranking_metrics(predictions: pd.DataFrame, sessions: pd.Series, *,
                              n_boot: int = N_BOOTSTRAP, seed: int = SEED,
                              alpha: float = ALPHA) -> dict[str, float]:
    """Cluster bootstrap of average precision and ROC AUC, resampling sessions.

    Sessions are drawn with replacement and every event belonging to a drawn
    session comes with it, so the resample preserves both the within-day
    clustering and the uneven day sizes.
    """
    frame = predictions.assign(
        session=sessions.reindex(predictions.index).to_numpy())
    groups = [group for _, group in frame.groupby("session", sort=True)]
    if len(groups) < 2:
        return {}

    rng = np.random.default_rng(seed)
    ap = np.empty(n_boot)
    auc = np.empty(n_boot)
    for draw in range(n_boot):
        picked = rng.integers(0, len(groups), len(groups))
        sample = pd.concat([groups[i] for i in picked], ignore_index=True)
        labels = sample["label"].to_numpy()
        scores = sample["score"].to_numpy()
        if np.unique(labels).size < 2:
            ap[draw] = auc[draw] = np.nan
            continue
        ap[draw] = average_precision_score(labels, scores)
        auc[draw] = roc_auc_score(labels, scores)

    ap_lo, ap_hi = _percentile_interval(ap, alpha)
    auc_lo, auc_hi = _percentile_interval(auc, alpha)
    return {
        "average_precision_ci_low": ap_lo,
        "average_precision_ci_high": ap_hi,
        "roc_auc_ci_low": auc_lo,
        "roc_auc_ci_high": auc_hi,
        "bootstrap_sessions": len(groups),
        "bootstrap_draws": n_boot,
    }


def bootstrap_daily_comparisons(predictions: pd.DataFrame, events: pd.DataFrame, *,
                                k: int = 5, n_boot: int = N_BOOTSTRAP,
                                seed: int = SEED, alpha: float = ALPHA) -> pd.DataFrame:
    """Paired session bootstrap of the model against each operational baseline.

    Returns one row per baseline with the observed difference in mean daily
    precision, its interval, the lift and its interval, and the share of draws
    in which the baseline matched or beat the model. That last column is the one
    worth reading first: a lift of 1.38x whose draws favour the baseline 12% of
    the time is a different claim from the same 1.38x at 0.1%.
    """
    table = daily_baseline_table(predictions, events, k)
    if len(table) < 2:
        return pd.DataFrame(columns=["baseline", "model_precision", "baseline_precision",
                                     "difference", "difference_ci_low",
                                     "difference_ci_high", "lift", "lift_ci_low",
                                     "lift_ci_high", "draws_not_beating_baseline",
                                     "sessions"])

    values = {name: table[name].to_numpy(dtype=float) for name in BASELINES}
    rng = np.random.default_rng(seed)
    picks = rng.integers(0, len(table), (n_boot, len(table)))
    # One resample of sessions, reused for every rule, so each draw compares
    # like with like -- that shared draw is what makes the interval paired.
    means = {name: series[picks].mean(axis=1) for name, series in values.items()}

    rows = []
    for name in BASELINES:
        if name == "model":
            continue
        difference = means["model"] - means[name]
        with np.errstate(divide="ignore", invalid="ignore"):
            lift = np.where(means[name] > 0, means["model"] / means[name], np.nan)
        diff_lo, diff_hi = _percentile_interval(difference, alpha)
        lift_lo, lift_hi = _percentile_interval(lift, alpha)
        observed_model = float(values["model"].mean())
        observed_baseline = float(values[name].mean())
        rows.append({
            "baseline": name,
            "model_precision": observed_model,
            "baseline_precision": observed_baseline,
            "difference": observed_model - observed_baseline,
            "difference_ci_low": diff_lo,
            "difference_ci_high": diff_hi,
            "lift": (observed_model / observed_baseline
                     if observed_baseline > 0 else float("nan")),
            "lift_ci_low": lift_lo,
            "lift_ci_high": lift_hi,
            "draws_not_beating_baseline": float(np.mean(difference <= 0)),
            "sessions": len(table),
        })
    return pd.DataFrame(rows)


def stage_deltas(study: pd.DataFrame) -> pd.DataFrame:
    """Rung-to-rung movement on the leakage ladder, as differences.

    No interval here, and the absence is deliberate rather than an omission.
    Consecutive rungs are the same pipeline on overlapping event populations --
    fixing the entry rule changes which filings are measurable at all -- so a
    resample of one rung is not exchangeable with a resample of the next, and a
    paired bootstrap over them would produce an interval that looks rigorous and
    means nothing. What *is* comparable across rungs is the invariant counts,
    which is why those lead the table.
    """
    columns = [c for c in ("average_precision", "roc_auc", "daily_precision_at_5")
               if c in study.columns]
    out = study[["stage", *columns]].copy()
    for column in columns:
        out[f"{column}_delta"] = study[column].diff()
    return out
