"""Expected reporting dates, and the two ways of getting them that would leak.

The features and the calendar page read one implementation, because the day they
disagree is the day the page stops describing the model's inputs.

Nothing here reads a vendor calendar, and that is the point. A published calendar
is the better source for a display -- it carries announced dates rather than
estimates -- and the wrong source for a feature: the calendar you download today
lists dates as known today, not as known then, and records nothing about when
each was announced. A backtest using it would let a 2022 filing know a date
published weeks later, and no guard here could catch it, because there is no
column to check.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from filing_triage.earnings import (
    earnings_rhythm_features,
    expected_next_report,
    is_earnings_filing,
)


def _events(rows) -> pd.DataFrame:
    return pd.DataFrame([
        {"event_id": f"e{i}", "ticker": ticker, "items": items,
         "acceptance_time": pd.Timestamp(when, tz="America/New_York")}
        for i, (ticker, when, items) in enumerate(rows)
    ])


class TestIdentifyingEarningsFilings:
    def test_item_202_is_matched_on_the_whole_code(self):
        """`2.02` appears inside `12.02`, and a substring match would count a
        filing that is not an earnings release."""
        items = pd.Series(["2.02", "2.02,9.01", "7.01,2.02", "12.02", "8.01", None])
        assert list(is_earnings_filing(items)) == [True, True, True, False,
                                                   False, False]


class TestTheExpectedDate:
    def test_the_annual_anchor_is_used_once_a_year_exists(self):
        """Last year's corresponding quarter plus 365 days. Measured against a
        median-gap predictor on 3,257 predictions it misses by a median of one
        day rather than four, because issuers report on close to the same
        calendar week each year while quarterly gaps drift."""
        rows = [("AAPL", d, "2.02") for d in
                ("2024-02-01", "2024-05-02", "2024-08-01", "2024-11-01",
                 "2025-01-30")]
        table = expected_next_report(_events(rows), as_of="2025-02-15")
        expected = table.set_index("ticker").loc["AAPL"]
        # 2024-05-02 + 365 days
        assert expected["expected"] == pd.Timestamp("2025-05-02")
        assert expected["method"] == "annual anchor"

    def test_cadence_is_the_fallback_before_a_full_year(self):
        rows = [("NEW", d, "2.02") for d in ("2025-01-15", "2025-04-15")]
        table = expected_next_report(_events(rows), as_of="2025-05-01")
        assert table.set_index("ticker").loc["NEW", "method"] == "quarterly cadence"

    def test_one_report_is_not_enough_to_predict_from(self):
        table = expected_next_report(_events([("ONE", "2025-01-15", "2.02")]),
                                     as_of="2025-05-01")
        assert table.empty

    def test_a_passed_estimate_rolls_forward_rather_than_showing_the_past(self):
        """The panel ends before today, or a report is late. Either way "next"
        must not be a date that has already gone by."""
        rows = [("OLD", d, "2.02") for d in
                ("2023-02-01", "2023-05-01", "2023-08-01", "2023-11-01")]
        table = expected_next_report(_events(rows), as_of="2025-06-01")
        assert (table["expected"] >= pd.Timestamp("2025-06-01")).all()
        assert (table["days_until"] >= 0).all()

    def test_the_history_behind_each_estimate_is_reported(self):
        """An estimate from three reports is worth less than one from twenty,
        and saying so is cheaper than letting a reader find out from a miss."""
        rows = [("AAPL", d, "2.02") for d in
                ("2024-02-01", "2024-05-02", "2024-08-01", "2024-11-01")]
        table = expected_next_report(_events(rows), as_of="2025-01-01")
        assert int(table.iloc[0]["prior_reports"]) == 4


class TestTheFeaturesStayPointInTime:
    def test_a_filing_never_informs_its_own_features(self):
        """The filing's own date is excluded by a strict `<`, so an earnings
        filing does not report zero days since the last earnings filing --
        itself."""
        rows = [("AAPL", d, "2.02") for d in ("2024-02-01", "2024-05-02")]
        features = earnings_rhythm_features(_events(rows))
        assert np.isnan(features["days_since_last_earnings"].iloc[0])
        assert features["days_since_last_earnings"].iloc[1] == 91

    def test_a_later_filing_cannot_reach_back_from_the_future(self):
        """Truncating the frame must not change any surviving row: if it did,
        a row would be reading filings that came after it."""
        rows = [("AAPL", d, "2.02") for d in
                ("2024-02-01", "2024-05-02", "2024-08-01", "2024-11-01")]
        full = earnings_rhythm_features(_events(rows))
        partial = earnings_rhythm_features(_events(rows[:3]))
        assert np.allclose(full["days_since_last_earnings"].iloc[:3].to_numpy(),
                           partial["days_since_last_earnings"].to_numpy(),
                           equal_nan=True)

    def test_an_overdue_report_reads_as_negative_not_clipped(self):
        """"Expected date has passed and nothing arrived" is a real state and a
        different one from "not due yet"."""
        rows = [("AAPL", d, "2.02") for d in
                ("2023-02-01", "2023-05-01", "2023-08-01", "2023-11-01",
                 "2025-06-01")]
        features = earnings_rhythm_features(_events(rows))
        assert features["days_to_expected_earnings"].iloc[-1] < 0

    def test_an_issuer_with_no_earnings_filings_gets_missing_not_zero(self):
        features = earnings_rhythm_features(_events([("XYZ", "2024-03-01", "8.01")]))
        assert features["days_since_last_earnings"].isna().all()
        assert features["days_to_expected_earnings"].isna().all()


class TestTheFeaturesReachThePipeline:
    def test_both_columns_are_built(self, world):
        from filing_triage import pipeline
        from filing_triage.config import PipelineConfig

        result = pipeline.run(world.events, world.prices, world.membership,
                              PipelineConfig(), compute_importance=False,
                              compute_uncertainty=False)
        for column in ("days_since_last_earnings", "days_to_expected_earnings"):
            assert column in result.features.columns

    def test_the_page_and_the_features_share_one_predictor(self):
        """Two consumers, one implementation. If the page ever computed its own
        estimate it would drift from the model's inputs without anything saying
        so."""
        import inspect

        from filing_triage import earnings

        source = inspect.getsource(earnings)
        assert source.count("def _predict(") == 1
        assert "_predict(" in inspect.getsource(earnings.expected_next_report)
        assert "_predict(" in inspect.getsource(earnings.earnings_rhythm_features)
