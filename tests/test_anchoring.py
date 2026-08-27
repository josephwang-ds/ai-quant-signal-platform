"""Where the reaction window opens, and why that is a measurement choice.

The entry rule and the label answer two different questions, and the project
spent a while implying they answered one. `pit_entry` guarantees the entry uses
an opening print that postdates EDGAR acceptance; the close-to-close label never
uses that print at all, opening instead at the previous close. These tests pin
down both halves: that the discrepancy is measured and reported, and that it is
deliberately *not* treated as a leak.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from filing_triage import pipeline
from filing_triage.config import PipelineConfig
from filing_triage.experiments import STAGES, anchoring_study
from filing_triage.ingest.prices import to_returns
from filing_triage.labels import _market_model


class TestTheSwitchIsNotACorrectnessSwitch:
    """It changes the question, not the honesty. Four bugs, not five."""

    def test_open_anchoring_does_not_participate_in_is_honest(self):
        assert PipelineConfig(open_anchored_returns=False).is_honest
        assert PipelineConfig(open_anchored_returns=True).is_honest

    def test_default_label_basis_is_the_event_study_convention(self):
        assert PipelineConfig().open_anchored_returns is False

    def test_it_is_not_a_rung_on_the_leakage_ladder(self):
        for _, switches, _ in STAGES:
            assert "open_anchored_returns" not in switches


class TestTheDiscrepancyIsReported:
    def test_close_anchored_labels_open_before_acceptance(self, world):
        result = pipeline.run(world.events, world.prices, world.membership,
                              PipelineConfig(), compute_importance=False)
        # Most 8-Ks land outside market hours, so most close-to-close windows
        # start at a price printed before the filing was accepted.
        assert result.integrity["pre_acceptance_label_anchors"] > 0
        assert result.integrity["pre_acceptance_label_share"] > 0.5
        assert result.integrity["median_label_anchor_staleness_hours"] > 0

    def test_open_anchoring_removes_them_entirely(self, world):
        result = pipeline.run(
            world.events, world.prices, world.membership,
            replace(PipelineConfig(), open_anchored_returns=True),
            compute_importance=False)
        assert result.integrity["pre_acceptance_label_anchors"] == 0
        assert result.integrity["pre_acceptance_label_share"] == 0.0

    def test_the_guards_stay_silent_either_way(self, world):
        """The point of the finding: no leakage check can see this.

        A reader could reasonably expect the audit to catch a label that opens
        before its own event. It cannot, because every check is about facts
        reaching a decision, and this is a choice about what to measure.
        """
        for open_anchored in (False, True):
            result = pipeline.run(
                world.events, world.prices, world.membership,
                replace(PipelineConfig(), open_anchored_returns=open_anchored),
                compute_importance=False)
            assert result.audit.passed


class TestAnchoringStudy:
    def test_reports_both_bases_and_the_share_already_priced(self, world):
        table = anchoring_study(world.events, world.prices, world.membership)
        assert list(table["reaction measured from"]) == [
            "prior close (label basis)", "entry open"]
        assert table.loc[0, "pre_acceptance_label_share"] > 0.5
        assert table.loc[1, "pre_acceptance_label_anchors"] == 0
        # The open-anchored question is genuinely harder: most of the reaction
        # is in the opening print, so far fewer filings clear the same cutoff.
        assert table.loc[1, "base_rate"] < table.loc[0, "base_rate"]


class TestOpenToCloseReturns:
    def test_to_returns_emits_both_series(self):
        prices = pd.DataFrame({
            "ticker": ["AAA"] * 3,
            "date": pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]).date,
            "open": [100.0, 104.0, 103.0],
            "high": [106.0, 106.0, 106.0],
            "low": [99.0, 99.0, 99.0],
            "close": [102.0, 105.0, 101.0],
            "volume": [1e6, 1e6, 1e6],
        })
        out = to_returns(prices)
        assert out["ret_open_to_close"].iloc[0] == 102.0 / 100.0 - 1.0
        # Close-to-close spans the overnight gap; open-to-close does not.
        assert out["ret"].iloc[1] == 105.0 / 102.0 - 1.0
        assert out["ret_open_to_close"].iloc[1] == 105.0 / 104.0 - 1.0

    def test_a_non_positive_open_becomes_missing_rather_than_infinite(self):
        prices = pd.DataFrame({
            "ticker": ["AAA", "AAA"],
            "date": pd.to_datetime(["2024-01-02", "2024-01-03"]).date,
            "open": [0.0, 50.0], "high": [1.0, 60.0], "low": [0.0, 40.0],
            "close": [1.0, 55.0], "volume": [1e6, 1e6],
        })
        out = to_returns(prices)
        assert np.isnan(out["ret_open_to_close"].iloc[0])


class TestMarketModelDegreesOfFreedom:
    def test_residual_sd_spends_both_estimated_parameters(self):
        rng = np.random.default_rng(0)
        mkt = rng.normal(0, 0.01, 120)
        stock = 0.0003 + 1.2 * mkt + rng.normal(0, 0.008, 120)
        _, _, resid_sd = _market_model(stock, mkt)

        resid = stock - np.polyval(np.polyfit(mkt, stock, 1), mkt)
        assert resid_sd == np.float64(resid.std(ddof=2)).item() or np.isclose(
            resid_sd, resid.std(ddof=2))
        # ddof=1 would understate the noise, and the reaction score divides by it.
        assert resid_sd > resid.std(ddof=1)


class TestSyntheticOpensCarryInformation:
    def test_open_to_close_is_not_pure_noise(self, world):
        """The corpus has to be able to express the question being asked of it.

        Opens used to be the same session's close plus a wobble, which made
        every open-to-close return noise and both anchoring bases score
        identically -- the study would have measured nothing.
        """
        returns = to_returns(world.prices)
        paired = returns.dropna(subset=["ret", "ret_open_to_close"])
        correlation = paired["ret"].corr(paired["ret_open_to_close"])
        assert correlation > 0.4
