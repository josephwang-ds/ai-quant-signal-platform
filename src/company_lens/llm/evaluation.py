"""Reproducible scorecard for frozen grounded-explanation cases."""

from __future__ import annotations

import json
import re
from pathlib import Path
from statistics import median
from typing import Any

from company_lens.llm.grounded import (
    CLAIM_SECTIONS,
    NUMBER_LITERAL,
    UNSUPPORTED_PATTERNS,
    localized_month_number_literals,
    validate_grounded_explanation,
)

CONCEPT_PATTERNS = {
    "historical_context": (
        re.compile(r"\b(?:historical|prior\s+(?:sample|observations?))\b", re.IGNORECASE),
        re.compile(r"(?:历史|此前\s*\d*\s*个?\s*样本)"),
    ),
    "no_disagreement": (
        re.compile(
            r"\b(?:no\s+disagreement|not\s+(?:the\s+result\s+of|due\s+to)\s+"
            r"(?:any\s+)?(?:a\s+)?disagreement)\b",
            re.IGNORECASE,
        ),
        re.compile(r"(?:并非源于.{0,20}分歧|没有分歧)"),
    ),
}

PILOT_THRESHOLDS = {
    "grounded_pass_rate": 1.0,
    "material_concept_coverage": 0.8,
    "claim_citation_rate": 1.0,
    "citation_precision": 1.0,
    "numeric_consistency": 1.0,
    "advice_violation_rate": 0.0,
}


def load_grounded_cases(path: str | Path) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    cases = payload.get("cases") if isinstance(payload, dict) else None
    if not isinstance(cases, list):
        raise TypeError("grounded evaluation fixture must contain a cases list")
    expanded = [_prepare_case(case) for case in cases]
    for pair in payload.get("paired_cases", []):
        for code, language in (("en", "English"), ("zh", "Chinese")):
            expanded.append(
                _prepare_case(
                    {
                        "id": f"{pair['id']}-{code}",
                        "event_id": pair["id"],
                        "language": language,
                        "depth": pair.get("depth", "beginner"),
                        "evidence": pair["evidence"],
                        "allowed_citations": pair["allowed_citations"],
                        "allowed_number_literals": pair["allowed_number_literals"],
                        "expected_concepts": pair["expected_concepts"][code],
                        "minimum_concept_coverage": pair.get(
                            "minimum_concept_coverage", 0.8
                        ),
                    }
                )
            )
    return expanded


def load_provider_run(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("responses"), dict):
        raise TypeError("provider run must contain a responses object")
    responses = dict(payload["responses"])
    for pair_id, pair in payload.get("paired_responses", {}).items():
        for code in ("en", "zh"):
            responses[f"{pair_id}-{code}"] = {"output": pair[code]}
    payload["responses"] = responses
    return payload


