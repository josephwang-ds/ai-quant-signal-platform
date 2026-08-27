"""The README's own numbers, checked against the repository.

Every count in the README drifted at least once while it was being written --
the test count sat three releases behind, and the stated test-suite size was a
third of the real one. That is the failure this project is about, turned inward:
a number that changes with nothing noticing.

Line counts are checked loosely, because they move with every commit and an exact
assertion would be noise. The test count is checked exactly, because it is a
discrete claim a reader can verify in one command.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text()
LINE_COUNT_TOLERANCE = 0.15


def _line_count(directory: str) -> int:
    files = list((ROOT / directory).rglob("*.py"))
    return sum(len(f.read_text().splitlines()) for f in files)


def _collected_tests() -> int:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(ROOT / "tests"), "--collect-only", "-q"],
        capture_output=True, text=True, cwd=ROOT,
    )
    match = re.search(r"(\d+) tests? collected", result.stdout)
    if match:
        return int(match.group(1))
    # Older pytest prints a per-file tally instead of a total.
    return sum(int(n) for n in re.findall(r"^tests/.*: (\d+)$", result.stdout, re.M))


class TestReadmeCounts:
    def test_test_count_is_current(self):
        stated = {int(n) for n in re.findall(r"(\d+) tests", README)}
        assert stated, "the README no longer states a test count"
        actual = _collected_tests()
        assert stated == {actual}, (
            f"README claims {sorted(stated)} tests; pytest collects {actual}"
        )

    @pytest.mark.parametrize("directory,label", [("src", "src/"), ("tests", "tests")])
    def test_line_counts_are_roughly_right(self, directory, label):
        match = re.search(
            r"About ([\d,]+) lines under `src/`, plus ([\d,]+) of tests", README)
        assert match, "the README no longer states its size"
        stated = int(match.group(1 if directory == "src" else 2).replace(",", ""))
        actual = _line_count(directory)
        drift = abs(stated - actual) / actual
        assert drift <= LINE_COUNT_TOLERANCE, (
            f"README says {stated:,} lines of {label}, the repository has "
            f"{actual:,} ({drift:.0%} off)"
        )


class TestReadmeHonesty:
    """The disclaimers are load-bearing, so their absence should fail a build.

    Not by keyword search: the README mentions "Sharpe ratio" precisely to say
    that none appears, and a test that banned the word would fail on the sentence
    promising the thing it checks for. These assert the statements are present.
    """

    def test_survivorship_limitation_is_stated(self):
        """The caveat a reader is most likely to assume away, because everything
        else on the page is real."""
        assert "survivor sample" in README
        assert "not controlled" in README

    def test_the_no_prediction_claim_is_present(self):
        assert "**Is not:** a return predictor" in README
        assert "Direction is never modelled" in README

    def test_the_synthetic_and_real_paths_are_distinguished(self):
        assert "real EDGAR pull" in README
        assert "synthetic corpus" in README


class TestDocFiguresMatchTheEvidence:
    """The figures in the method docs, checked against the run that produced them.

    These two files fell a whole release behind: the README was rewritten to lead
    with intervals and the anchoring finding while METHODOLOGY described the event
    window with neither, and LEAKAGE quoted the synthetic generator's 80%
    after-hours setting as though it were a measurement of the market.

    Nothing caught it, which is this project's own failure mode aimed at its
    prose. A number in a document is a claim, and a claim that no longer matches
    the artefact behind it is worse than no claim -- a reader has no way to tell.
    """

    EVIDENCE = ROOT / "evidence" / "real_run"

    @pytest.fixture(scope="class")
    @staticmethod
    def evidence():
        import csv
        import json

        root = TestDocFiguresMatchTheEvidence.EVIDENCE
        metrics = json.loads((root / "metrics.json").read_text())
        integrity = json.loads((root / "integrity.json").read_text())
        with (root / "reaction_capture.csv").open() as handle:
            capture = {row["population"]: row for row in csv.DictReader(handle)}
        with (root / "anchoring_study.csv").open() as handle:
            anchoring = list(csv.DictReader(handle))
        with (root / "hyperparameter_sensitivity.csv").open() as handle:
            grid = [float(r["average_precision"]) for r in csv.DictReader(handle)]
        return {"metrics": metrics, "integrity": integrity, "capture": capture,
                "anchoring": anchoring, "grid": grid}

    @staticmethod
    def _doc(name: str) -> str:
        return (ROOT / "docs" / name).read_text()

    def test_the_after_hours_share_is_the_measured_one(self, evidence):
        """80% is the synthetic generator's setting. Quoting it as a fact about
        EDGAR is the specific error this checks for."""
        share = evidence["integrity"]["pre_acceptance_label_share"]
        for name in ("LEAKAGE.md", "METHODOLOGY.md"):
            assert f"{share:.1%}" in self._doc(name), (
                f"docs/{name} no longer states the measured after-hours share "
                f"{share:.1%}"
            )

    def test_the_reaction_capture_figures_are_current(self, evidence):
        capture = evidence["capture"]
        leakage = self._doc("LEAKAGE.md")
        for population in ("all filings", "not material",
                           "material (>= threshold)", "material, accepted post"):
            share = float(capture[population]["median_share_in_open"])
            assert f"{share:.1%}" in leakage, (
                f"LEAKAGE.md no longer states {share:.1%} for '{population}'"
            )

    def test_both_anchorings_are_quoted_together(self, evidence):
        """The open-anchored number read alone says the ranker failed, which is
        not what it means. Neither doc may quote one without the other."""
        closed = evidence["metrics"]["average_precision"]
        opened = float(evidence["anchoring"][1]["average_precision"])
        for name in ("LEAKAGE.md", "METHODOLOGY.md"):
            doc = self._doc(name)
            assert f"{closed:.3f}" in doc and f"{opened:.3f}" in doc, (
                f"docs/{name} must quote both {closed:.3f} and {opened:.3f}"
            )

    def test_the_sensitivity_spread_is_narrower_than_the_interval(self, evidence):
        """The argument only works while this inequality holds. If a rerun ever
        reverses it, the sentence claiming no tuning could have produced the
        headline stops being true and must be rewritten, not re-rounded."""
        metrics = evidence["metrics"]
        spread = max(evidence["grid"]) - min(evidence["grid"])
        interval = (metrics["average_precision_ci_high"]
                    - metrics["average_precision_ci_low"])
        assert spread < interval, (
            f"the grid now spreads {spread:.3f}, wider than the {interval:.3f} "
            "interval; the claim in METHODOLOGY.md and LEAKAGE.md no longer holds"
        )
        for name in ("LEAKAGE.md", "METHODOLOGY.md"):
            doc = self._doc(name)
            assert f"{spread:.3f}" in doc and f"{interval:.3f}" in doc

    def test_the_impossible_entry_count_is_current(self, evidence):
        """The invariant the entry fix is judged on, so it leads LEAKAGE §1."""
        import csv

        with (self.EVIDENCE / "leakage_study.csv").open() as handle:
            naive = next(csv.DictReader(handle))
        count = int(float(naive["impossible_entries"]))
        share = float(naive["impossible_share"])
        leakage = self._doc("LEAKAGE.md")
        assert f"{count:,}" in leakage
        assert f"{share:.1%}" in leakage
