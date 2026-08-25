"""Provider adapters that preserve the shared grounded-explanation contract."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from typing import Any

import requests

from company_lens.llm.grounded import GroundedExplanationRequest
from company_lens.llm.openai_provider import (
    EXPLANATION_SCHEMA,
    SYSTEM_INSTRUCTIONS,
    OpenAIResponsesProvider,
    ProviderConfigurationError,
    ProviderResponseError,
)


class DeepSeekResponsesProvider(OpenAIResponsesProvider):
    """DeepSeek's OpenAI-compatible Responses API with JSON Schema output."""

    provider_name = "deepseek"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = "deepseek-v4-flash",
        base_url: str = "https://api.deepseek.com",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url,
            **kwargs,
        )

    @classmethod
    def from_env(cls, **kwargs: Any) -> DeepSeekResponsesProvider:
        settings = {
            "api_key": os.environ.get("DEEPSEEK_API_KEY"),
            "model": os.environ.get(
                "COMPANY_LENS_DEEPSEEK_MODEL", "deepseek-v4-flash"
            ),
            "base_url": os.environ.get(
                "DEEPSEEK_BASE_URL", "https://api.deepseek.com"
            ),
        }
        settings.update(kwargs)
        return cls(**settings)

    def _payload(self, request: GroundedExplanationRequest) -> dict:
        payload = super()._payload(request)
        # DeepSeek's Responses API is stateless and does not document these
        # OpenAI-specific request controls.
        payload.pop("prompt_cache_key", None)
        payload.pop("store", None)
        payload["text"]["format"].pop("strict", None)
        return payload


class QwenChatProvider:
    """Alibaba Cloud Model Studio Chat Completions adapter for strict Qwen JSON."""

    provider_name = "qwen"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = "qwen3.8-max",
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout: float = 45.0,
        max_output_tokens: int = 1_200,
        session: Any | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_output_tokens = max_output_tokens
        self.session = session or requests.Session()

    @classmethod
    def from_env(cls, **kwargs: Any) -> QwenChatProvider:
        settings = {
            "api_key": os.environ.get("DASHSCOPE_API_KEY"),
            "model": os.environ.get("COMPANY_LENS_QWEN_MODEL", "qwen3.8-max"),
            "base_url": os.environ.get(
                "QWEN_BASE_URL",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            ),
        }
        settings.update(kwargs)
        return cls(**settings)

    def generate(self, request: GroundedExplanationRequest) -> dict:
        explanation, _ = self.generate_with_metadata(request)
        return explanation

    def generate_with_metadata(
        self, request: GroundedExplanationRequest
    ) -> tuple[dict, dict[str, int]]:
        if not self.api_key:
            raise ProviderConfigurationError("DASHSCOPE_API_KEY is not configured")
        response = self.session.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=self._payload(request),
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        try:
            output_text = payload["choices"][0]["message"]["content"]
            explanation = json.loads(output_text)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
            raise ProviderResponseError(
                "Qwen response contained no parseable JSON message"
            ) from error
        if not isinstance(explanation, dict):
            raise ProviderResponseError("Qwen response output was not a JSON object")
        usage = payload.get("usage", {})
        metadata = {
            "input_tokens": int(usage.get("prompt_tokens", 0)),
            "output_tokens": int(usage.get("completion_tokens", 0)),
        }
        return explanation, metadata

    def _payload(self, request: GroundedExplanationRequest) -> dict:
        schema = deepcopy(EXPLANATION_SCHEMA)
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": schema["name"],
                "strict": schema["strict"],
                "schema": schema["schema"],
            },
        }
        user_input = {
            "task": {
                "ticker": request.ticker,
                "accession": request.accession,
                "language": request.language,
                "reader_depth": request.depth,
            },
            "allowed_citations": sorted(request.allowed_citations),
            "allowed_number_literals": sorted(request.allowed_number_literals),
            "evidence": request.evidence,
        }
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                {
                    "role": "user",
                    "content": json.dumps(
                        user_input, ensure_ascii=False, separators=(",", ":")
                    ),
                },
            ],
            "response_format": response_format,
            "enable_thinking": False,
            "max_tokens": self.max_output_tokens,
        }


