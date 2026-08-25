from __future__ import annotations

from company_lens.llm import explanation_cache_key, validate_grounded_explanation
from company_lens.llm.grounded import localized_month_number_literals


def _valid() -> dict:
    return {
        "mode": "grounded_llm",
        "what_changed": [
            {"text": "Revenue was $120 million.", "citations": ["filing#sentence-1"]}
        ],
        "why_it_matters": [
            {"text": "The historical return was +12.0%.", "citations": ["metric:return"]}
        ],
        "uncertainties": [
            {"text": "The evidence does not establish future performance.", "citations": []}
        ],
    }


def test_grounded_validator_accepts_only_supplied_citations_and_numbers() -> None:
    result = validate_grounded_explanation(
        _valid(),
        allowed_citations={"filing#sentence-1", "metric:return"},
        allowed_number_literals={"$120", "+12.0%"},
    )

    assert result.ok
    assert result.errors == ()


def test_grounded_validator_preserves_signed_number_next_to_chinese_text() -> None:
    response = _valid()
    response["why_it_matters"][0]["text"] = "基准调整后变动为+1.0%。"

    result = validate_grounded_explanation(
        response,
        allowed_citations={"filing#sentence-1", "metric:return"},
        allowed_number_literals={"$120", "+1.0%"},
    )

    assert result.ok
    assert result.errors == ()


def test_named_english_month_has_controlled_numeric_localization() -> None:
    evidence = {"passage": "The appointment is effective November 18, 2026."}

    assert localized_month_number_literals(evidence) == frozenset({"11"})


def test_grounded_validator_rejects_hallucinated_evidence_and_advice() -> None:
    response = _valid()
    response["what_changed"][0] = {
        "text": "Revenue was $999 million; buy the stock.",
        "citations": ["filing#invented"],
    }

    result = validate_grounded_explanation(
        response,
        allowed_citations={"filing#sentence-1", "metric:return"},
        allowed_number_literals={"$120", "+12.0%"},
    )

    assert not result.ok
    assert any("unsupported citations" in error for error in result.errors)
    assert any("unsupported numbers" in error for error in result.errors)
    assert any("advice or a directional forecast" in error for error in result.errors)


def test_grounded_validator_rejects_wrong_mode_extra_fields_and_chinese_forecast() -> None:
    response = _valid()
    response["mode"] = "unverified"
    response["confidence"] = 0.9
    response["why_it_matters"][0]["text"] = "股价预计上涨。"

    result = validate_grounded_explanation(
        response,
        allowed_citations={"filing#sentence-1", "metric:return"},
        allowed_number_literals={"$120", "+12.0%"},
    )

    assert not result.ok
    assert "mode must be grounded_llm" in result.errors
    assert any("unexpected fields" in error for error in result.errors)
    assert any("advice or a directional forecast" in error for error in result.errors)


def test_explanation_cache_key_changes_with_model_or_evidence() -> None:
    base = {
        "accession": "abc",
        "prompt_version": "v1",
        "provider": "openai",
        "model": "gpt-5.6-terra",
        "evidence": {"passages": ["one"]},
    }

    first = explanation_cache_key(**base)

    assert first == explanation_cache_key(**base)
    assert first != explanation_cache_key(**{**base, "model": "gpt-5.6-luna"})
    assert first != explanation_cache_key(
        **{**base, "evidence": {"passages": ["one", "two"]}}
    )
