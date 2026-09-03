"""The README's one picture, and the two ways a chart lies.

It lies by drifting -- which is why this one is generated from the evidence rather
than screenshotted -- and it lies by labelling a bar with the wrong stage. The
second is easy to do and invisible afterwards, so the mapping is checked against
the file it renames.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_ladder_chart import STAGE_WORDS, load, render  # noqa: E402

LADDER = ROOT / "evidence" / "real_run" / "leakage_study.csv"


@pytest.fixture(scope="module")
def rows():
    if not LADDER.exists():
        pytest.skip("no exported evidence in this checkout")
    return load(LADDER)


class TestEveryStageIsRenamed:
    def test_the_plain_names_cover_every_row(self, rows):
        """An unmapped stage falls through to the CSV's own wording, which is
        written for someone who already knows what purged cross-validation is."""
        missing = [r["stage"] for r in rows if r["stage"] not in STAGE_WORDS]
        assert not missing, f"{missing} would render as raw pipeline vocabulary"

    def test_no_plain_name_is_stale(self, rows):
        """The other direction: a rename left behind after the stage it renamed
        was renamed itself."""
        stages = {r["stage"] for r in rows}
        assert not set(STAGE_WORDS) - stages


class TestTheNumbersComeFromTheEvidence:
    def test_every_score_is_drawn(self, rows):
        svg = render(rows)
        for row in rows:
            assert f"{float(row['average_precision']):.3f}" in svg

    def test_the_impossible_entry_counts_are_drawn(self, rows):
        svg = render(rows)
        for row in rows:
            assert f"{int(float(row['impossible_entries'])):,}" in svg

    def test_the_generator_hard_codes_no_result(self):
        source = (ROOT / "scripts" / "build_ladder_chart.py").read_text()
        code = re.sub(r"<style>.*?</style>", "", source, flags=re.S)
        assert not set(re.findall(r"(?<![\w.\-])0\.\d{3}(?![\w])", code))

    def test_the_committed_chart_matches_the_evidence(self, rows):
        """The file in the repository is what GitHub renders. If it has drifted
        from the evidence, the README is showing a stale picture."""
        chart = ROOT / "docs" / "leakage-ladder.svg"
        if not chart.exists():
            pytest.skip("chart not generated in this checkout")
        assert chart.read_text() == render(rows)


class TestItIsReadableWithoutSeeingIt:
    def test_the_alt_text_carries_both_findings(self, rows):
        svg = render(rows)
        label = re.search(r'aria-label="([^"]+)"', svg).group(1)
        assert f"{float(rows[0]['average_precision']):.3f}" in label
        assert f"{int(float(rows[-1]['impossible_entries'])):,}" in label

    def test_it_carries_its_own_styles_and_no_network_requests(self, rows):
        """GitHub renders README images in a sandbox that blocks external
        fetches, so a chart depending on one renders unstyled."""
        svg = render(rows)
        assert "<style>" in svg
        assert "http://" not in svg.replace("http://www.w3.org/2000/svg", "")

    def test_it_is_legible_in_dark_mode(self, rows):
        assert "prefers-color-scheme: dark" in render(rows)
