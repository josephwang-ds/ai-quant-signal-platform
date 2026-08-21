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
        ["python", "-m", "pytest", str(ROOT / "tests"), "--collect-only", "-q"],
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
