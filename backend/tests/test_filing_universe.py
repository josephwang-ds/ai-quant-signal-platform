"""Point-in-time universe and survivorship-funnel tests.

Offline against a real slice of EDGAR's 2017 QTR1 ``form.idx`` and a matching
slice of ``company_tickers.json``.

The property under protection is not "the parser works". It is that the
universe is assembled from **what was filed at the time**, and that the names
lost on the way to a tradeable symbol are counted rather than quietly dropped.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.text_signals.filing_universe import (
    FilingIndexEntry,
    UniverseFunnel,
    annual_filers,
    build_universe_for_year,
    parse_company_tickers,
    parse_form_index,
    summarize_funnels,
)

FIXTURES = Path(__file__).parent / "fixtures" / "universe"
INDEX = FIXTURES / "form-2017-QTR1-slice.idx"
TICKERS = FIXTURES / "company_tickers_slice.json"


def _entries():
    return parse_form_index(INDEX.read_text(encoding="utf-8", errors="replace"))


def _tickers():
    return parse_company_tickers(TICKERS.read_bytes())


class TestFormIndexParsing:
    def test_parses_real_index_lines(self):
        entries = _entries()
        assert entries
        first = entries[0]
        assert first.form_type == "10-K"
        assert first.cik > 0
        assert first.filing_date.startswith("2017-")
        assert first.document_path.startswith("edgar/data/")

    def test_amendments_are_excluded(self):
        """10-K/A restates a prior filing; counting it would double the year."""
        forms = {e.form_type for e in _entries()}
        assert forms == {"10-K"}

    def test_transition_reports_are_excluded(self):
        """10-KT covers a non-standard span and is not comparable year over year."""
        raw = INDEX.read_text(encoding="utf-8", errors="replace")
        assert "10-KT" in raw, "fixture lost its 10-KT decoys"
        assert all(e.form_type != "10-KT" for e in _entries())

    def test_other_forms_are_ignored(self):
        raw = INDEX.read_text(encoding="utf-8", errors="replace")
        assert "8-K " in raw, "fixture lost its 8-K decoys"
        assert all(e.form_type == "10-K" for e in _entries())

    def test_accession_number_is_derived_from_the_path(self):
        entry = FilingIndexEntry(
            form_type="10-K",
            company_name="Example Corp",
            cik=1234,
            filing_date="2017-03-01",
            document_path="edgar/data/1234/0001683168-17-000653.txt",
        )
        assert entry.accession_number == "0001683168-17-000653"

    def test_company_names_with_multiple_spaces_survive(self):
        entries = _entries()
        assert all(e.company_name.strip() == e.company_name for e in entries)
        assert all(e.company_name for e in entries)


class TestBothIndexDialects:
    """The daily and quarterly indexes format dates differently.

    Quarterly writes ``2017-03-24``; daily writes ``20260814``. A parser that
    accepts only one returns **zero** matches against the other — which reads
    as "no filings that day" rather than as a parse failure. That silent zero
    was a real bug: the live collector reported 0 new 10-K filings on a day
    that had 14.
    """

    DAILY = FIXTURES / "form-daily-20260814-slice.idx"

    def test_daily_index_dialect_parses(self):
        entries = parse_form_index(
            self.DAILY.read_text(encoding="utf-8", errors="replace")
        )
        assert entries, "daily-index dialect must not silently yield zero"
        assert all(e.form_type == "10-K" for e in entries)

    def test_daily_dates_are_normalised_to_iso(self):
        entries = parse_form_index(
            self.DAILY.read_text(encoding="utf-8", errors="replace")
        )
        for entry in entries:
            assert len(entry.filing_date) == 10
            assert entry.filing_date[4] == "-" and entry.filing_date[7] == "-"

    def test_quarterly_dialect_still_parses(self):
        assert parse_form_index(
            INDEX.read_text(encoding="utf-8", errors="replace")
        )


class TestAnnualFilers:
    def test_deduplicates_by_cik_keeping_earliest(self):
        entries = [
            FilingIndexEntry("10-K", "Dup Corp", 7, "2017-06-01", "edgar/data/7/b.txt"),
            FilingIndexEntry("10-K", "Dup Corp", 7, "2017-02-01", "edgar/data/7/a.txt"),
        ]
        chosen = annual_filers(entries, year=2017)
        assert len(chosen) == 1
        assert chosen[7].filing_date == "2017-02-01"

    def test_filters_to_the_requested_year(self):
        entries = [
            FilingIndexEntry("10-K", "A", 1, "2016-12-31", "edgar/data/1/a.txt"),
            FilingIndexEntry("10-K", "B", 2, "2017-01-02", "edgar/data/2/b.txt"),
        ]
        assert set(annual_filers(entries, year=2017)) == {2}


class TestSurvivorshipFunnel:
    def test_unresolvable_ciks_are_counted_not_silently_dropped(self):
        resolved, funnel = build_universe_for_year(
            _entries(), _tickers(), year=2017
        )
        assert funnel.filers > funnel.with_ticker, (
            "fixture should contain filers with no current ticker"
        )
        assert funnel.ticker_attrition > 0
        assert funnel.dropped_no_ticker, "dropped names must be recorded, not discarded"
        assert len(resolved) == funnel.with_ticker

    def test_attrition_is_the_reported_number(self):
        _, funnel = build_universe_for_year(_entries(), _tickers(), year=2017)
        expected = 1.0 - (funnel.with_ticker / funnel.filers)
        assert funnel.ticker_attrition == pytest.approx(expected)

    def test_price_filter_narrows_and_is_recorded(self):
        tickers = _tickers()
        keep_two = set(list(tickers.values())[:2])
        _, funnel = build_universe_for_year(
            _entries(), tickers, year=2017, price_filter=lambda syms: keep_two
        )
        assert funnel.with_prices <= funnel.with_ticker
        assert funnel.with_prices <= 2

    def test_max_names_caps_the_traded_universe(self):
        resolved, funnel = build_universe_for_year(
            _entries(), _tickers(), year=2017, max_names=3
        )
        assert funnel.selected <= 3
        assert len(resolved) == funnel.selected

    def test_empty_year_reports_none_attrition_not_zero(self):
        _, funnel = build_universe_for_year([], _tickers(), year=1999)
        assert funnel.filers == 0
        assert funnel.ticker_attrition is None

    def test_funnel_stages_are_monotonically_narrowing(self):
        _, funnel = build_universe_for_year(
            _entries(), _tickers(), year=2017, max_names=2
        )
        assert funnel.filers >= funnel.with_ticker >= funnel.with_prices >= funnel.selected


class TestFunnelSummary:
    def test_summarises_across_years(self):
        funnels = [
            UniverseFunnel(year=2017, filers=100, with_ticker=40, with_prices=35, selected=20),
            UniverseFunnel(year=2018, filers=120, with_ticker=60, with_prices=50, selected=20),
        ]
        summary = summarize_funnels(funnels)
        assert summary["years"] == 2
        assert summary["total_filer_observations"] == 220
        assert summary["total_selected"] == 40
        assert summary["mean_ticker_attrition"] == pytest.approx((0.6 + 0.5) / 2)
        assert len(summary["by_year"]) == 2

    def test_empty_summary_is_none_not_zero(self):
        summary = summarize_funnels([])
        assert summary["years"] == 0
        assert summary["mean_ticker_attrition"] is None


class TestAttritionIsNotPurelySurvivorship:
    """Documents a limit of the measurement, so it is not over-claimed.

    Filers that cannot be mapped to a ticker are a *mixture*: companies that
    delisted or were acquired, and companies that were never exchange-listed at
    all (OTC issuers, private companies with public debt). The funnel therefore
    **bounds** the survivorship problem rather than isolating it. Separating the
    two needs a historical listing database, which is precisely what C1 says is
    not available for free.
    """

    def test_dropped_names_are_exposed_for_inspection(self):
        _, funnel = build_universe_for_year(_entries(), _tickers(), year=2017)
        assert funnel.dropped_no_ticker
        # Exposed so a reader can judge the mix themselves rather than take
        # the single attrition number at face value.
        assert funnel.as_dict()["example_dropped"]
