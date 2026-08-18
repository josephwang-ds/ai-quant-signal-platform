"""Item 1A extraction tests.

Runs offline against trimmed-but-real 10-K documents in
``tests/fixtures/tenk``. The trimming removed the middle of the risk prose and
everything after Item 1B; every structural trap the extractor exists to survive
was deliberately preserved:

* the table-of-contents entry,
* mid-sentence cross-references ("...Part I, Item 1A of this Form 10-K..."),
* running page headers repeating the item label,
* the real heading and the Item 1B boundary.

The disambiguation logic was also verified against the full untrimmed filings
(1.5 MB Apple, 10 MB Microsoft) during development; the fixtures keep that
coverage affordable to commit.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.text_signals.section_extraction import (
    MIN_SECTION_CHARS,
    extract_item_section,
    extract_risk_factors,
    html_to_text,
)

FIXTURES = Path(__file__).parent / "fixtures" / "tenk"
AAPL = FIXTURES / "aapl-10k-2023.htm"
MSFT = FIXTURES / "msft-10k-2023.htm"


def _markup(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


class TestHtmlToText:
    def test_block_tags_become_line_breaks(self):
        """Without this, adjacent table cells fuse into 'Item 1A.Risk Factors'."""
        text = html_to_text("<table><tr><td>Item 1A.</td><td>Risk Factors</td></tr></table>")
        assert "Item 1A." in text
        assert "Risk Factors" in text
        assert "1A.Risk" not in text

    def test_non_breaking_spaces_are_normalised(self):
        """EDGAR HTML is full of &nbsp;; leaving them breaks every \\s regex."""
        text = html_to_text("<p>Item&nbsp;1A.&nbsp;&nbsp;Risk&nbsp;Factors</p>")
        assert "\xa0" not in text
        assert "Item 1A. Risk Factors" in text

    def test_script_and_style_content_is_dropped(self):
        text = html_to_text(
            "<div><script>var x='Item 1A. Risk Factors';</script>"
            "<style>.a{}</style><p>Real body</p></div>"
        )
        assert "var x" not in text
        assert "Real body" in text

    def test_entities_are_decoded(self):
        assert "AT&T" in html_to_text("<p>AT&amp;T</p>")

    def test_real_filings_flatten_to_substantial_text(self):
        for path in (AAPL, MSFT):
            text = html_to_text(_markup(path))
            assert len(text) > 10_000, path.name
            assert "\xa0" not in text


class TestRealFilings:
    @pytest.mark.parametrize("path", [AAPL, MSFT], ids=["aapl", "msft"])
    def test_extracts_a_substantial_risk_factors_body(self, path):
        result = extract_risk_factors(_markup(path))
        assert result.ok, result.unavailable_reason
        assert result.char_count > MIN_SECTION_CHARS
        assert result.terminator in {"1B", "1C", "2"}

    @pytest.mark.parametrize("path", [AAPL, MSFT], ids=["aapl", "msft"])
    def test_body_starts_at_the_heading_not_the_contents(self, path):
        result = extract_risk_factors(_markup(path))
        head = result.text[:120].lower()
        assert "item 1a" in head
        # A table-of-contents entry is followed by a page number and the next
        # item within a few characters; a body is followed by prose.
        assert "unresolved staff comments" not in head

    @pytest.mark.parametrize("path", [AAPL, MSFT], ids=["aapl", "msft"])
    def test_body_stops_before_the_next_item(self, path):
        """The clearest boundary check: Item 1B's own title must not appear."""
        result = extract_risk_factors(_markup(path))
        assert "unresolved staff comments" not in result.text.lower()

    def test_multiple_decoys_were_actually_present(self):
        """Guards the guard: if the fixtures lost their decoys the tests are hollow."""
        for path in (AAPL, MSFT):
            text = html_to_text(_markup(path))
            occurrences = text.lower().count("item 1a")
            assert occurrences >= 2, f"{path.name} has only {occurrences} 'Item 1A'"

    def test_reported_offsets_reproduce_the_body(self):
        result = extract_risk_factors(_markup(AAPL))
        text = html_to_text(_markup(AAPL))
        assert text[result.start_offset : result.end_offset].strip() == result.text


