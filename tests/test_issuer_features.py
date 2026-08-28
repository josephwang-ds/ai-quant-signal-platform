"""Features built from past labels, and the rule that keeps them knowable.

This is the most dangerous family in the project: everything else is computed
from prices and text that existed at decision time, while these are computed
from *outcomes*. An outcome is knowable only after its window closes, so at
filing N's decision time the usable history is the issuer's prior filings whose
windows had already closed.

`expanding()` over every earlier row is the obvious implementation and it is
wrong -- for an issuer filing in clusters it lets a filing be told the answer by
siblings whose reactions had not finished happening. That is `.rolling()`
without `.shift()`, one level up. On the real sample the rule changes 8.7% of
rows while barely moving the metric, which is the same lesson the universe guard
teaches: the count is the invariant, the score cannot see it.
"""

from __future__ import annotations

from dataclasses import replace

import pandas as pd
import pytest

from filing_triage import pipeline
from filing_triage.config import PipelineConfig
from filing_triage.features import build_features
from filing_triage.ingest.edgar import parse_issuer_profile, sic_division


@pytest.fixture(scope="module")
def scored(world):
    return pipeline.run(world.events, world.prices, world.membership,
                        PipelineConfig(), compute_importance=False,
                        compute_uncertainty=False)


class TestOnlyResolvedHistoryIsCounted:
    def test_the_first_filing_of_an_issuer_has_no_history(self, scored):
        features = scored.features
        events = scored.events.set_index("event_id")
        first = (events.sort_values("acceptance_time")
                 .groupby("ticker").head(1).index)
        usable = features.index.intersection(first)
        assert (features.loc[usable, "issuer_prior_resolved"] == 0).all()

    def test_an_unknown_rate_is_left_missing_not_filled(self, scored):
        """Filling it with the sample mean would carry the whole corpus into
        every issuer that had no history yet."""
        features = scored.features
        none_yet = features["issuer_prior_resolved"] == 0
        if not none_yet.any():
            pytest.skip("every row has history on this world")
        assert features.loc[none_yet, "issuer_prior_material_rate"].isna().all()

    def test_a_rate_is_always_a_proportion(self, scored):
        rate = scored.features["issuer_prior_material_rate"].dropna()
        assert ((rate >= 0) & (rate <= 1)).all()

    def test_no_row_counts_a_filing_whose_window_had_not_closed(self, scored):
        """The invariant, recomputed independently of the implementation."""
        features = scored.features
        frame = (scored.events.set_index("event_id")
                 .loc[features.index, ["ticker", "entry_session"]]
                 .join(scored.labels.set_index("event_id")["label_end_session"]))
        for ticker, group in frame.groupby("ticker"):
            entry = pd.to_datetime(group["entry_session"]).to_numpy("datetime64[D]")
            end = pd.to_datetime(group["label_end_session"]).to_numpy("datetime64[D]")
            for position, event_id in enumerate(group.index):
                allowed = int((end < entry[position]).sum())
                counted = int(features.loc[event_id, "issuer_prior_resolved"])
                assert counted <= allowed, (
                    f"{ticker} {event_id} counted {counted} priors, only "
                    f"{allowed} had resolved"
                )

    def test_the_leaky_switch_counts_more(self, world):
        """The switch has to actually do something, or it is decoration. It is
        also how `experiments` can price the leak instead of asserting it."""
        honest = pipeline.run(world.events, world.prices, world.membership,
                              PipelineConfig(), compute_importance=False,
                              compute_uncertainty=False)
        leaky = pipeline.run(world.events, world.prices, world.membership,
                             replace(PipelineConfig(), resolved_issuer_history=False),
                             compute_importance=False, compute_uncertainty=False)
        shared = honest.features.index.intersection(leaky.features.index)
        counted_honest = honest.features.loc[shared, "issuer_prior_resolved"]
        counted_leaky = leaky.features.loc[shared, "issuer_prior_resolved"]
        assert (counted_leaky >= counted_honest).all()
        assert (counted_leaky > counted_honest).any()

    def test_the_switch_participates_in_is_honest(self):
        """A correctness switch that `is_honest` ignores is one CI cannot gate."""
        assert PipelineConfig().resolved_issuer_history is True
        assert not replace(PipelineConfig(),
                           resolved_issuer_history=False).is_honest


class TestIssuerProfileFeatures:
    def test_sic_division_takes_the_first_two_digits(self):
        assert sic_division(3571) == 35
        assert sic_division("0926") == 9

    def test_an_absent_sic_is_flagged_not_guessed(self):
        assert sic_division(None) == -1
        assert sic_division("") == -1

    def test_the_profile_parser_keeps_the_attributes_it_documents(self):
        payload = {"sic": "3571", "sicDescription": "Electronic Computers",
                   "category": "Large accelerated filer", "fiscalYearEnd": "0926",
                   "stateOfIncorporation": "CA"}
        profile = parse_issuer_profile(payload, 320193)
        assert profile["sic_division"] == 35
        assert profile["fiscal_year_end"] == "0926"

    def test_a_run_without_a_profile_gets_a_sentinel_not_nan(self, scored):
        """No profile table is 'this run has no such source', which is not the
        same fact as 'EDGAR reports nothing for this issuer' -- and an all-NaN
        column makes the imputer warn once per fold about a statistic it cannot
        compute."""
        features = scored.features
        assert (features["sic_group"] == -1).all()
        assert features["days_to_fiscal_year_end"].notna().all()

    def test_a_september_year_end_survives_a_csv_round_trip(self, tmp_path):
        """`0926` comes back from a CSV as the integer 926, which slices to
        month 92. The leading zero is load-bearing."""
        profile = pd.DataFrame([{"cik": 1, "sic_division": 35,
                                 "fiscal_year_end": "0926"}])
        path = tmp_path / "profile.csv"
        profile.to_csv(path, index=False)
        events = pd.DataFrame({
            "event_id": ["a"], "cik": [1], "ticker": ["AAPL"],
            "acceptance_time": pd.to_datetime(["2024-03-01T12:00:00Z"]),
            "items": ["2.02"], "session_state": ["open"],
            "entry_session": [pd.Timestamp("2024-03-04").date()],
        })
        built = build_features(events, pd.DataFrame(
            columns=["ticker", "date", "ret", "volume", "volume_median_60", "close"]),
            PipelineConfig(), profile=pd.read_csv(path))
        days = float(built["days_to_fiscal_year_end"].iloc[0])
        assert 0 <= days <= 365, f"month parsed wrong, got {days}"
