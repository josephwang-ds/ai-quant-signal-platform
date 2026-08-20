"""The universe builder's interval logic.

Pure logic over the additions-and-removals table, so it is testable without the
network the script otherwise needs. The case that matters is a ticker that leaves
and comes back: collapsing its two spells into one would re-admit it for the
years it was absent, reintroducing -- in the file whose whole job is to prevent
it -- exactly the survivorship error.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_universe import _assemble, _clean, _spells   # noqa: E402

START = date(2010, 1, 1)


class TestSpells:
    def test_never_moved_and_still_a_member(self):
        assert _spells([], True, START) == [(START, None)]

    def test_added_once(self):
        assert _spells([(date(2018, 3, 1), "add")], True, START) == [
            (date(2018, 3, 1), None)]

    def test_removed_and_gone(self):
        """First move is a removal, so it was a member before the table begins."""
        assert _spells([(date(2021, 6, 30), "remove")], False, START) == [
            (START, date(2021, 6, 30))]

    def test_left_and_came_back(self):
        moves = [(date(2021, 6, 30), "remove"), (date(2023, 3, 1), "add")]
        assert _spells(moves, True, START) == [
            (START, date(2021, 6, 30)),
            (date(2023, 3, 1), None),
        ]

    def test_two_complete_spells(self):
        moves = [(date(2016, 1, 5), "add"), (date(2019, 4, 1), "remove"),
                 (date(2022, 9, 1), "add")]
        assert _spells(moves, True, START) == [
            (date(2016, 1, 5), date(2019, 4, 1)),
            (date(2022, 9, 1), None),
        ]

    def test_moves_out_of_order_are_sorted(self):
        moves = [(date(2023, 3, 1), "add"), (date(2021, 6, 30), "remove")]
        assert _spells(moves, True, START) == _spells(sorted(moves), True, START)

    def test_spells_never_overlap(self):
        moves = [(date(2016, 1, 5), "add"), (date(2019, 4, 1), "remove"),
                 (date(2022, 9, 1), "add"), (date(2023, 1, 1), "remove")]
        spells = _spells(moves, False, START)
        for (_, earlier_end), (later_start, _) in zip(spells, spells[1:]):
            assert earlier_end is not None and earlier_end <= later_start


class TestAssemble:
    @pytest.fixture
    def changes(self) -> pd.DataFrame:
        return pd.DataFrame({
            "Date": ["2021-06-30", "2023-03-01", "2018-03-01"],
            "Added_Ticker": [None, "XYZ", "NEW"],
            "Removed_Ticker": ["XYZ", None, None],
        })

    @pytest.fixture
    def current(self) -> pd.DataFrame:
        return pd.DataFrame({"ticker": ["XYZ", "NEW", "OLD"],
                             "name": ["Xyz Inc", "New Co", "Old Co"]})

    def test_rejoiner_gets_two_rows(self, current, changes):
        ciks = {"XYZ": 1, "NEW": 2, "OLD": 3}
        frame = _assemble(current, changes, ciks, START)
        xyz = frame[frame["ticker"] == "XYZ"]
        assert len(xyz) == 2
        assert xyz["end_date"].isna().sum() == 1        # one spell still open

    def test_issuer_without_a_cik_is_dropped(self, current, changes):
        """No CIK means no EDGAR filings to fetch; carrying it forward only
        produces a confusing failure later in the pull."""
        frame = _assemble(current, changes, {"XYZ": 1}, START)
        assert set(frame["ticker"]) == {"XYZ"}

    def test_untouched_current_member_spans_from_start(self, current, changes):
        frame = _assemble(current, changes, {"OLD": 3}, START)
        assert frame["start_date"].iloc[0] == START
        assert pd.isna(frame["end_date"].iloc[0])


class TestTickerCleaning:
    @pytest.mark.parametrize("raw,expected", [
        ("BRK.B", "BRK-B"), (" aapl ", "AAPL"), ("BF.B", "BF-B"), ("MSFT", "MSFT"),
    ])
    def test_normalises(self, raw, expected):
        assert _clean(raw) == expected
