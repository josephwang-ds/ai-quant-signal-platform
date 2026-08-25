from __future__ import annotations

import json

import pytest

from company_lens.llm import (
    AnthropicMessagesProvider,
    DeepSeekResponsesProvider,
    GeminiInteractionsProvider,
    GroundedExplanationRequest,
    QwenChatProvider,
    create_explanation_provider,
)


def _request() -> GroundedExplanationRequest:
    return GroundedExplanationRequest(
        ticker="AAPL",
        accession="abc",
        prompt_version="v1",
        language="Chinese",
        depth="beginner",
        evidence={"passages": [{"citation": "filing#1", "text": "Revenue was $120."}]},
        allowed_citations=frozenset({"filing#1"}),
        allowed_number_literals=frozenset({"$120"}),
    )


def _explanation() -> dict:
    return {
        "mode": "grounded_llm",
        "what_changed": [{"text": "Revenue was $120.", "citations": ["filing#1"]}],
        "why_it_matters": [{"text": "This is the reported figure.", "citations": ["filing#1"]}],
        "uncertainties": [{"text": "Future performance is unknown.", "citations": []}],
    }


class _Response:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self.payload


class _Session:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.call = None

    def post(self, url, **kwargs):
        self.call = {"url": url, **kwargs}
        return _Response(self.payload)


def test_deepseek_uses_responses_json_schema_without_openai_storage_fields() -> None:
    session = _Session(
        {
            "output_text": json.dumps(_explanation()),
            "usage": {"input_tokens": 10, "output_tokens": 20},
        }
    )
    provider = DeepSeekResponsesProvider(api_key="test", session=session)

    output, usage = provider.generate_with_metadata(_request())

    assert output == _explanation()
    assert usage == {"input_tokens": 10, "output_tokens": 20}
    assert session.call["url"] == "https://api.deepseek.com/responses"
    body = session.call["json"]
    assert body["text"]["format"]["type"] == "json_schema"
    assert "store" not in body
    assert "prompt_cache_key" not in body


def test_qwen_uses_chat_completions_strict_schema() -> None:
    session = _Session(
        {
            "choices": [{"message": {"content": json.dumps(_explanation())}}],
            "usage": {"prompt_tokens": 11, "completion_tokens": 21},
        }
    )
    provider = QwenChatProvider(api_key="test", session=session)

    output, usage = provider.generate_with_metadata(_request())

    assert output == _explanation()
    assert usage == {"input_tokens": 11, "output_tokens": 21}
    assert session.call["url"].endswith("/chat/completions")
    body = session.call["json"]
    assert body["response_format"]["type"] == "json_schema"
    assert body["response_format"]["json_schema"]["strict"] is True
    assert body["enable_thinking"] is False


def test_anthropic_uses_native_output_config() -> None:
    session = _Session(
        {
            "content": [{"type": "text", "text": json.dumps(_explanation())}],
            "usage": {"input_tokens": 12, "output_tokens": 22},
        }
    )
    provider = AnthropicMessagesProvider(api_key="test", session=session)

    output, usage = provider.generate_with_metadata(_request())

    assert output == _explanation()
    assert usage == {"input_tokens": 12, "output_tokens": 22}
    assert session.call["url"] == "https://api.anthropic.com/v1/messages"
    assert session.call["json"]["output_config"]["format"]["type"] == "json_schema"
    assert session.call["headers"]["x-api-key"] == "test"


def test_gemini_uses_native_interactions_structured_output() -> None:
    session = _Session(
        {
            "steps": [
                {
                    "type": "model_output",
                    "content": [{"type": "text", "text": json.dumps(_explanation())}],
                }
            ],
            "usage": {"input_tokens": 13, "output_tokens": 23},
        }
    )
    provider = GeminiInteractionsProvider(api_key="test", session=session)

    output, usage = provider.generate_with_metadata(_request())

    assert output == _explanation()
    assert usage == {"input_tokens": 13, "output_tokens": 23}
    assert session.call["url"].endswith("/v1beta/interactions")
    assert session.call["json"]["response_format"]["mime_type"] == "application/json"
    assert session.call["headers"]["x-goog-api-key"] == "test"


@pytest.mark.parametrize(
    ("alias", "provider_name", "model"),
    [
        ("openai", "openai", "gpt-5.6-terra"),
        ("deepseek", "deepseek", "deepseek-v4-flash"),
        ("qianwen", "qwen", "qwen3.8-max"),
        ("claude", "anthropic", "claude-sonnet-5"),
        ("google", "gemini", "gemini-3.7-flash"),
    ],
)
def test_provider_factory_supports_user_facing_aliases(
    monkeypatch, alias: str, provider_name: str, model: str
) -> None:
    for key in (
        "COMPANY_LENS_LLM_MODEL",
        "COMPANY_LENS_DEEPSEEK_MODEL",
        "COMPANY_LENS_QWEN_MODEL",
        "COMPANY_LENS_ANTHROPIC_MODEL",
        "COMPANY_LENS_GEMINI_MODEL",
    ):
        monkeypatch.delenv(key, raising=False)

    provider = create_explanation_provider(alias)

    assert provider.provider_name == provider_name
    assert provider.model == model
