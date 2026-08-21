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
from itertools import pairwise
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_universe import (
    _assemble,
    _clean,
    _find,
    _read_wikipedia,
    _spells,
)

WIKI_PAGE = """<html><body>
<p>The S&amp;P 500 is a stock market index.</p>
<table class="wikitable"><tr><th>Nav</th></tr><tr><td>unrelated table</td></tr></table>
<table class="wikitable" id="constituents">
  <tr><th>Symbol</th><th>Security</th><th>GICS Sector</th><th>CIK</th></tr>
  <tr><td>AAPL</td><td>Apple Inc.</td><td>Information Technology</td><td>320193</td></tr>
  <tr><td>MSFT</td><td>Microsoft</td><td>Information Technology</td><td>789019</td></tr>
</table>
<table class="wikitable" id="changes">
  <tr><th rowspan="2">Date</th><th colspan="2">Added</th><th colspan="2">Removed</th></tr>
  <tr><th>Ticker</th><th>Security</th><th>Ticker</th><th>Security</th></tr>
  <tr><td>2023-03-01</td><td>XYZ</td><td>Xyz Inc</td><td></td><td></td></tr>
  <tr><td>2021-06-30</td><td></td><td></td><td>XYZ</td><td>Xyz Inc</td></tr>
</table>
</body></html>"""


class FakeResponse:
    def __init__(self, text): self.text = text
    def raise_for_status(self): pass


class TestReadWikipedia:
    """The page is fetched and parsed offline here.

    This exists because of a specific failure: pandas 3 reads a bare string
    argument to read_html as a *file path*, so passing the document itself raises
    FileNotFoundError with the entire document quoted in the message. The visible
    symptom was a terminal full of Wikipedia and no usable error.
    """

    @pytest.fixture(autouse=True)
    def _no_network(self, monkeypatch):
        monkeypatch.setattr("build_universe.requests.get",
                            lambda *a, **k: FakeResponse(WIKI_PAGE))

    def test_parses_a_literal_document(self):
        current, _ = _read_wikipedia({})
        assert len(current) == 2
        assert set(current["ticker"]) == {"AAPL", "MSFT"}

    def test_finds_the_tables_by_content_not_position(self):
        """The constituents table is second on the page, behind an unrelated one."""
        current, changes = _read_wikipedia({})
        assert "ticker" in current.columns and "name" in current.columns
        assert _find(changes, "added", "ticker")
        assert _find(changes, "removed", "ticker")

    def test_multiindex_headers_are_flattened(self):
        _, changes = _read_wikipedia({})
        assert "added_ticker" in changes.columns
        assert "removed_ticker" in changes.columns

    def test_end_to_end_produces_two_spells_for_the_rejoiner(self):
        current, changes = _read_wikipedia({})
        frame = _assemble(current, changes, {"XYZ": 42}, date(2010, 1, 1))
        xyz = frame[frame["ticker"] == "XYZ"]
        assert len(xyz) == 2, "XYZ left in 2021 and returned in 2023"

    def test_a_departed_issuer_is_kept_even_with_no_cik(self):
        """Neither source resolves a CIK for an issuer that has left the index.
        Dropping those rows would delete exactly the historical members the file
        exists to preserve -- and would do it after the survivorship check looked."""
        current, changes = _read_wikipedia({})
        frame = _assemble(current, changes, {}, date(2010, 1, 1))
        xyz = frame[frame["ticker"] == "XYZ"]
        assert len(xyz) == 2
        assert xyz["cik"].isna().all()

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
        for (_, earlier_end), (later_start, _) in pairwise(spells):
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

    def test_issuer_without_a_cik_is_kept_but_marked(self, current, changes):
        """No CIK means no filings to fetch, but the interval still belongs in the
        universe -- the survivorship guard needs to know the issuer existed."""
        frame = _assemble(current, changes, {"XYZ": 1}, START)
        assert set(frame["ticker"]) == {"XYZ", "NEW", "OLD"}
        assert frame.loc[frame["ticker"] == "XYZ", "cik"].notna().all()
        assert frame.loc[frame["ticker"] == "NEW", "cik"].isna().all()

    def test_untouched_current_member_spans_from_start(self, current, changes):
        frame = _assemble(current, changes, {"OLD": 3}, START).set_index("ticker")
        assert frame.loc["OLD", "start_date"] == START
        assert pd.isna(frame.loc["OLD", "end_date"])


class TestTickerCleaning:
    @pytest.mark.parametrize("raw,expected", [
        ("BRK.B", "BRK-B"), (" aapl ", "AAPL"), ("BF.B", "BF-B"), ("MSFT", "MSFT"),
    ])
    def test_normalises(self, raw, expected):
        assert _clean(raw) == expected