class TestDisambiguation:
    """Synthetic documents isolating one decoy class each."""

    def _doc(self, body: str) -> str:
        return f"<html><body>{body}</body></html>"

    def test_table_of_contents_entry_is_not_chosen(self):
        markup = self._doc(
            "<p>TABLE OF CONTENTS</p>"
            "<p>Item 1. Business 1</p>"
            "<p>Item 1A. Risk Factors 5</p>"
            "<p>Item 1B. Unresolved Staff Comments 16</p>"
            "<p>Item 1A. Risk Factors</p>"
            f"<p>{'Genuine risk disclosure prose. ' * 200}</p>"
            "<p>Item 1B. Unresolved Staff Comments</p>"
            "<p>None.</p>"
        )
        result = extract_risk_factors(markup)
        assert result.ok
        assert "Genuine risk disclosure prose." in result.text
        assert result.char_count > MIN_SECTION_CHARS

    def test_mid_sentence_cross_reference_is_not_chosen(self):
        markup = self._doc(
            "<p>Results may differ; see Part I, Item 1A of this Form 10-K under "
            "the heading Risk Factors for details.</p>"
            "<p>Item 1A. Risk Factors</p>"
            f"<p>{'Actual disclosure text. ' * 200}</p>"
            "<p>Item 1B. Unresolved Staff Comments</p>"
        )
        result = extract_risk_factors(markup)
        assert result.ok
        assert result.text.lower().startswith("item 1a")
        assert "Results may differ" not in result.text

    def test_running_page_headers_do_not_truncate_the_section(self):
        """Microsoft's filing repeats the label atop every page of the section."""
        pages = "".join(
            f"<p>Item 1A</p><p>{'Risk prose for page %d. ' % i * 40}</p>"
            for i in range(1, 6)
        )
        markup = self._doc(
            "<p>Item 1A. Risk Factors 23</p>"
            "<p>Item 1A. RISK FACTORS</p>"
            f"{pages}"
            "<p>Item 1B. Unresolved Staff Comments</p>"
        )
        result = extract_risk_factors(markup)
        assert result.ok
        # All five pages survive — the section was not cut at a running header.
        for i in range(1, 6):
            assert f"Risk prose for page {i}." in result.text

    def test_falls_back_to_item_2_when_1b_is_absent(self):
        markup = self._doc(
            "<p>Item 1A. Risk Factors</p>"
            f"<p>{'Disclosure. ' * 300}</p>"
            "<p>Item 2. Properties</p>"
        )
        result = extract_risk_factors(markup)
        assert result.ok
        assert result.terminator == "2"
        assert "Properties" not in result.text


class TestHonestFailure:
    """A missing section stays missing; it never becomes the whole document."""

    def test_absent_item_reports_unavailable(self):
        result = extract_risk_factors("<html><body><p>Item 1. Business</p></body></html>")
        assert not result.ok
        assert result.text is None
        assert "no heading-position match" in result.unavailable_reason

    def test_not_applicable_stub_is_rejected_with_its_length(self):
        markup = "<html><body><p>Item 1A. Risk Factors</p><p>Not applicable.</p>" \
                 "<p>Item 1B. Unresolved Staff Comments</p></body></html>"
        result = extract_risk_factors(markup)
        assert not result.ok
        assert result.text is None
        assert "below the" in result.unavailable_reason
        assert result.char_count > 0  # reports what it did find

    def test_empty_document(self):
        result = extract_risk_factors("")
        assert not result.ok
        assert result.unavailable_reason == "empty document text"

    def test_toc_only_document_does_not_return_the_contents(self):
        markup = "<html><body><p>Item 1A. Risk Factors 5</p>" \
                 "<p>Item 1B. Unresolved Staff Comments 16</p></body></html>"
        result = extract_risk_factors(markup)
        assert not result.ok


class TestOtherItems:
    def test_extracts_item_7_when_asked(self):
        markup = (
            "<html><body><p>Item 7. Management's Discussion and Analysis</p>"
            f"<p>{'MD&A prose. ' * 300}</p>"
            "<p>Item 8. Financial Statements</p></body></html>"
        )
        result = extract_item_section(
            html_to_text(markup),
            item="7",
            expected_title="management",
            terminators=("7A", "8"),
        )
        assert result.ok
        assert "MD&A prose." in result.text
        assert result.terminator == "8"
