"""End to end: filings and prices in, a ranked queue and an audit out.

The order is deliberate. Timestamps are resolved first, the universe is filtered
second, and only then is anything measured -- because every later step inherits
whatever those two got wrong.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from filing_triage.config import PipelineConfig
from filing_triage.evaluate import daily_queue, evaluate, evaluate_by_fold
from filing_triage.features import build_features
from filing_triage.guards import LeakageAudit
from filing_triage.ingest.prices import to_returns
from filing_triage.ingest.universe import restrict_to_membership
from filing_triage.labels import build_labels
from filing_triage.model import TriageModel
from filing_triage.pit import CALENDAR, TradingClock, naive_entry_session_from_filing_date


@dataclass
class PipelineResult:
    config: PipelineConfig
    events: pd.DataFrame
    features: pd.DataFrame
    labels: pd.DataFrame
    predictions: pd.DataFrame
    metrics: dict
    by_fold: pd.DataFrame
    audit: LeakageAudit
    queue: pd.DataFrame
    importance: pd.DataFrame = field(default_factory=pd.DataFrame)
    integrity: dict = field(default_factory=dict)


def run(events: pd.DataFrame, prices: pd.DataFrame, membership: pd.DataFrame,
        config: PipelineConfig | None = None, *,
        compute_importance: bool = True) -> PipelineResult:
    config = config or PipelineConfig()
    clock = TradingClock(embargo=config.embargo)

    events = _resolve_timing(events.copy(), clock, config)
    integrity = _entry_integrity(events, clock)

    n_before = len(events)
    if config.pit_universe:
        events = restrict_to_membership(events, membership,
                                        ticker="ticker", when="event_date")
    integrity["events_dropped_by_universe"] = n_before - len(events)
    integrity["events_total"] = n_before

    returns = to_returns(prices)
    labels = build_labels(events, returns, config)
    integrity["events_measured"] = int(labels.attrs.get("measured", len(labels)))
    integrity["events_scored"] = 0
    integrity["attrition"] = labels.attrs.get("attrition", {})
    events = events[events["event_id"].isin(labels["event_id"])].reset_index(drop=True)

    features = build_features(events, returns, config)
    aligned = labels.set_index("event_id").loc[features.index]

    audit = _audit(events, features, membership, aligned, config)

    model = TriageModel(config)
    predictions = model.fit_predict_oos(
        features=features,
        labels=aligned["label"],
        event_time=events.set_index("event_id").loc[features.index, "acceptance_time"],
        label_end_time=pd.to_datetime(aligned["label_end_session"]).dt.tz_localize(
            events["acceptance_time"].dt.tz),
        audit=audit,
        compute_importance=compute_importance,
    )

    # Walk-forward tests folds 1..n, so the earliest block is only ever training
    # data and those events never receive an out-of-sample score. That is correct
    # and it is also the last place the count silently drops -- without this line
    # the attrition table adds up to fewer events than were scored, and the reader
    # is left to guess. It is the honest cost of the split: shuffled K-fold
    # "scores" every event, by training on the future to do it.
    held_back = len(features) - len(predictions)
    if held_back > 0:
        integrity["attrition"] = dict(integrity.get("attrition") or {})
        integrity["attrition"]["held out by walk-forward as training-only"] = held_back

    # Importance is calculated on each fold's held-out rows, never on the data
    # used to fit that fold. Leakage/embargo studies disable it for runtime.
    importance = model.oos_importance_

    integrity["events_scored"] = len(predictions)

    return PipelineResult(
        config=config,
        events=events,
        features=features,
        labels=aligned.reset_index(),
        predictions=predictions,
        metrics=evaluate(
            predictions,
            sessions=events.set_index("event_id")["entry_session"],
            events=events,
        ) if len(predictions) else {},
        by_fold=evaluate_by_fold(predictions) if len(predictions) else pd.DataFrame(),
        audit=audit,
        queue=daily_queue(predictions, events) if len(predictions) else pd.DataFrame(),
        importance=importance,
        integrity=integrity,
    )


# --------------------------------------------------------------------------- #
def _resolve_timing(events: pd.DataFrame, clock: TradingClock,
                    config: PipelineConfig) -> pd.DataFrame:
    """Decide, for every filing, the first session we are allowed to act in."""
    events["decision_time"] = events["acceptance_time"].map(clock.decision_time)
    events["session_state"] = events["acceptance_time"].map(clock.session_state)

    if config.pit_entry:
        events["entry_session"] = events["acceptance_time"].map(clock.entry_session)
    else:
        # The bug: the filing *date* treated as tradable at its own open.
        events["entry_session"] = events["filing_date"].map(
            naive_entry_session_from_filing_date)

    events["event_date"] = events["entry_session"]
    return events.sort_values("acceptance_time").reset_index(drop=True)


def _entry_integrity(events: pd.DataFrame, clock: TradingClock) -> dict:
    """How much hindsight the chosen entry rule hands out.

    This is where a bad entry rule shows up. It barely moves the ranking metric --
    which is exactly why it survives code review -- but it means the queue points
    at an opening print that had already happened when the filing landed.
    """
    opens = events["entry_session"].map(
        lambda d: CALENDAR.open_at(d).astimezone(events["acceptance_time"].dt.tz))
    hindsight_hours = (events["acceptance_time"] - opens).dt.total_seconds() / 3600.0
    impossible = hindsight_hours > 0
    return {
        "impossible_entries": int(impossible.sum()),
        "impossible_share": float(impossible.mean()) if len(events) else 0.0,
        "median_hindsight_hours": float(hindsight_hours[impossible].median())
                                  if impossible.any() else 0.0,
        "max_hindsight_hours": float(hindsight_hours.max()) if len(events) else 0.0,
    }


def _audit(events: pd.DataFrame, features: pd.DataFrame, membership: pd.DataFrame,
           labels: pd.DataFrame, config: PipelineConfig) -> LeakageAudit:
    audit = LeakageAudit()
    audit.timezone_aware(events)
    audit.causal(events, fact="acceptance_time", decision="decision_time")
    audit.unique_events(events, ["cik", "accession"])
    audit.universe_pit(events, membership, ticker="ticker", when="event_date")
    audit.feature_matrix(features)

    entry_open = events.set_index("event_id")["entry_session"].map(
        lambda d: CALENDAR.open_at(d).astimezone(events["acceptance_time"].dt.tz))
    tradability = pd.DataFrame({
        "acceptance_time": events.set_index("event_id")["acceptance_time"],
        "entry_open": entry_open,
    })
    audit.causal(tradability, fact="acceptance_time", decision="entry_open",
                 label="entry opens after the EDGAR accepted timestamp",
                 holds="no entry uses a price printed before EDGAR acceptance")

    est = pd.DataFrame({
        "estimation_end": pd.to_datetime(labels["estimation_end"]),
        "event_date": pd.to_datetime(events.set_index("event_id")
                                     .loc[labels.index, "entry_session"]),
    })
    audit.estimation_window_gap(est, est_end="estimation_end", event_date="event_date")
    return audit
