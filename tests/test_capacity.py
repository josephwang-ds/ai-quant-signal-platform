"""Reading capacity as a variable, and the reading of precision@k that survives it.

`k` is how many filings someone reads, not how many arrive, and the project
fixed it at five because that was the assumed capacity of the reader it was
written for. That is a product constraint. Quoting one `k` as the headline
promotes it to a scientific one, and the lift is exactly the reading that does
not survive the promotion: on an unchanged model it runs from 2.6x at k=1 to
1.1x at k=20.

The ceiling is the other half. precision@5 cannot be read against 100% -- a
session holding one material filing caps it at 0.2 however good the ranking is,
and a third of eligible sessions hold none at all.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from filing_triage import experiments, pipeline
from filing_triage.config import PipelineConfig
from filing_triage.evaluate import daily_baseline_table

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def scored(world):
    return pipeline.run(world.events, world.prices, world.membership,
                        PipelineConfig(), compute_importance=False,
                        compute_uncertainty=False)


class TestTheCeilingIsReported:
    def test_a_session_cannot_beat_its_own_material_count(self, scored):
        """The invariant the whole ceiling rests on: five slots and one material
        filing is a maximum of 0.2, whatever the ranker does."""
        table = daily_baseline_table(scored.predictions, scored.events, k=5)
        expected = table["material"].clip(upper=5) / 5
        assert np.allclose(table["oracle"], expected)

    def test_no_rule_ever_beats_the_oracle(self, scored):
        table = daily_baseline_table(scored.predictions, scored.events, k=5)
        for rule in ("model", "random", "arrival", "item_202"):
            assert (table[rule] <= table["oracle"] + 1e-9).all(), (
                f"{rule} scored above the achievable ceiling"
            )

    def test_the_ceiling_reaches_the_metrics(self, scored):
        assert "daily_oracle_precision_at_5" in scored.metrics
        assert "daily_span_captured_at_5" in scored.metrics

    def test_span_is_the_model_between_floor_and_ceiling(self, scored):
        m = scored.metrics
        floor, ceiling = m["daily_random_precision_at_5"], m["daily_oracle_precision_at_5"]
        expected = (m["daily_model_precision_at_5"] - floor) / (ceiling - floor)
        assert m["daily_span_captured_at_5"] == pytest.approx(expected)


class TestCapacityIsSwept:
    @pytest.fixture(scope="class")
    @staticmethod
    def profile(scored):
        return experiments.capacity_profile(scored.predictions, scored.events)

    def test_every_capacity_that_has_sessions_is_reported(self, profile):
        assert not profile.empty
        assert profile["capacity_k"].is_monotonic_increasing

    def test_sessions_fall_away_as_capacity_grows(self, profile):
        """A capacity above the day's filing count is reading everything, not
        triage, so those sessions are excluded. This is the real limit on how
        far k can be pushed, and it belongs in the table beside the metric."""
        assert profile["sessions"].is_monotonic_decreasing

    def test_the_ceiling_falls_as_capacity_grows(self, profile):
        """More slots spread over the same material filings, so the achievable
        precision drops -- which is why raw precision@k must not be compared
        across k without it."""
        assert profile["oracle_ceiling"].is_monotonic_decreasing

    def test_the_model_never_exceeds_its_ceiling_at_any_capacity(self, profile):
        assert (profile["model"] <= profile["oracle_ceiling"] + 1e-9).all()

    def test_the_span_moves_less_than_the_lift(self, profile):
        """The claim the sweep exists to support. If this ever reverses, the
        span is no longer the capacity-robust reading and saying so in the
        report becomes false."""
        if len(profile) < 3:
            pytest.skip("too few capacities with sessions on this world")
        lift = profile["lift_vs_random"].dropna()
        span = profile["span_captured"].dropna()
        assert lift.max() - lift.min() > span.max() - span.min()


class TestTheCeilingHasAnExplanation:
    def test_the_material_count_distribution_is_reported(self, scored):
        """A low ceiling reads as a defect until you see that a third of
        sessions simply contain nothing material."""
        counts = experiments.session_material_counts(scored.predictions, scored.events)
        assert not counts.empty
        assert counts["share"].sum() == pytest.approx(1.0)

    def test_the_stated_ceiling_matches_the_distribution(self, scored):
        counts = experiments.session_material_counts(scored.predictions, scored.events)
        implied = float((counts["ceiling_at_k"] * counts["share"]).sum())
        assert implied == pytest.approx(
            scored.metrics["daily_oracle_precision_at_5"], abs=1e-6)

    def test_sessions_with_nothing_material_cap_everyone_at_zero(self, scored):
        counts = experiments.session_material_counts(scored.predictions, scored.events)
        empty = counts[counts["material_filings"] == 0]
        if empty.empty:
            pytest.skip("this world has no empty sessions")
        assert float(empty["ceiling_at_k"].iloc[0]) == 0.0


class TestEmptyInputsDoNotRaise:
    def test_capacity_profile_on_an_empty_frame(self):
        empty = pd.DataFrame(columns=["score", "label", "fold"])
        events = pd.DataFrame(columns=["event_id", "entry_session",
                                       "acceptance_time", "items"])
        assert experiments.capacity_profile(empty, events).empty


class TestTheEvidencePackageIsSelfConsistent:
    """Files in one package must describe one run.

    They stopped doing so the first time the estimator changed: the headline
    metrics were recomputed while the leakage ladder was copied out of
    `data/build`, where it had been left by an earlier run of a different model.
    Both numbers were plausible, they disagreed, and nothing said so -- which is
    the failure mode this project exists to refuse, aimed at its own evidence.
    """

    EVIDENCE = ROOT / "evidence" / "real_run"

    def _has_evidence(self) -> bool:
        return (self.EVIDENCE / "metrics.json").exists()

    def test_the_ladders_honest_rung_matches_the_headline(self):
        import csv
        import json

        if not self._has_evidence():
            pytest.skip("no exported evidence in this checkout")
        metrics = json.loads((self.EVIDENCE / "metrics.json").read_text())
        with (self.EVIDENCE / "leakage_study.csv").open() as handle:
            ladder = list(csv.DictReader(handle))
        honest = float(ladder[-1]["average_precision"])
        assert honest == pytest.approx(metrics["average_precision"], abs=1e-9), (
            "the ladder and the headline metrics come from different runs"
        )

    def test_every_file_the_manifest_lists_exists(self):
        import json

        if not self._has_evidence():
            pytest.skip("no exported evidence in this checkout")
        manifest = json.loads((self.EVIDENCE / "manifest.json").read_text())
        missing = [name for name in manifest["files"]
                   if not (self.EVIDENCE / name).exists()]
        assert not missing, f"manifest lists files that are not there: {missing}"

    def test_the_capacity_sweep_agrees_with_the_headline_at_k5(self):
        import csv
        import json

        if not self._has_evidence():
            pytest.skip("no exported evidence in this checkout")
        metrics = json.loads((self.EVIDENCE / "metrics.json").read_text())
        with (self.EVIDENCE / "capacity_profile.csv").open() as handle:
            row = next(r for r in csv.DictReader(handle) if r["capacity_k"] == "5")
        assert float(row["model"]) == pytest.approx(
            metrics["daily_precision_at_5"], abs=1e-9)
        assert float(row["oracle_ceiling"]) == pytest.approx(
            metrics["daily_oracle_precision_at_5"], abs=1e-9)
