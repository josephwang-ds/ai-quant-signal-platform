"""Intervals, and the two ways of computing them that would be wrong here.

The project argues that a flattering number deserves suspicion. A number with no
error bar is the same problem one level up, so these pin down that the intervals
exist, that they resample the session rather than the row, and that the baseline
comparison stays paired.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from filing_triage import cli, experiments, pipeline, report
from filing_triage.candidates import CANDIDATES, build, sensitivity_grid
from filing_triage.config import PipelineConfig
from filing_triage.uncertainty import (
    bootstrap_daily_comparisons,
    bootstrap_ranking_metrics,
    stage_deltas,
)


@pytest.fixture(scope="module")
def scored(world):
    return pipeline.run(world.events, world.prices, world.membership,
                        PipelineConfig(), compute_importance=False)


class TestRankingIntervals:
    def test_the_headline_metrics_arrive_with_intervals(self, scored):
        for metric in ("average_precision", "roc_auc"):
            point = scored.metrics[metric]
            low = scored.metrics[f"{metric}_ci_low"]
            high = scored.metrics[f"{metric}_ci_high"]
            assert low < point < high, f"{metric} point estimate outside its interval"
            assert 0.0 <= low < high <= 1.0

    def test_the_bootstrap_resamples_sessions_not_rows(self):
        """The interval must widen when outcomes really are clustered by day.

        Constructed rather than measured on the corpus, because on this data the
        correction is nearly invisible -- the label is a market-model residual,
        so the common factor that would drive same-day correlation is already
        subtracted. That makes the real sample a bad test of whether the cluster
        bootstrap is wired up: both methods agree there precisely because there
        is little clustering left to find. Here every session is internally
        identical, so a row bootstrap cannot see the structure and a session
        bootstrap must.
        """
        rng = np.random.default_rng(0)
        rows = []
        for session in range(60):
            # Whole days are material or not. Nothing varies within one, so the
            # base rate a resample sees is decided entirely by which *days* it
            # draws -- 60 coin flips for the session bootstrap, and effectively
            # none for the row bootstrap, which reconstructs the same mix every
            # time out of 1,200 rows.
            label = int(rng.random() < 0.3)
            for _ in range(20):
                # Overlapping distributions on purpose: perfectly separable
                # scores pin average precision at 1.0 and neither method can
                # show any spread at all.
                rows.append({"session": f"d{session:03d}", "label": label,
                             "score": 0.3 * label + rng.normal(0, 0.4)})
        frame = pd.DataFrame(rows)
        predictions = frame[["label", "score"]]
        sessions = frame["session"]

        clustered = bootstrap_ranking_metrics(predictions, sessions,
                                              n_boot=400, seed=1)
        clustered_width = (clustered["average_precision_ci_high"]
                           - clustered["average_precision_ci_low"])

        from sklearn.metrics import average_precision_score
        rng = np.random.default_rng(1)
        naive = []
        for _ in range(400):
            sample = predictions.iloc[rng.integers(0, len(predictions),
                                                   len(predictions))]
            if sample["label"].nunique() < 2:
                continue
            naive.append(average_precision_score(sample["label"], sample["score"]))
        naive_width = float(np.percentile(naive, 97.5) - np.percentile(naive, 2.5))

        assert clustered_width > 2 * naive_width

    def test_it_reports_how_many_sessions_and_draws_it_used(self, scored):
        assert scored.metrics["bootstrap_draws"] > 0
        assert scored.metrics["bootstrap_sessions"] > 1

    def test_a_single_session_cannot_be_bootstrapped(self, scored):
        one = scored.predictions.head(5)
        sessions = pd.Series("2024-01-02", index=one.index)
        assert bootstrap_ranking_metrics(one, sessions, n_boot=10) == {}


class TestPairedBaselineComparison:
    def test_every_baseline_gets_a_difference_and_a_lift_interval(self, scored):
        table = scored.baseline_comparisons
        assert set(table["baseline"]) == {"random", "arrival", "item_202"}
        for row in table.itertuples():
            assert row.difference_ci_low < row.difference < row.difference_ci_high
            assert row.lift_ci_low < row.lift < row.lift_ci_high
            assert 0.0 <= row.draws_not_beating_baseline <= 1.0

    def test_the_comparison_is_paired_on_the_same_resample(self, scored):
        """Model and baseline see the same sessions, so the draw must be shared.

        Bootstrapping the two means independently discards that pairing and
        widens the interval on their difference for no reason. Reusing one
        resample of sessions across every rule is what keeps it honest, and an
        unpaired interval is detectably wider.
        """
        paired = bootstrap_daily_comparisons(scored.predictions, scored.events,
                                             n_boot=400, seed=5)
        random_row = paired[paired["baseline"] == "random"].iloc[0]
        paired_width = random_row.difference_ci_high - random_row.difference_ci_low

        from filing_triage.evaluate import daily_baseline_table
        table = daily_baseline_table(scored.predictions, scored.events, 5)
        rng = np.random.default_rng(5)
        model = table["model"].to_numpy()
        baseline = table["random"].to_numpy()
        unpaired = np.array([
            model[rng.integers(0, len(table), len(table))].mean()
            - baseline[rng.integers(0, len(table), len(table))].mean()
            for _ in range(400)
        ])
        unpaired_width = float(np.percentile(unpaired, 97.5)
                               - np.percentile(unpaired, 2.5))
        assert paired_width < unpaired_width

    def test_all_rules_are_scored_on_one_shared_session_table(self, scored):
        """The aggregate and the bootstrap must count the same sessions."""
        table = scored.baseline_comparisons
        assert table["sessions"].nunique() == 1
        assert table["model_precision"].nunique() == 1


class TestLadderDeltasCarryNoInterval:
    def test_stage_deltas_are_differences_without_intervals(self, world):
        study = experiments.run_leakage_study(world.events, world.prices,
                                              world.membership)
        deltas = stage_deltas(study)
        assert "average_precision_delta" in deltas.columns
        assert pd.isna(deltas["average_precision_delta"].iloc[0])
        # Deliberately absent: consecutive rungs measure overlapping but
        # different event populations, so a paired interval over them would be
        # rigorous-looking nonsense.
        assert not any(c.endswith("_ci_low") for c in deltas.columns)


class TestHyperparameterProvenance:
    def test_overrides_reach_the_estimator(self, world):
        result = pipeline.run(world.events, world.prices, world.membership,
                              PipelineConfig(), compute_importance=False,
                              compute_uncertainty=False,
                              estimator_overrides={"max_depth": 2})
        assert result.metrics["n_events"] > 0

    def test_the_shipped_pipeline_sets_no_overrides(self, world):
        from filing_triage.model import TriageModel
        assert TriageModel(PipelineConfig()).estimator_overrides is None

    @pytest.mark.parametrize("family", sorted(CANDIDATES))
    def test_the_grid_perturbs_one_setting_at_a_time(self, family):
        for overrides in sensitivity_grid(family):
            assert len(overrides) <= 1, (
                f"{family} grid entry {overrides} moves more than one setting, "
                "so a movement in the metric cannot be attributed to either"
            )

    @pytest.mark.parametrize("family", sorted(CANDIDATES))
    def test_every_family_grid_starts_from_its_own_defaults(self, family):
        assert sensitivity_grid(family)[0] == {}

    def test_the_grid_follows_the_configured_family(self):
        """A grid frozen to a previous default still runs and still prints a
        reassuring spread -- while perturbing parameters the current estimator
        does not have. A sensitivity study that has silently stopped testing
        anything is worse than none, because it reads as evidence."""
        configured = PipelineConfig().estimator
        settings = {k for entry in sensitivity_grid(configured) for k in entry}
        valid = build(configured).named_steps["clf"].get_params()
        assert settings, f"no grid defined for the configured family {configured!r}"
        assert settings <= set(valid), (
            f"{sorted(settings - set(valid))} are not parameters of {configured}"
        )

    def test_sensitivity_reports_one_row_per_setting(self, world):
        grid = [{}, {"max_depth": 2}]
        table = experiments.hyperparameter_sensitivity(
            world.events, world.prices, world.membership, grid=grid)
        assert list(table["setting"]) == ["defaults", "max_depth=2"]
        assert table["average_precision"].notna().all()


class TestIntervalsReachTheReader:
    """The interval has to arrive on the surfaces a reader actually looks at.

    Computing it and then quoting the point estimate anyway is the same failure
    the module docstring describes, moved one step later in the pipeline: the
    number a reader is asked to believe would still be a claim with its error
    bar deleted. So these check the two places the number is published -- the
    CLI summary and the HTML report -- rather than only the dict it came from.
    """

    def test_the_cli_summary_prints_the_ranking_intervals(self, scored):
        printed = dict(cli._headline(scored.metrics, scored.baseline_comparisons))
        low = scored.metrics["average_precision_ci_low"]
        assert f"{low:.3f}" in printed["average precision"]
        assert f"{scored.metrics['roc_auc_ci_low']:.3f}" in printed["ROC AUC"]

    def test_the_paired_lift_reads_as_a_lift_and_a_range(self, scored):
        rendered = cli._paired_lift(scored.baseline_comparisons, "random")
        random = scored.baseline_comparisons.set_index("baseline").loc["random"]
        assert rendered.startswith(f"{random['lift']:.2f}x")
        assert f"[{random['lift_ci_low']:.2f}, {random['lift_ci_high']:.2f}]" in rendered

    def test_the_cli_queue_rows_carry_the_paired_interval(self, scored):
        """The shared fixture world has too few crowded sessions for the queue
        metric to be reported at all, so the eligibility flag is forced here --
        what is under test is the rendering of those rows, not the rule that
        decides whether they appear."""
        usable = {**scored.metrics, "daily_usable_at_5": True}
        printed = dict(cli._headline(usable, scored.baseline_comparisons))
        random = scored.baseline_comparisons.set_index("baseline").loc["random"]
        assert f"[{random['lift_ci_low']:.2f}," in printed["lift vs matched random @5"]
        assert "model" in printed["arrival-order precision @5"]

    def test_a_run_without_the_bootstrap_prints_no_placeholder(self, world):
        """The studies score the pipeline with uncertainty off, and a rendered
        `[nan, nan]` there would read as a computation that failed rather than
        one deliberately skipped."""
        bare = pipeline.run(world.events, world.prices, world.membership,
                            PipelineConfig(), compute_importance=False,
                            compute_uncertainty=False)
        printed = dict(cli._headline(bare.metrics, bare.baseline_comparisons))
        assert "nan" not in " ".join(printed.values()).lower()
        assert "[" not in printed["average precision"]

    def test_the_report_baseline_table_carries_lifts_and_intervals(self, scored):
        table = report._baseline_table(scored.metrics, scored.baseline_comparisons)
        random = scored.baseline_comparisons.set_index("baseline").loc["random"]
        assert f"{random['lift']:.2f}&times;" in table
        assert f"[{random['lift_ci_low']:.2f}, {random['lift_ci_high']:.2f}]" in table
        assert "Draws favouring it" in table

    def test_the_report_baseline_table_counts_draws_out_of_the_total(self, scored):
        """A share is harder to read than a count, and the count is the claim:
        `0 / 2000` says how much resampling the comparison survived."""
        table = report._baseline_table(scored.metrics, scored.baseline_comparisons)
        assert f"/ {scored.metrics['bootstrap_draws']:,}" in table

    def test_the_report_tiles_carry_the_interval(self, scored):
        tiles = report._stat_row(scored.metrics, 0.6, scored.baseline_comparisons)
        assert f"95% [{scored.metrics['average_precision_ci_low']:.3f}," in tiles
        assert f"95% [{scored.metrics['roc_auc_ci_low']:.3f}," in tiles

    def test_the_report_renders_without_a_bootstrap(self, world):
        bare = pipeline.run(world.events, world.prices, world.membership,
                            PipelineConfig(), compute_importance=False,
                            compute_uncertainty=False)
        table = report._baseline_table(bare.metrics, bare.baseline_comparisons)
        assert "nan" not in table.lower()
        assert "&mdash;" in table