class AnthropicMessagesProvider:
    """Anthropic Messages API adapter using native structured outputs."""

    provider_name = "anthropic"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = "claude-sonnet-5",
        base_url: str = "https://api.anthropic.com/v1",
        timeout: float = 45.0,
        max_output_tokens: int = 1_200,
        session: Any | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_output_tokens = max_output_tokens
        self.session = session or requests.Session()

    @classmethod
    def from_env(cls, **kwargs: Any) -> AnthropicMessagesProvider:
        settings = {
            "api_key": os.environ.get("ANTHROPIC_API_KEY"),
            "model": os.environ.get(
                "COMPANY_LENS_ANTHROPIC_MODEL", "claude-sonnet-5"
            ),
            "base_url": os.environ.get(
                "ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1"
            ),
        }
        settings.update(kwargs)
        return cls(**settings)

    def generate(self, request: GroundedExplanationRequest) -> dict:
        explanation, _ = self.generate_with_metadata(request)
        return explanation

    def generate_with_metadata(
        self, request: GroundedExplanationRequest
    ) -> tuple[dict, dict[str, int]]:
        if not self.api_key:
            raise ProviderConfigurationError("ANTHROPIC_API_KEY is not configured")
        response = self.session.post(
            f"{self.base_url}/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json=self._payload(request),
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        output_text = next(
            (
                block.get("text")
                for block in payload.get("content", [])
                if isinstance(block, dict)
                and block.get("type") == "text"
                and isinstance(block.get("text"), str)
            ),
            None,
        )
        try:
            explanation = json.loads(output_text)
        except (TypeError, json.JSONDecodeError) as error:
            raise ProviderResponseError(
                "Anthropic response contained no parseable JSON text block"
            ) from error
        if not isinstance(explanation, dict):
            raise ProviderResponseError("Anthropic response output was not a JSON object")
        usage = payload.get("usage", {})
        return explanation, {
            "input_tokens": int(usage.get("input_tokens", 0)),
            "output_tokens": int(usage.get("output_tokens", 0)),
        }

    def _payload(self, request: GroundedExplanationRequest) -> dict:
        return {
            "model": self.model,
            "max_tokens": self.max_output_tokens,
            "system": SYSTEM_INSTRUCTIONS,
            "messages": [
                {
                    "role": "user",
                    "content": json.dumps(
                        _grounded_user_input(request),
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                }
            ],
            "output_config": {
                "format": {
                    "type": "json_schema",
                    "schema": deepcopy(EXPLANATION_SCHEMA["schema"]),
                }
            },
        }


class GeminiInteractionsProvider:
    """Google Gemini Interactions API adapter using native structured output."""

    provider_name = "gemini"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = "gemini-3.7-flash",
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout: float = 45.0,
        session: Any | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()

    @classmethod
    def from_env(cls, **kwargs: Any) -> GeminiInteractionsProvider:
        settings = {
            "api_key": os.environ.get("GEMINI_API_KEY"),
            "model": os.environ.get(
                "COMPANY_LENS_GEMINI_MODEL", "gemini-3.7-flash"
            ),
            "base_url": os.environ.get(
                "GEMINI_BASE_URL",
                "https://generativelanguage.googleapis.com/v1beta",
            ),
        }
        settings.update(kwargs)
        return cls(**settings)

    def generate(self, request: GroundedExplanationRequest) -> dict:
        explanation, _ = self.generate_with_metadata(request)
        return explanation

    def generate_with_metadata(
        self, request: GroundedExplanationRequest
    ) -> tuple[dict, dict[str, int]]:
        if not self.api_key:
            raise ProviderConfigurationError("GEMINI_API_KEY is not configured")
        response = self.session.post(
            f"{self.base_url}/interactions",
            headers={
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json",
            },
            json=self._payload(request),
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        output_text = _gemini_output_text(payload)
        try:
            explanation = json.loads(output_text)
        except (TypeError, json.JSONDecodeError) as error:
            raise ProviderResponseError(
                "Gemini response contained no parseable structured output"
            ) from error
        if not isinstance(explanation, dict):
            raise ProviderResponseError("Gemini response output was not a JSON object")
        usage = payload.get("usage", payload.get("usage_metadata", {}))
        return explanation, {
            "input_tokens": int(
                usage.get("input_tokens", usage.get("prompt_token_count", 0))
            ),
            "output_tokens": int(
                usage.get("output_tokens", usage.get("candidates_token_count", 0))
            ),
        }

    def _payload(self, request: GroundedExplanationRequest) -> dict:
        packet = json.dumps(
            _grounded_user_input(request),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return {
            "model": self.model,
            "input": f"{SYSTEM_INSTRUCTIONS}\n\nEvidence packet:\n{packet}",
            "response_format": {
                "type": "text",
                "mime_type": "application/json",
                "schema": deepcopy(EXPLANATION_SCHEMA["schema"]),
            },
        }


def create_explanation_provider(
    provider: str | None = None,
    *,
    model: str | None = None,
) -> (
    OpenAIResponsesProvider
    | DeepSeekResponsesProvider
    | QwenChatProvider
    | AnthropicMessagesProvider
    | GeminiInteractionsProvider
):
    """Create the selected provider from server-side environment configuration."""
    selected = (provider or os.environ.get("COMPANY_LENS_LLM_PROVIDER", "openai")).lower()
    kwargs = {"model": model} if model else {}
    if selected == "openai":
        return OpenAIResponsesProvider.from_env(**kwargs)
    if selected == "deepseek":
        return DeepSeekResponsesProvider.from_env(**kwargs)
    if selected in {"qwen", "qianwen"}:
        return QwenChatProvider.from_env(**kwargs)
    if selected in {"anthropic", "claude"}:
        return AnthropicMessagesProvider.from_env(**kwargs)
    if selected in {"google", "gemini"}:
        return GeminiInteractionsProvider.from_env(**kwargs)
    raise ValueError(
        "unsupported LLM provider "
        f"{selected!r}; choose openai, deepseek, qwen, anthropic, or gemini"
    )


def _grounded_user_input(request: GroundedExplanationRequest) -> dict:
    return {
        "task": {
            "ticker": request.ticker,
            "accession": request.accession,
            "language": request.language,
            "reader_depth": request.depth,
        },
        "allowed_citations": sorted(request.allowed_citations),
        "allowed_number_literals": sorted(request.allowed_number_literals),
        "evidence": request.evidence,
    }


def _gemini_output_text(payload: dict) -> str:
    direct = payload.get("output_text")
    if isinstance(direct, str) and direct:
        return direct
    for step in payload.get("steps", []):
        if not isinstance(step, dict):
            continue
        for content in step.get("content", []):
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                return content["text"]
    raise ProviderResponseError("Gemini response contained no output text")