def evaluate_provider_run(
    cases: list[dict[str, Any]],
    run: dict[str, Any],
    *,
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Score one provider run against the same frozen evidence and review labels."""
    thresholds = thresholds or PILOT_THRESHOLDS
    responses = run.get("responses", {})
    case_results = []
    cited_claims = claim_count = supported_citations = citation_count = 0
    supported_numbers = number_count = advice_violations = 0
    concepts_matched = concept_count = contract_passes = grounded_passes = 0
    latencies: list[float] = []
    input_tokens = output_tokens = 0
    estimated_cost = 0.0
    cost_records = 0

    for case in cases:
        response_record = responses.get(case["id"], {})
        output = response_record.get("output", {}) if isinstance(response_record, dict) else {}
        allowed_citations = set(case["allowed_citations"])
        allowed_numbers = set(case["allowed_number_literals"])
        validation = validate_grounded_explanation(
            output,
            allowed_citations=allowed_citations,
            allowed_number_literals=allowed_numbers,
        )
        contract_passes += int(validation.ok)

        claims = _claims(output)
        required_claims = [claim for section, claim in claims if section != "uncertainties"]
        claim_count += len(required_claims)
        cited_claims += sum(bool(claim.get("citations")) for claim in required_claims)
        emitted_citations = [
            citation
            for _, claim in claims
            for citation in claim.get("citations", [])
            if isinstance(citation, str)
        ]
        citation_count += len(emitted_citations)
        supported_citations += sum(citation in allowed_citations for citation in emitted_citations)

        text = " ".join(
            claim.get("text", "")
            for _, claim in claims
            if isinstance(claim.get("text"), str)
        )
        emitted_numbers = NUMBER_LITERAL.findall(text)
        number_count += len(emitted_numbers)
        supported_numbers += sum(number in allowed_numbers for number in emitted_numbers)
        case_advice = any(
            any(pattern.search(claim.get("text", "")) for pattern in UNSUPPORTED_PATTERNS)
            for _, claim in claims
            if isinstance(claim.get("text"), str)
        )
        advice_violations += int(case_advice)

        expected = case.get("expected_concepts", [])
        matched = sum(_concept_matches(text, concept) for concept in expected)
        concept_count += len(expected)
        concepts_matched += matched
        coverage = _rate(matched, len(expected))
        minimum_coverage = float(case.get("minimum_concept_coverage", 0.8))
        grounded = validation.ok and coverage >= minimum_coverage
        grounded_passes += int(grounded)

        latency = response_record.get("latency_ms") if isinstance(response_record, dict) else None
        if isinstance(latency, (int, float)):
            latencies.append(float(latency))
        usage = response_record.get("usage", {}) if isinstance(response_record, dict) else {}
        input_tokens += int(usage.get("input_tokens", 0))
        output_tokens += int(usage.get("output_tokens", 0))
        recorded_cost = response_record.get("estimated_cost_usd")
        if isinstance(recorded_cost, (int, float)):
            estimated_cost += float(recorded_cost)
            cost_records += 1
        case_results.append(
            {
                "id": case["id"],
                "language": case["language"],
                "contract_pass": validation.ok,
                "concept_coverage": coverage,
                "grounded_pass": grounded,
                "errors": list(validation.errors),
            }
        )

    metrics = {
        "grounded_pass_rate": _rate(grounded_passes, len(cases)),
        "contract_pass_rate": _rate(contract_passes, len(cases)),
        "material_concept_coverage": _rate(concepts_matched, concept_count),
        "claim_citation_rate": _rate(cited_claims, claim_count),
        "citation_precision": _rate(supported_citations, citation_count),
        "numeric_consistency": _rate(supported_numbers, number_count),
        "advice_violation_rate": _rate(advice_violations, len(cases)),
        "fallback_or_missing_rate": _rate(
            sum(not _is_grounded_record(responses.get(case["id"])) for case in cases),
            len(cases),
        ),
    }
    gate_checks = {
        metric: (
            value <= threshold
            if metric == "advice_violation_rate"
            else value >= threshold
        )
        for metric, threshold in thresholds.items()
        for value in [metrics[metric]]
    }
    languages = dict.fromkeys(sorted({case["language"] for case in cases}), 0)
    for case in cases:
        languages[case["language"]] += 1
    unique_events = {
        case.get("event_id", case["id"].removesuffix("-en").removesuffix("-zh"))
        for case in cases
    }
    evaluation_set_ready = (
        len(cases) >= 20
        and len(unique_events) >= 10
        and all(count >= 8 for count in languages.values())
    )
    return {
        "schema_version": "company-lens.llm-eval.v1",
        "provider": run.get("provider", "unknown"),
        "model": run.get("model", "unknown"),
        "fixture_cases": len(cases),
        "unique_events": len(unique_events),
        "languages": languages,
        "metrics": metrics,
        "pilot_gate": {
            "thresholds": thresholds,
            "checks": gate_checks,
            "passed": all(gate_checks.values()),
        },
        "evaluation_set_ready": evaluation_set_ready,
        "production_decision_ready": (
            evaluation_set_ready
            and run.get("provider") != "reference_fixture"
            and len(latencies) == len(cases)
            and cost_records == len(cases)
        ),
        "operations": {
            "latency_ms_p50": median(latencies) if latencies else None,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost_usd": estimated_cost if cost_records else None,
            "cost_coverage_rate": _rate(cost_records, len(cases)),
        },
        "cases": case_results,
        "method": (
            "frozen bilingual evidence; exact citation and numeric allowlists; "
            "review-labeled material concepts"
        ),
    }


def _claims(output: dict) -> list[tuple[str, dict]]:
    if not isinstance(output, dict):
        return []
    return [
        (section, claim)
        for section in CLAIM_SECTIONS
        for claim in output.get(section, [])
        if isinstance(claim, dict)
    ]


def _concept_matches(text: str, concept: dict) -> bool:
    normalized = text.casefold()
    compact = _compact_concept_text(normalized)
    literal_match = any(
        _compact_concept_text(str(candidate).casefold()) in compact
        for candidate in concept["any_of"]
    )
    semantic_match = any(
        pattern.search(normalized)
        for pattern in CONCEPT_PATTERNS.get(concept.get("id"), ())
    )
    return literal_match or semantic_match


def _compact_concept_text(text: str) -> str:
    compact = re.sub(r"\s+", "", text)
    return re.sub(r"(?<=%)的(?=[a-z\u4e00-\u9fff])", "", compact)


def _prepare_case(case: dict[str, Any]) -> dict[str, Any]:
    prepared = dict(case)
    prepared["allowed_number_literals"] = sorted(
        {
            *case["allowed_number_literals"],
            *localized_month_number_literals(case["evidence"]),
        }
    )
    return prepared


def _is_grounded_record(record: object) -> bool:
    if not isinstance(record, dict):
        return False
    output = record.get("output")
    return isinstance(output, dict) and output.get("mode") == "grounded_llm"


def _rate(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 1.0
