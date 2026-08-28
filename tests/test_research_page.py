"""The findings page, and why none of its numbers live in its source.

A hand-written summary of a measured result is a copy, and a copy drifts. This
project's whole argument is that numbers drift when nothing is watching, so the
page that makes that argument publicly cannot itself be a transcription: it is
generated from `evidence/real_run` at build time, and it fails loudly rather
than rendering a stale figure when the export is missing.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_research_page import load, render  # noqa: E402  (needs the path above)

EVIDENCE = ROOT / "evidence" / "real_run"


@pytest.fixture(scope="module")
def page() -> str:
    if not (EVIDENCE / "metrics.json").exists():
        pytest.skip("no exported evidence in this checkout")
    return render(load(EVIDENCE))


@pytest.fixture(scope="module")
def evidence() -> dict:
    if not (EVIDENCE / "metrics.json").exists():
        pytest.skip("no exported evidence in this checkout")
    with (EVIDENCE / "leakage_study.csv").open() as handle:
        ladder = list(csv.DictReader(handle))
    return {
        "metrics": json.loads((EVIDENCE / "metrics.json").read_text()),
        "ladder": ladder,
    }


class TestNothingIsTranscribed:
    def test_the_source_hard_codes_no_result(self):
        """The check that keeps this page honest. A three-decimal literal in the
        generator is a number that stopped tracking the evidence the moment it
        was typed."""
        source = (ROOT / "scripts" / "build_research_page.py").read_text()
        # Strip the CSS block, where decimals are line-heights and opacities.
        code = re.sub(r"<style>.*?</style>", "", source, flags=re.S)
        literals = set(re.findall(r"(?<![\w.\-])0\.\d{3}(?![\w])", code))
        assert not literals, (
            f"{sorted(literals)} are written into the generator; they must be "
            "read from evidence/real_run instead"
        )

    def test_it_refuses_to_render_without_the_export(self, tmp_path):
        """Silently rendering a page with blanks where the findings should be is
        worse than not rendering: the page would still look finished."""
        with pytest.raises(SystemExit, match="make evidence"):
            load(tmp_path)


class TestThePageCarriesTheFindings:
    def test_the_ladder_endpoints_appear(self, page, evidence):
        ladder = evidence["ladder"]
        assert f"{float(ladder[0]['average_precision']):.3f}" in page
        assert f"{float(ladder[-1]['average_precision']):.3f}" in page

    def test_the_headline_carries_its_interval(self, page, evidence):
        m = evidence["metrics"]
        assert f"{m['average_precision']:.3f}" in page
        assert f"{m['average_precision_ci_low']:.3f}" in page
        assert f"{m['average_precision_ci_high']:.3f}" in page

    def test_precision_is_shown_against_its_ceiling(self, page, evidence):
        """The number alone invites reading 19.8% as failure. The ceiling is what
        makes it readable."""
        m = evidence["metrics"]
        assert f"{m['daily_precision_at_5']:.1%}" in page
        assert f"{m['daily_oracle_precision_at_5']:.1%}" in page
        assert f"{m['daily_span_captured_at_5']:.0%}" in page

    def test_the_impossible_entry_count_appears(self, page, evidence):
        naive = evidence["ladder"][0]
        assert f"{int(float(naive['impossible_entries'])):,}" in page

    def test_the_page_states_its_own_limitation(self, page):
        """Everything else on the page is real, which makes the survivorship
        caveat exactly the one a reader would assume away."""
        assert "survivorship" in page.lower() or "survivor" in page.lower()

    def test_it_links_back_into_the_site(self, page):
        assert 'href="index.html"' in page
        assert 'href="report.html"' in page


class TestTheIndexLinksToIt:
    def test_the_entry_points_exist_in_the_renderer(self):
        """A page nobody can reach is not published. The index carries both
        links, in both languages."""
        source = (ROOT / "src" / "company_lens" / "web" / "page.py").read_text()
        assert 'href="research.html"' in source
        assert 'href="earnings.html"' in source
        for key in ("method.research", "method.earnings"):
            assert source.count(f"'{key}'") >= 2, (
                f"{key} needs an English and a Chinese string"
            )
