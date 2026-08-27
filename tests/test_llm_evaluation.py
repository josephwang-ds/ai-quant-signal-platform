from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from company_lens.llm import (
    evaluate_provider_run,
    load_grounded_cases,
    load_provider_run,
)
from company_lens.llm.evaluation import _concept_matches

CASES = Path("evidence/llm_eval/cases.json")
RESPONSES = Path("evidence/llm_eval/reference_responses.json")


def test_frozen_bilingual_reference_fixture_passes_pilot_gate() -> None:
    scorecard = evaluate_provider_run(
        load_grounded_cases(CASES), load_provider_run(RESPONSES)
    )

    assert scorecard["fixture_cases"] == 20
    assert scorecard["unique_events"] == 10
    assert scorecard["languages"] == {"Chinese": 10, "English": 10}
    assert scorecard["metrics"]["grounded_pass_rate"] == 1.0
    assert scorecard["metrics"]["material_concept_coverage"] == 1.0
    assert scorecard["metrics"]["citation_precision"] == 1.0
    assert scorecard["metrics"]["numeric_consistency"] == 1.0
    assert scorecard["pilot_gate"]["passed"]
    assert scorecard["evaluation_set_ready"]
    assert not scorecard["production_decision_ready"]
    assert scorecard["operations"]["estimated_cost_usd"] is None
    assert scorecard["operations"]["cost_coverage_rate"] == 0.0


def test_scorecard_rejects_unsupported_citation_number_and_chinese_forecast() -> None:
    cases = load_grounded_cases(CASES)
    run = deepcopy(load_provider_run(RESPONSES))
    claim = run["responses"]["aapl-results-zh"]["output"]["why_it_matters"][0]
    claim["text"] = "股价预计上涨 99%。"
    claim["citations"] = ["invented#citation"]

    scorecard = evaluate_provider_run(cases, run)
    result = next(
        case for case in scorecard["cases"] if case["id"] == "aapl-results-zh"
    )

    assert not result["contract_pass"]
    assert scorecard["metrics"]["grounded_pass_rate"] < 1.0
    assert scorecard["metrics"]["citation_precision"] < 1.0
    assert scorecard["metrics"]["numeric_consistency"] < 1.0
    assert scorecard["metrics"]["advice_violation_rate"] > 0.0
    assert not scorecard["pilot_gate"]["passed"]


def test_concept_matching_handles_reviewed_equivalent_phrasing() -> None:
    assert _concept_matches(
        "The magnitude was small relative to the prior sample.",
        {"id": "historical_context", "any_of": ["historical"]},
    )
    assert _concept_matches(
        "The resignation was not due to a disagreement.",
        {"id": "no_disagreement", "any_of": ["no disagreement"]},
    )
    assert _concept_matches(
        "该协议仍需PSCW批准。",
        {"id": "condition", "any_of": ["仍需 PSCW 批准"]},
    )
    assert not _concept_matches(
        "收入增加为 $157。",
        {"id": "revenue", "any_of": ["$157 million"]},
    )
