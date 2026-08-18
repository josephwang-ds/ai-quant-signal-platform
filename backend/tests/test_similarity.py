"""Year-over-year similarity tests.

The central property: a document compared against a lightly-edited version of
itself must score higher than against a heavily-rewritten one, and the
machinery must refuse the comparisons that would measure something other than
change.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from app.text_signals.section_extraction import extract_risk_factors
from app.text_signals.similarity import (
    CrossCompanyComparisonError,
    TimedDocument,
    pair_consecutive_filings,
    select_point_in_time_corpus,
    year_over_year_similarity,
)

ET = ZoneInfo("America/New_York")
FIXTURES = Path(__file__).parent / "fixtures" / "tenk"

BASE = (
    "The Company faces substantial competition in every market it serves. "
    "Adverse macroeconomic conditions may reduce demand for our products. "
    "Supply chain disruption could impair our ability to manufacture goods. "
    "Regulatory changes in the jurisdictions where we operate may increase "
    "compliance cost and restrict how we design and sell our offerings. "
    "Cybersecurity incidents could compromise confidential information and "
    "damage our reputation with customers and partners. "
) * 12


def _doc(doc_id, symbol, text, day=1, year=2024) -> TimedDocument:
    return TimedDocument(
        doc_id=doc_id,
        symbol=symbol,
        text=text,
        available_at=datetime(year, 11, day, 9, 30, tzinfo=ET),
        fiscal_year=year,
    )


def _corpus() -> list[TimedDocument]:
    """A background corpus so IDF has something to weight against."""
    return [
        _doc(f"bg-{i}", f"SYM{i}", BASE + f" Segment {w} results varied. " * 20)
        for i, w in enumerate(
            ["alpha", "beta", "gamma", "delta", "epsilon", "zeta"], start=1
        )
    ]


class TestSimilarityOrdering:
    """The property that matters: more editing must score as less similar."""

    def test_light_edit_scores_higher_than_heavy_rewrite(self):
        prior = _doc("y0", "AAA", BASE, year=2023)
        light = _doc("y1-light", "AAA", BASE + " We also added one new sentence. ")
        heavy = _doc(
            "y1-heavy",
            "AAA",
            "Entirely different discussion of maritime shipping logistics, "
            "port congestion, container leasing rates and crew availability. " * 12,
        )
        corpus = _corpus() + [prior]

        near = year_over_year_similarity(light, prior, idf_corpus=corpus)
        far = year_over_year_similarity(heavy, prior, idf_corpus=corpus)

        assert near.ok and far.ok
        assert near.cosine_similarity > far.cosine_similarity
        # And the signal moves the other way, which is what the study uses.
        assert near.change_score < far.change_score

    def test_identical_text_is_maximally_similar(self):
        prior = _doc("y0", "AAA", BASE, year=2023)
        same = _doc("y1", "AAA", BASE)
        result = year_over_year_similarity(same, prior, idf_corpus=_corpus() + [prior])
        assert result.cosine_similarity == pytest.approx(1.0, abs=1e-9)
        assert result.change_score == pytest.approx(0.0, abs=1e-9)

    def test_change_score_is_one_minus_cosine(self):
        prior = _doc("y0", "AAA", BASE, year=2023)
        current = _doc("y1", "AAA", BASE + " A modest addition to the disclosure. ")
        r = year_over_year_similarity(current, prior, idf_corpus=_corpus() + [prior])
        assert r.change_score == pytest.approx(1.0 - r.cosine_similarity)


class TestRefusals:
    def test_cross_company_comparison_is_refused(self):
        """A cross-company cosine measures industry, not change."""
        a = _doc("a", "AAA", BASE)
        b = _doc("b", "BBB", BASE, year=2023)
        with pytest.raises(CrossCompanyComparisonError, match="industry vocabulary"):
            year_over_year_similarity(a, b, idf_corpus=_corpus())

    def test_self_comparison_is_refused(self):
        a = _doc("same-id", "AAA", BASE)
        with pytest.raises(ValueError, match="itself"):
            year_over_year_similarity(a, a, idf_corpus=_corpus())

    def test_empty_document_reports_unavailable(self):
        prior = _doc("y0", "AAA", BASE, year=2023)
        empty = _doc("y1", "AAA", "   ")
        r = year_over_year_similarity(empty, prior, idf_corpus=_corpus() + [prior])
        assert not r.ok
        assert "empty" in r.unavailable_reason

    def test_short_document_reports_unavailable_not_zero(self):
        prior = _doc("y0", "AAA", BASE, year=2023)
        stub = _doc("y1", "AAA", "Not applicable.")
        r = year_over_year_similarity(stub, prior, idf_corpus=_corpus() + [prior])
        assert not r.ok
        assert r.cosine_similarity is None
        assert "too short" in r.unavailable_reason

    def test_empty_corpus_reports_unavailable(self):
        prior = _doc("y0", "AAA", BASE, year=2023)
        current = _doc("y1", "AAA", BASE)
        r = year_over_year_similarity(current, prior, idf_corpus=[])
        assert not r.ok
        assert "corpus is empty" in r.unavailable_reason

    def test_disjoint_vocabulary_is_undefined_not_zero(self):
        """A zero vector would report maximal change from a vectorisation failure."""
        corpus = [_doc("c", "SYM", "alpha beta gamma delta epsilon " * 60)]
        prior = _doc("y0", "AAA", "alpha beta gamma delta epsilon " * 60, year=2023)
        current = _doc("y1", "AAA", "zzzqqq wwwvvv yyyxxx uuutttt ssrrqq " * 60)
        r = year_over_year_similarity(current, prior, idf_corpus=corpus)
        assert not r.ok
        assert r.cosine_similarity is None
        assert "all zeros" in r.unavailable_reason


class TestPointInTimeCorpus:
    def test_future_documents_are_excluded(self):
        now = datetime(2024, 11, 1, 9, 30, tzinfo=ET)
        docs = [
            _doc("past", "A", BASE, day=1, year=2023),
            _doc("now", "B", BASE, day=1, year=2024),
            _doc("future", "C", BASE, day=2, year=2024),
        ]
        selected = select_point_in_time_corpus(docs, now)
        ids = {d.doc_id for d in selected}
        assert ids == {"past", "now"}, "a not-yet-available filing leaked into IDF"

    def test_equality_is_admissible(self):
        moment = datetime(2024, 11, 1, 9, 30, tzinfo=ET)
        docs = [_doc("exact", "A", BASE, day=1, year=2024)]
        assert len(select_point_in_time_corpus(docs, moment)) == 1

    def test_naive_as_of_is_rejected(self):
        with pytest.raises(ValueError, match="naive datetime"):
            select_point_in_time_corpus([], datetime(2024, 11, 1))

    def test_idf_leakage_would_change_the_answer(self):
        """Proves the guard is load-bearing, not decorative.

        If future filings are allowed into the IDF fit, term weights move and
        the reported similarity changes. The test asserts the two corpora do
        not agree, which is why the filtering has to happen before the fit.
        """
        prior = _doc("y0", "AAA", BASE, year=2023)
        current = _doc("y1", "AAA", BASE + " Newly added competitive pressure. ")
        as_of = current.available_at

        honest = select_point_in_time_corpus(_corpus() + [prior], as_of)
        leaked = _corpus() + [prior] + [
            _doc("future-1", "ZZZ", "competitive pressure " * 400, day=28, year=2025),
            _doc("future-2", "YYY", "competitive pressure " * 400, day=28, year=2025),
        ]
        assert len(leaked) > len(honest)

        a = year_over_year_similarity(current, prior, idf_corpus=honest)
        b = year_over_year_similarity(current, prior, idf_corpus=leaked)
        assert a.ok and b.ok
        assert a.cosine_similarity != pytest.approx(b.cosine_similarity, abs=1e-12)


class TestPairing:
    def test_pairs_each_filing_with_its_own_predecessor(self):
        docs = [
            _doc("a-2022", "AAA", BASE, year=2022),
            _doc("a-2023", "AAA", BASE, year=2023),
            _doc("a-2024", "AAA", BASE, year=2024),
            _doc("b-2023", "BBB", BASE, year=2023),
            _doc("b-2024", "BBB", BASE, year=2024),
        ]
        pairs = pair_consecutive_filings(docs)
        assert {(c.doc_id, p.doc_id) for c, p in pairs} == {
            ("a-2023", "a-2022"),
            ("a-2024", "a-2023"),
            ("b-2024", "b-2023"),
        }

    def test_never_pairs_across_companies(self):
        docs = [
            _doc("a-2023", "AAA", BASE, year=2023),
            _doc("b-2024", "BBB", BASE, year=2024),
        ]
        assert pair_consecutive_filings(docs) == []

    def test_single_filing_yields_no_pair(self):
        assert pair_consecutive_filings([_doc("only", "AAA", BASE)]) == []


class TestRealFilings:
    def test_apple_against_microsoft_risk_factors_is_refused(self):
        """Even on real text, cross-company is a refusal rather than a number."""
        aapl = extract_risk_factors(
            (FIXTURES / "aapl-10k-2023.htm").read_text(encoding="utf-8", errors="replace")
        )
        msft = extract_risk_factors(
            (FIXTURES / "msft-10k-2023.htm").read_text(encoding="utf-8", errors="replace")
        )
        assert aapl.ok and msft.ok

        a = _doc("aapl-2023", "AAPL", aapl.text)
        m = _doc("msft-2023", "MSFT", msft.text, year=2023)
        with pytest.raises(CrossCompanyComparisonError):
            year_over_year_similarity(a, m, idf_corpus=[a, m])

    def test_real_section_compares_against_its_own_edit(self):
        """End to end: real HTML -> extracted section -> similarity."""
        extracted = extract_risk_factors(
            (FIXTURES / "aapl-10k-2023.htm").read_text(encoding="utf-8", errors="replace")
        )
        assert extracted.ok
        prior = _doc("aapl-2022", "AAPL", extracted.text, year=2022)
        current = _doc(
            "aapl-2023",
            "AAPL",
            extracted.text + " The Company added a new paragraph about supply "
            "concentration and single source component availability. ",
        )
        msft = extract_risk_factors(
            (FIXTURES / "msft-10k-2023.htm").read_text(encoding="utf-8", errors="replace")
        )
        corpus = [prior, _doc("msft", "MSFT", msft.text, year=2022)]

        result = year_over_year_similarity(current, prior, idf_corpus=corpus)
        assert result.ok, result.unavailable_reason
        # Nearly identical, but demonstrably not flagged as unchanged.
        assert 0.9 < result.cosine_similarity < 1.0
        assert result.change_score > 0.0
