"""The leakage experiment.

Same data, same features, same estimator. The only thing that changes is whether
the pipeline is allowed to cheat -- and by how much. Bugs are switched off one at
a time so each one's contribution is separable rather than a single before/after
number that could be explained by anything.

The point is not that the honest number is small. The point is that the naive
number is large, arrives with no warning, and is what a pipeline written the
obvious way will report.
"""

from __future__ import annotations

from dataclasses import replace

import pandas as pd

from filing_triage import pipeline
from filing_triage.config import PipelineConfig

# Fixes applied cumulatively, cheapest-to-spot first. Each stage differs from the
# previous one by exactly one switch.
STAGES: list[tuple[str, dict, str]] = [
    ("Naive pipeline", {
        "shift_trailing_features": False, "pit_entry": False,
        "pit_universe": False, "purged_cv": False,
    }, ("Shuffled K-fold, today's index, trailing windows that include the event "
        "day, entry on the filing date.")),
    ("+ purged, embargoed CV", {
        "shift_trailing_features": False, "pit_entry": False,
        "pit_universe": False, "purged_cv": True,
    }, ("Stop training on the future and on labels whose outcome windows reach "
        "into the test fold.")),
    ("+ shifted trailing features", {
        "shift_trailing_features": True, "pit_entry": False,
        "pit_universe": False, "purged_cv": True,
    }, ("Trailing volatility and turnover must end the session before entry, not "
        "include it.")),
    ("+ point-in-time universe", {
        "shift_trailing_features": True, "pit_entry": False,
        "pit_universe": True, "purged_cv": True,
    }, ("Screen on index membership as of the event date, restoring the issuers "
        "that were later dropped.")),
    ("+ point-in-time entry", {
        "shift_trailing_features": True, "pit_entry": True,
        "pit_universe": True, "purged_cv": True,
    }, ("Enter at the first open after the acceptance time. Barely moves the "
        "metric -- and hands back every impossible trade.")),
]

# Average precision leads. With a 10% base rate this is a ranking problem, and AUC
# is the wrong headline for one: it averages over the whole ranking, including the
# long tail nobody reads. It is also blunt about leaks that concentrate on the
# positives -- the unshifted-window bug moves AUC by 0.04 and average precision
# by 70%. AUC stays in the table as a familiar cross-check.
HEADLINE = ["average_precision", "roc_auc", "daily_precision_at_5", "daily_lift_at_5"]


def run_leakage_study(events: pd.DataFrame, prices: pd.DataFrame,
                      membership: pd.DataFrame,
                      base: PipelineConfig | None = None) -> pd.DataFrame:
    base = base or PipelineConfig()
    rows = []
    for name, switches, note in STAGES:
        result = pipeline.run(events, prices, membership, replace(base, **switches),
                              compute_importance=False)
        rows.append({
            "stage": name,
            "note": note,
            "n_events": result.metrics.get("n_events", 0),
            "base_rate": result.metrics.get("base_rate", float("nan")),
            **{k: result.metrics.get(k, float("nan")) for k in HEADLINE},
            "impossible_entries": result.integrity["impossible_entries"],
            "impossible_share": result.integrity["impossible_share"],
            "median_hindsight_hours": result.integrity["median_hindsight_hours"],
            "checks_failed": len(result.audit.failures),
            "switches": result.config.describe_switches(),
        })
    return pd.DataFrame(rows)


def embargo_sweep(events: pd.DataFrame, prices: pd.DataFrame,
                  membership: pd.DataFrame, embargoes: list,
                  base: PipelineConfig | None = None) -> pd.DataFrame:
    """How the ranking holds up as we wait longer before acting.

    An effect that survives only at zero delay is a measurement of the
    announcement itself, not something anyone could have used. Watching it decay
    is more informative than any single number.
    """
    base = base or PipelineConfig()
    rows = []
    for embargo in embargoes:
        result = pipeline.run(events, prices, membership, replace(base, embargo=embargo),
                              compute_importance=False)
        rows.append({
            "embargo": str(embargo),
            "embargo_hours": embargo.total_seconds() / 3600.0,
            **{k: result.metrics.get(k, float("nan")) for k in HEADLINE},
        })
    return pd.DataFrame(rows)
