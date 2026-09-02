"""The Form 4 leakage ladder, and why its comparison has to be paired.

A Form 4 can be entered two ways, and one of them is wrong in a way that looks
like a better dataset rather than a mistake: the transaction date is the more
precise field, so anchoring there produces tighter windows and larger apparent
reactions. These pin down that the two anchors are scored on the same filings,
that the honest one is the later one, and that the difference is measured rather
than assumed.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from filing_triage.config import PipelineConfig

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from export_insider_evidence import (  # noqa: E402  (needs the path above)
    ANCHORS,
    anchored_events,
    ladder,
    reaction_by_kind,
)

from filing_triage.pit import TradingClock  # noqa: E402  (after the path insert)

SESSIONS = pd.bdate_range("2023-01-02", periods=420)


def _returns(seed: int = 3) -> pd.DataFrame:
    """A two-ticker panel with the benchmark the market model needs."""
    rng = np.random.default_rng(seed)
    frames = []
    for ticker in ("AAA", "SPY"):
        close = 100 * np.exp(np.cumsum(rng.normal(0, 0.012, len(SESSIONS))))
        frames.append(pd.DataFrame({
            # `date` objects, not Timestamps: that is what the ingested price
            # frame carries, and the session grid is keyed on it directly.
            "ticker": ticker, "date": SESSIONS.date, "close": close,
            "open": close * 0.999, "high": close * 1.01, "low": close * 0.99,
            "volume": rng.integers(1e6, 5e6, len(SESSIONS)),
        }))
    from filing_triage.ingest.prices import to_returns

    return to_returns(pd.concat(frames, ignore_index=True))


def _events(n: int = 60, gap_days: int = 2) -> pd.DataFrame:
    """Filings whose transaction date sits `gap_days` before acceptance."""
    accepted = SESSIONS[200:200 + n]
    return pd.DataFrame({
        "event_id": [f"e{i}" for i in range(n)],
        "ticker": "AAA",
        "acceptance_time": pd.DatetimeIndex(accepted).tz_localize(
            "America/New_York") + pd.Timedelta(hours=18),
        "first_transaction_date": (accepted - pd.Timedelta(days=gap_days)).date,
        "last_transaction_date": accepted.date,
        "disclosure_gap_days": float(gap_days),
        "trades": 1,
        "net_value": np.linspace(-5e5, 5e5, n),
        "gross_value": 5e5,
        "direction": ["sell"] * (n // 2) + ["buy"] * (n - n // 2),
        "any_plan_10b5_1": [True, False] * (n // 2),
        "all_plan_10b5_1": False,
        "owners": 1,
        "any_officer": True,
        "any_director": False,
        "any_ten_percent_owner": False,
        "behaviour": ["routine", "opportunistic"] * (n // 2),
    })


class TestTheTwoAnchors:
    def test_the_honest_anchor_never_precedes_the_naive_one(self):
        """The insider traded first and the market learned later. An entry built
        from the acceptance time cannot sit earlier than one built from the
        trade, or the gap has been applied backwards."""
        events = _events()
        clock = TradingClock()
        honest = anchored_events(events, "acceptance_time", clock)
        naive = anchored_events(events, "transaction_date", clock)
        merged = honest.set_index("event_id")["entry_session"].to_frame("honest").join(
            naive.set_index("event_id")["entry_session"].rename("naive"))
        assert (merged["honest"] >= merged["naive"]).all()

    def test_the_gap_actually_separates_the_two(self):
        """If both anchors produced the same entry the ladder would measure
        nothing, and would say so by reporting a zero difference for the wrong
        reason."""
        events = _events(gap_days=4)
        clock = TradingClock()
        honest = anchored_events(events, "acceptance_time", clock)
        naive = anchored_events(events, "transaction_date", clock)
        merged = honest.set_index("event_id")["entry_session"].to_frame("honest").join(
            naive.set_index("event_id")["entry_session"].rename("naive"))
        assert (merged["honest"] > merged["naive"]).mean() > 0.9

    def test_an_event_without_a_usable_date_is_dropped_not_guessed(self):
        events = _events(n=10)
        events.loc[events.index[:3], "first_transaction_date"] = None
        assert len(anchored_events(events, "transaction_date", TradingClock())) == 7

    def test_the_anchors_are_named_honest_and_not(self):
        assert ANCHORS[-1] == "acceptance_time"


class TestTheLadderIsPaired:
    @pytest.fixture(scope="class")
    def built(self):
        return ladder(_events(), _returns(), PipelineConfig())

    def test_both_rows_are_scored_on_the_same_filings(self, built):
        """Otherwise the comparison could be won by one rule keeping events the
        other drops, which is a different claim entirely."""
        table, summary = built
        assert summary["shared_filings"] > 0, "the ladder scored nothing"
        assert table["filings"].nunique() == 1
        assert table["filings"].iloc[0] == summary["shared_filings"]

    def test_exactly_one_row_is_marked_honest(self, built):
        table, _ = built
        assert table["honest"].sum() == 1
        assert table.loc[table["honest"], "anchor"].iloc[0] == "acceptance_time"

    def test_the_summary_reports_the_difference_signed(self, built):
        """Positive means the naive anchor manufactured reaction out of days the
        market had not yet seen the filing."""
        table, summary = built
        naive = table[~table["honest"]].iloc[0]
        honest = table[table["honest"]].iloc[0]
        assert summary["shared_filings"] > 0, "the ladder scored nothing"
        assert summary["inflation_in_material_share"] == pytest.approx(
            naive["material_share"] - honest["material_share"])


class TestSubgroupsAreNotReportedOnNoise:
    def test_thin_groups_are_dropped_rather_than_shown(self):
        """A rate computed on nine filings is noise wearing a percentage sign."""
        events = _events()
        labels = pd.DataFrame({"event_id": events["event_id"],
                               "reaction": np.linspace(-3, 3, len(events))})
        table = reaction_by_kind(events, labels, PipelineConfig(), minimum=1000)
        assert table.empty

    def test_the_cuts_the_literature_names_are_all_present(self):
        events = _events()
        labels = pd.DataFrame({"event_id": events["event_id"],
                               "reaction": np.linspace(-3, 3, len(events))})
        table = reaction_by_kind(events, labels, PipelineConfig(), minimum=5)
        assert set(table["cut"]) == {"direction", "behaviour", "disclosed plan", "role"}

    def test_every_reported_group_carries_its_count(self, ):
        events = _events()
        labels = pd.DataFrame({"event_id": events["event_id"],
                               "reaction": np.linspace(-3, 3, len(events))})
        table = reaction_by_kind(events, labels, PipelineConfig(), minimum=5)
        assert (table["filings"] >= 5).all()
