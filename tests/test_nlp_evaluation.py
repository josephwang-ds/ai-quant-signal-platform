from __future__ import annotations

from pathlib import Path

from company_lens.nlp import evaluate_change_cases, load_change_cases


def test_labeled_change_fixture_is_reproducible() -> None:
    cases = load_change_cases(Path("evidence/nlp_eval/change_cases.json"))

    metrics = evaluate_change_cases(cases)

    assert metrics["fixture_cases"] == 4
    assert metrics["overall"]["precision"] == 1.0
    assert metrics["overall"]["recall"] == 1.0
    assert metrics["overall"]["f1"] == 1.0
    assert all(result["matched"] == result["expected"] for result in metrics["cases"])
