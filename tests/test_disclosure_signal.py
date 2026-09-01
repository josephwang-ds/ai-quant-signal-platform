"""The latest-filing card, and what it must refuse to imply.

The card is where a model output finally meets a reader, so the constraints
that mattered upstream have to survive the last translation. It compares one
filing with its own issuer's past and never with other companies; it states
reaction magnitude and never direction; and it disappears rather than degrades
when the scoring run has not happened.
"""

from __future__ import annotations

import json

import pytest

from company_lens.contracts import CompanySnapshot
from company_lens.web.page import _disclosure_signal


def _snapshot(signal=None) -> CompanySnapshot:
    return CompanySnapshot(
        schema_version="test", ticker="AAPL", company_name="Apple Inc.",
        as_of="2026-08-19", benchmark="SPY", period={}, profile={}, market={},
        performance={}, growth=[], period_options={}, latest_filings=[],
        explanation={}, provenance={}, disclosure_signal=signal)


def _signal(**overrides) -> dict:
    base = {
        "state": "read_now",
        "reasons": ["pre-filing volume above 84% of its own history"],
        "probability": 0.43,
        "issuer_base_rate": 0.26,
        "eligible_history": 38,
        "confidence": "standard",
        "points": [{"novelty": 0.5, "reaction": 1.2, "date": "2025-01-01",
                    "items": "2.02", "current": False},
                   {"novelty": 0.9, "reaction": 3.4, "date": "2026-07-30",
                    "items": "2.02,9.01", "current": True}],
        "model": {"estimator": "random_forest", "calibration": "identity",
                  "evaluated_through": "2026-08-17"},
    }
    base.update(overrides)
    return base


class TestTheCardDisappearsRatherThanDegrading:
    def test_no_signal_renders_nothing(self):
        """A card reading "unknown" in four slots takes the same space as a real
        answer and reads like a broken feature."""
        assert _disclosure_signal(_snapshot(None)) == ""

    def test_an_empty_signal_renders_nothing(self):
        assert _disclosure_signal(_snapshot({})) == ""

    def test_a_page_without_a_scoring_run_still_builds(self):
        """The scoring pipeline lives in another package. A company page that
        cannot render without it is a page that breaks whenever it does."""
        assert "signal-section" not in _disclosure_signal(_snapshot(None))


class TestTheCardStatesItsBoundary:
    def test_it_says_magnitude_not_direction(self):
        html = _disclosure_signal(_snapshot(_signal()))
        assert "not" in html and "direction" in html.lower()

    def test_it_never_names_a_trade(self):
        html = _disclosure_signal(_snapshot(_signal())).lower()
        for word in ("buy", "sell", "price target", "expected return"):
            assert word not in html

    def test_it_says_the_comparison_is_within_one_issuer(self):
        html = _disclosure_signal(_snapshot(_signal()))
        assert "same issuer" in html or "own history" in html.lower()


class TestEveryDisplayedNumberCarriesItsQualifiers:
    def test_the_probability_appears_with_the_issuer_base_rate(self):
        """A 43% chance means nothing without knowing this issuer clears its own
        bar 26% of the time anyway."""
        html = _disclosure_signal(_snapshot(_signal()))
        assert "43%" in html and "26%" in html

    def test_the_history_depth_is_shown(self):
        assert "38" in _disclosure_signal(_snapshot(_signal()))

    def test_the_model_and_evaluation_date_are_shown(self):
        html = _disclosure_signal(_snapshot(_signal()))
        assert "random_forest" in html and "2026-08-17" in html

    def test_a_missing_probability_omits_the_stats_rather_than_printing_none(self):
        html = _disclosure_signal(_snapshot(_signal(probability=None)))
        assert "signal-stats" not in html
        assert "None" not in html


class TestTheStates:
    @pytest.mark.parametrize("state,label", [
        ("read_now", "Read now"), ("monitor", "Monitor"), ("routine", "Routine"),
        ("insufficient_history", "Not enough history"), ("withheld", "Withheld"),
    ])
    def test_each_state_has_a_readable_label(self, state, label):
        assert label in _disclosure_signal(_snapshot(_signal(state=state)))

    def test_an_unknown_state_falls_back_to_abstention(self):
        """Never to a confident one: a state this code does not recognise must
        not render as `Read now`."""
        html = _disclosure_signal(_snapshot(_signal(state="something_new")))
        assert "Not enough history" in html
        assert "Read now" not in html


class TestTheScatterData:
    def test_the_points_are_embedded_for_offline_rendering(self):
        html = _disclosure_signal(_snapshot(_signal()))
        assert 'id="signal-points"' in html
        payload = html.split('id="signal-points">')[1].split("</script>")[0]
        assert len(json.loads(payload)) == 2

    def test_exactly_one_point_is_the_current_filing(self):
        points = _signal()["points"]
        assert sum(1 for p in points if p["current"]) == 1

    def test_reasons_are_escaped(self):
        html = _disclosure_signal(_snapshot(
            _signal(reasons=["<script>alert(1)</script>"])))
        assert "<script>alert" not in html
