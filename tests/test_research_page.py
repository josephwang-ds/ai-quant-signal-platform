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


@pytest.fixture(scope="module")
def self_relative() -> dict:
    path = EVIDENCE / "self_relative_metrics.json"
    if not path.exists():
        pytest.skip("no issuer-relative export in this checkout")
    return json.loads(path.read_text())


class TestTheIssuerRelativeSectionsCarryTheirEvidence:
    """The second model's results reach the page the same way the first's do:
    read from the export, never typed."""

    def test_the_base_rate_it_has_to_beat_is_shown(self, page, self_relative):
        assert f"{self_relative['target']['base_rate']:.1%}" in page

    def test_the_shipped_calibration_is_marked_as_the_pick(self, page):
        assert "Leave the scores alone" in page
        assert "<em>(shipped)</em>" in page

    def test_the_calibration_error_comes_from_the_export(self, page, self_relative):
        assert f"{self_relative['calibration']['ece']:.3f}" in page

    def test_the_read_now_threshold_is_the_selected_one(self, page, self_relative):
        assert f"{self_relative['recommendation']['read_now_threshold']:.2f}" in page

    def test_abstention_is_described_rather_than_hidden(self, page):
        """An issuer with too little history is told so. A page that showed only
        the states it could score would describe a different product."""
        assert "too short" in page

    def test_it_says_the_target_carries_no_direction(self, page):
        """The one claim on the page that a reader could most damagingly
        misread."""
        assert "direction cannot be recovered" in page


class TestTheTransformerResultIsReportedEitherWay:
    def test_the_ablation_interval_appears_when_it_was_run(self, page):
        if "financial transformer" not in page:
            pytest.skip("no text cache in this checkout")
        with (EVIDENCE / "nlp_feature_ablation.csv").open() as handle:
            rows = {r["group"]: r for r in csv.DictReader(handle)}
        row = rows["transformer_text"]
        assert f"{float(row['diff_ci_low']):+.4f}" in page

    def test_the_section_is_absent_without_a_text_cache(self):
        """The page is generated from evidence; a section describing an encode
        that never happened would be its one hand-written claim."""
        from build_research_page import _transformer_section

        assert _transformer_section({"ablation": [], "metrics": {}}) == ""
        assert _transformer_section(
            {"ablation": [{"group": "transformer_text"}], "metrics": {}}) == ""

    def test_a_partial_issuer_relative_export_fails_loudly(self, tmp_path):
        """Half of it is worse than none: the page would render a calibration
        table beside a policy fitted in a different run."""
        from build_research_page import _self_relative

        (tmp_path / "calibration_comparison.csv").write_text("method\n")
        with pytest.raises(SystemExit, match="partial issuer-relative"):
            _self_relative(tmp_path, lambda name: [])

    def test_no_issuer_relative_export_simply_omits_the_sections(self, tmp_path):
        from build_research_page import _issuer_relative, _self_relative

        assert _self_relative(tmp_path, lambda name: []) == {"self_relative": None}
        assert _issuer_relative({"self_relative": None}) == ""


@pytest.fixture(scope="module")
def volatility() -> dict:
    path = EVIDENCE / "volatility_metrics.json"
    if not path.exists():
        pytest.skip("no volatility export in this checkout")
    return json.loads(path.read_text())


class TestTheVolatilitySectionStatesItsOwnLimits:
    def test_the_horizon_is_named(self, page, volatility):
        assert f"{volatility['task']['horizon']} sessions" in page

    def test_the_shipped_forecaster_is_the_one_that_passed_the_gate(self, page,
                                                                    volatility):
        shipped = volatility["shipped"]
        assert volatility["gates"][shipped]["calibrated"] is True
        assert f"Vs {volatility['reference'].upper()}" in page

    def test_the_foundation_model_result_is_reported_not_omitted(self, page,
                                                                 volatility):
        if "chronos" not in volatility["gates"]:
            pytest.skip("no foundation-model forecasts in this checkout")
        with (EVIDENCE / "volatility_paired.csv").open() as handle:
            paired = {r["forecaster"]: r for r in csv.DictReader(handle)}
        assert f"{float(paired['chronos']['difference']):+.4f}" in page

    def test_the_regime_split_is_shown_not_only_the_average(self, page):
        """A forecaster can hit its nominal coverage overall by being too wide
        when calm and too narrow when turbulent, which is backwards for a risk
        card."""
        assert "turbulent" in page
        assert "widen enough" in page

    def test_it_says_the_forecast_never_reaches_the_ranker(self, page):
        assert "reaches the ranker" in page

    def test_a_partial_volatility_export_fails_loudly(self, tmp_path):
        from build_research_page import _volatility

        (tmp_path / "volatility_paired.csv").write_text("forecaster\n")
        with pytest.raises(SystemExit, match="partial volatility"):
            _volatility(tmp_path, lambda name: [])

    def test_no_volatility_export_omits_the_section(self, tmp_path):
        from build_research_page import _volatility, _volatility_section

        assert _volatility(tmp_path, lambda name: []) == {"volatility": None}
        assert _volatility_section(None) == ""
