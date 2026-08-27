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

import numpy as np
import pandas as pd

from filing_triage import pipeline
from filing_triage.config import PipelineConfig
from filing_triage.evaluate import daily_baseline_table
from filing_triage.ingest.prices import to_returns
from filing_triage.labels import build_labels
from filing_triage.pit import TradingClock

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
    }, ("Enter at the first open after the acceptance time. This also changes the "
        "measured window; the invariant is that every impossible entry disappears.")),
]

# Average precision leads. With a rare fixed-threshold label this is a ranking problem, and AUC
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
                              compute_importance=False,
                              compute_uncertainty=False)
        rows.append({
            "stage": name,
            "note": note,
            "n_events": result.metrics.get("n_events", 0),
            "base_rate": result.metrics.get("base_rate", float("nan")),
            **{k: result.metrics.get(k, float("nan")) for k in HEADLINE},
            "impossible_entries": result.integrity["impossible_entries"],
            "impossible_share": result.integrity["impossible_share"],
            "median_hindsight_hours": result.integrity["median_hindsight_hours"],
            "pre_acceptance_label_anchors":
                result.integrity["pre_acceptance_label_anchors"],
            "pre_acceptance_label_share":
                result.integrity["pre_acceptance_label_share"],
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
                              compute_importance=False,
                              compute_uncertainty=False)
        rows.append({
            "embargo": str(embargo),
            "embargo_hours": embargo.total_seconds() / 3600.0,
            **{k: result.metrics.get(k, float("nan")) for k in HEADLINE},
        })
    return pd.DataFrame(rows)


def anchoring_study(events: pd.DataFrame, prices: pd.DataFrame,
                    membership: pd.DataFrame,
                    base: PipelineConfig | None = None) -> pd.DataFrame:
    """What the reaction looks like measured from the prior close, and from the open.

    Not a leakage ladder rung, because neither row is a bug. The default
    close-to-close window is the standard market-model event study and it is the
    right basis for a materiality label. But it opens at a price printed before
    most of these filings were accepted, which means the label is not a return
    anyone could have earned -- and the README's "useful triage, not a trading
    strategy" deserves a measurement rather than a promise.

    The open-anchored row is that measurement. It asks how much of the reaction
    was still on the table once the market opened, and the honest answer is: much
    less than the headline label implies. Read the two rows together, never the
    second one alone -- a collapsed base rate here is the question changing, not
    the ranker failing.
    """
    base = base or PipelineConfig()
    rows = []
    for label, open_anchored in (("prior close (label basis)", False),
                                 ("entry open", True)):
        result = pipeline.run(events, prices, membership,
                              replace(base, open_anchored_returns=open_anchored),
                              compute_importance=False,
                              compute_uncertainty=False)
        rows.append({
            "reaction measured from": label,
            "n_events": result.metrics.get("n_events", 0),
            "base_rate": result.metrics.get("base_rate", float("nan")),
            **{k: result.metrics.get(k, float("nan")) for k in HEADLINE},
            "pre_acceptance_label_anchors":
                result.integrity["pre_acceptance_label_anchors"],
            "pre_acceptance_label_share":
                result.integrity["pre_acceptance_label_share"],
            "median_label_anchor_staleness_hours":
                result.integrity["median_label_anchor_staleness_hours"],
        })
    return pd.DataFrame(rows)


def reaction_capture_profile(events: pd.DataFrame, prices: pd.DataFrame,
                             base: PipelineConfig | None = None) -> pd.DataFrame:
    """How much of each filing's reaction was already in the opening print.

    `anchoring_study` shows the ranking metrics collapsing when the label is
    measured from the open, which invites the wrong reading -- that the ranker
    stopped working. This says what actually happened, by measuring the same
    filings both ways and taking the ratio.

    The decomposition is the finding. Across all filings the median share sitting
    in the overnight gap is small, because most 8-Ks move nothing and a ratio of
    two small numbers is noise. Restrict to the filings that cleared the
    materiality cutoff and the share jumps; restrict further to the ones accepted
    after the close and it jumps again. The reaction concentrates in the gap
    exactly where the ranker is trying to look, which is why an open-anchored
    label is so much harder to predict -- and why "useful triage, not a trading
    strategy" is a measurement here rather than a disclaimer.
    """
    base = base or PipelineConfig()
    clock = TradingClock(embargo=base.embargo)
    frame = events.copy()
    frame["entry_session"] = frame["acceptance_time"].map(clock.entry_session)
    frame["session_state"] = frame["acceptance_time"].map(clock.session_state)
    returns = to_returns(prices)

    closed = build_labels(frame, returns, replace(base, open_anchored_returns=False))
    opened = build_labels(frame, returns, replace(base, open_anchored_returns=True))
    paired = (closed.set_index("event_id")[["car", "reaction", "label"]]
              .join(opened.set_index("event_id")[["car", "reaction"]],
                    lsuffix="_close", rsuffix="_open", how="inner")
              .dropna(subset=["car_close", "car_open"]))
    if paired.empty:
        return pd.DataFrame(columns=["population", "filings", "median_share_in_open",
                                     "median_reaction_retained"])

    paired = paired.join(frame.set_index("event_id")["session_state"])
    # A ratio of two near-zero moves is noise, not a share, so the denominator
    # guards against it rather than producing a spectacular meaningless number.
    denominator = paired["car_close"].abs().replace(0.0, np.nan)
    paired["share_in_open"] = 1.0 - paired["car_open"].abs() / denominator
    paired["reaction_retained"] = (
        paired["reaction_open"] / paired["reaction_close"].replace(0.0, np.nan))

    material = paired[paired["label"] == 1]
    populations: list[tuple[str, pd.DataFrame]] = [
        ("all filings", paired),
        ("not material", paired[paired["label"] == 0]),
        ("material (>= threshold)", material),
    ]
    populations += [
        (f"material, accepted {state}", material[material["session_state"] == state])
        for state in ("pre", "open", "post", "closed")
    ]

    return pd.DataFrame([
        {
            "population": name,
            "filings": len(group),
            "median_share_in_open": float(group["share_in_open"].median())
                                    if len(group) else float("nan"),
            "median_reaction_retained": float(group["reaction_retained"].median())
                                        if len(group) else float("nan"),
        }
        for name, group in populations
    ])


# A deliberately coarse grid around the defaults. Wide enough that a result which
# only exists at one setting would show up as a spread; not a search, and never
# used to pick anything.
SENSITIVITY_GRID: list[dict] = [
    {},                                              # the shipped defaults
    {"max_depth": 3},
    {"max_depth": 6},
    {"max_iter": 100},
    {"max_iter": 400},
    {"learning_rate": 0.03},
    {"learning_rate": 0.12},
    {"min_samples_leaf": 10},
    {"min_samples_leaf": 60},
    {"l2_regularization": 0.0},
    {"l2_regularization": 5.0},
]


def hyperparameter_sensitivity(events: pd.DataFrame, prices: pd.DataFrame,
                               membership: pd.DataFrame,
                               base: PipelineConfig | None = None,
                               grid: list[dict] | None = None) -> pd.DataFrame:
    """Whether the headline number depends on the estimator settings.

    The estimator's constants are hard-coded, and a reader is entitled to ask
    where they came from -- because if they were chosen by watching the
    out-of-sample metric, that is a selection leak spanning the whole project and
    the one class of leakage the audit cannot see. No guard can catch it: every
    individual run is clean, and the contamination lives in which run got kept.

    Rather than answer with a promise, answer with a spread. Each row perturbs
    one setting and rescores; if the spread across the grid is small relative to
    the bootstrap interval on the default, then no achievable amount of tuning
    could have produced the headline, and the provenance question stops mattering.
    """
    base = base or PipelineConfig()
    grid = grid if grid is not None else SENSITIVITY_GRID
    rows = []
    for overrides in grid:
        result = pipeline.run(events, prices, membership, base,
                              compute_importance=False,
                              compute_uncertainty=False,
                              estimator_overrides=overrides or None)
        rows.append({
            "setting": ", ".join(f"{k}={v}" for k, v in overrides.items()) or "defaults",
            **{k: result.metrics.get(k, float("nan")) for k in HEADLINE},
        })
    return pd.DataFrame(rows)


# Reading capacities worth reporting. Not a search for the best one: the point
# is that a reader can see how much the headline depends on a number the project
# assumed rather than derived.
CAPACITIES = (1, 2, 3, 5, 10, 20)


def capacity_profile(predictions: pd.DataFrame, events: pd.DataFrame,
                     capacities: tuple[int, ...] = CAPACITIES) -> pd.DataFrame:
    """precision@k against its floor and its ceiling, across reading capacities.

    `k` is how many filings someone reads, not how many arrive, and the project
    fixed it at five because that was the assumed capacity of the reader it was
    written for. That is a product constraint, and quoting one k as *the* metric
    promotes it to a scientific one. This reports the whole tradeoff instead.

    Three columns make it readable, and the third is the one that matters:

      ``oracle``  what a perfect ranker scores. It is not 1.0 and is usually far
                  from it -- a session holding one material filing caps
                  precision@5 at 0.2 however good the ranking is -- so raw
                  precision cannot be read without it.
      ``random``  the floor: each session's own material rate, exactly, not a
                  simulated draw.
      ``span``    where the model sits between the two. Raw precision falls as k
                  grows and so does the ceiling, largely cancelling; the span is
                  what survives the choice of k.

    ``sessions`` falls away sharply with k, and that is the real limit on how far
    this can be pushed: a capacity above the day's filing count is not triage,
    it is reading everything, so those sessions are excluded and at k=20 almost
    nothing is left.
    """
    rows = []
    total_sessions = predictions.join(
        events.set_index("event_id")[["entry_session"]], how="left"
    )["entry_session"].nunique()

    for k in capacities:
        table = daily_baseline_table(predictions, events, k)
        if table.empty:
            continue
        model = float(table["model"].mean())
        random = float(table["random"].mean())
        oracle = float(table["oracle"].mean())
        span = oracle - random
        rows.append({
            "capacity_k": k,
            "sessions": len(table),
            "session_share": len(table) / total_sessions if total_sessions else float("nan"),
            "model": model,
            "random_floor": random,
            "oracle_ceiling": oracle,
            "arrival": float(table["arrival"].mean()),
            "item_202": float(table["item_202"].mean()),
            "lift_vs_random": model / random if random > 0 else float("nan"),
            "span_captured": (model - random) / span if span > 0 else float("nan"),
        })
    return pd.DataFrame(rows)


def session_material_counts(predictions: pd.DataFrame, events: pd.DataFrame,
                            k: int = 5) -> pd.DataFrame:
    """How many material filings a session actually holds, which sets the ceiling.

    The distribution is the explanation for why the ceiling is as low as it is,
    and it is not something the model can do anything about. On the real sample
    a third of eligible sessions contain no material filing at all: on those days
    a perfect ranker scores zero, and so does everything else.
    """
    frame = predictions.join(
        events.set_index("event_id")[["entry_session"]], how="left")
    per_session = frame.groupby("entry_session")["label"].agg(["size", "sum"])
    eligible = per_session[per_session["size"] > k]
    if eligible.empty:
        return pd.DataFrame(columns=["material_filings", "sessions", "share",
                                     "ceiling_at_k"])
    counts = eligible["sum"].astype(int).value_counts().sort_index()
    return pd.DataFrame({
        "material_filings": counts.index,
        "sessions": counts.to_numpy(),
        "share": counts.to_numpy() / len(eligible),
        "ceiling_at_k": [min(int(n), k) / k for n in counts.index],
    })
