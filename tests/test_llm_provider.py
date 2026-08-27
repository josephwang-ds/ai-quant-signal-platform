from __future__ import annotations

import json

from company_lens.contracts import Citation, FilingBrief, FilingReaction
from company_lens.llm import (
    JsonExplanationCache,
    OpenAIResponsesProvider,
    build_grounded_request,
    generate_with_fallback,
)


def _performance() -> dict:
    return {
        "asset": {"total_return": 0.12, "cagr": 0.04, "max_drawdown": -0.18},
        "benchmark": {"total_return": 0.08},
        "relative_total_return": 0.04,
        "observations": 500,
    }


def _filings() -> list[FilingBrief]:
    accession = "0000000001-26-000001"
    anchor = f"{accession}#sentence-4"
    return [
        FilingBrief(
            accession=accession,
            form="8-K",
            accepted_at="2026-08-20T16:30:00-04:00",
            items=[{"code": "2.02", "label": "Results of operations (earnings)"}],
            source_url="https://www.sec.gov/example",
            novelty=0.2,
            passages=[
                Citation(
                    anchor=anchor,
                    accession=accession,
                    source_url="https://www.sec.gov/example",
                    text="The company reported revenue of $120 million.",
                )
            ],
            reaction=FilingReaction(
                session="2026-08-21",
                asset_open_to_close=0.015,
                benchmark_open_to_close=0.005,
                benchmark_adjusted_move=0.01,
                magnitude_percentile=0.7,
                prior_sample_size=10,
            ),
        )
    ]


def _explanation(request) -> dict:
    citation = next(iter(request.evidence["latest_filing"]["passages"]))["citation"]
    return {
        "mode": "grounded_llm",
        "what_changed": [
            {
                "text": "The filing reported revenue of $120 million.",
                "citations": [citation],
            }
        ],
        "why_it_matters": [
            {
                "text": "The historical total return was +12.0%.",
                "citations": ["metric:asset.total_return"],
            }
        ],
        "uncertainties": [
            {"text": "The evidence does not establish future performance.", "citations": []}
        ],
    }


class _Response:
    def __init__(self, explanation: dict) -> None:
        self.explanation = explanation

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return {
            "usage": {"input_tokens": 321, "output_tokens": 123},
            "output": [
                {
                    "type": "message",
                    "content": [
                        {"type": "output_text", "text": json.dumps(self.explanation)}
                    ],
                }
            ]
        }


class _Session:
    def __init__(self, explanation: dict) -> None:
        self.explanation = explanation
        self.call = None

    def post(self, url, **kwargs):
        self.call = {"url": url, **kwargs}
        return _Response(self.explanation)


class _Provider:
    provider_name = "fake"
    model = "fake-grounded-v1"

    def __init__(self, response: dict) -> None:
        self.response = response
        self.calls = 0

    def generate(self, request) -> dict:
        self.calls += 1
        return self.response


def test_evidence_packet_freezes_citations_and_formatted_numbers() -> None:
    request = build_grounded_request("aapl", _performance(), _filings())

    assert request.ticker == "AAPL"
    assert "metric:asset.total_return" in request.allowed_citations
    assert "metric:filing.benchmark_adjusted_move" in request.allowed_citations
    assert "$120" in request.allowed_number_literals
    assert "+12.0%" in request.allowed_number_literals
    assert request.evidence["latest_filing"]["reaction"]["benchmark_adjusted_move"] == {
        "citation": "metric:filing.benchmark_adjusted_move",
        "value": "+1.0%",
    }


def test_openai_adapter_uses_strict_responses_schema_without_storing() -> None:
    request = build_grounded_request("AAPL", _performance(), _filings())
    explanation = _explanation(request)
    session = _Session(explanation)
    provider = OpenAIResponsesProvider(api_key="test-key", session=session)

    assert provider.generate(request) == explanation
    assert session.call["url"] == "https://api.openai.com/v1/responses"
    assert session.call["headers"]["Authorization"] == "Bearer test-key"
    body = session.call["json"]
    assert body["store"] is False
    assert body["text"]["format"]["type"] == "json_schema"
    assert body["text"]["format"]["strict"] is True
    assert body["prompt_cache_key"].endswith(request.prompt_version)
    assert "Preserve every stated unit" in body["instructions"]


def test_openai_adapter_exposes_usage_for_model_scorecards() -> None:
    request = build_grounded_request("AAPL", _performance(), _filings())
    explanation = _explanation(request)
    provider = OpenAIResponsesProvider(
        api_key="test-key", session=_Session(explanation)
    )

    output, usage = provider.generate_with_metadata(request)

    assert output == explanation
    assert usage == {"input_tokens": 321, "output_tokens": 123}


def test_generation_validates_writes_cache_and_reuses_it(tmp_path) -> None:
    request = build_grounded_request("AAPL", _performance(), _filings())
    provider = _Provider(_explanation(request))
    cache = JsonExplanationCache(tmp_path)

    first = generate_with_fallback(
        provider,
        request,
        performance=_performance(),
        filings=_filings(),
        cache=cache,
    )
    second = generate_with_fallback(
        provider,
        request,
        performance=_performance(),
        filings=_filings(),
        cache=cache,
    )

    assert first.fallback_reason is None
    assert not first.cache_hit
    assert second.cache_hit
    assert provider.calls == 1


def test_generation_falls_back_when_provider_invents_a_number() -> None:
    request = build_grounded_request("AAPL", _performance(), _filings())
    invalid = _explanation(request)
    invalid["why_it_matters"][0]["text"] = "The historical total return was +99.0%."

    result = generate_with_fallback(
        _Provider(invalid),
        request,
        performance=_performance(),
        filings=_filings(),
    )

    assert result.explanation["mode"] == "deterministic_fallback"
    assert "unsupported numbers" in result.fallback_reason
