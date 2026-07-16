"""OpenAI-compatible Chat Completions adapter — backend-only; stdlib HTTP, no SDK.

Supports one configured provider per deployment (OpenAI, DeepSeek, or any
OpenAI-compatible HTTPS Chat Completions host via LLM_BASE_URL).
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from app.research_copilot.llm_config import LlmProviderSettings
from app.research_copilot.llm_port import ContextItem, LlmPort, LlmResult


class OpenAiCompatibleLlmAdapter(LlmPort):
    """POST {base_url}/chat/completions with Bearer auth."""

    def __init__(
        self,
        *,
        settings: LlmProviderSettings,
        timeout_seconds: float = 45.0,
    ) -> None:
        self.settings = settings
        self.api_key = settings.api_key
        self.model = settings.model
        self.base_url = settings.base_url
        self.provider = settings.provider
        self.endpoint = settings.chat_completions_url
        self.timeout_seconds = timeout_seconds
        self.supports_response_format_json_object = (
            settings.supports_response_format_json_object
        )

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        context: list[ContextItem],
    ) -> LlmResult:
        context_block = "\n\n".join(
            (
                f"[citation_id={item.citation_id}] "
                f"({item.source_type}:{item.source_id}) {item.label}\n"
                f"{item.content}"
            )
            for item in context
        )
        payload: dict = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"Workspace context:\n{context_block}\n\n"
                        f"Researcher question:\n{user_prompt}"
                    ),
                },
            ],
            "temperature": 0.2,
        }
        if self.supports_response_format_json_object:
            payload["response_format"] = {"type": "json_object"}

        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(
                request, timeout=self.timeout_seconds
            ) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            status = exc.code
            if status in {401, 403}:
                raise ProviderAuthenticationError(
                    "Research Copilot provider authentication failed."
                ) from exc
            if status == 429:
                raise ProviderUnavailableError(
                    "Research Copilot provider is rate limited."
                ) from exc
            raise ProviderUnavailableError(
                f"Research Copilot provider request failed with status {status}."
            ) from exc
        except TimeoutError as exc:
            raise ProviderTimeoutError(
                "Research Copilot provider request timed out."
            ) from exc
        except urllib.error.URLError as exc:
            raise ProviderUnavailableError(
                "Research Copilot provider unreachable."
            ) from exc

        try:
            body = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ProviderMalformedResponseError(
                "Research Copilot provider returned a non-JSON response."
            ) from exc

        try:
            choice = body["choices"][0]
            text = choice["message"]["content"].strip()
            finish_reason = choice.get("finish_reason")
            model = body.get("model", self.model)
        except (KeyError, IndexError, TypeError, AttributeError) as exc:
            raise ProviderMalformedResponseError(
                "Research Copilot provider returned a malformed response."
            ) from exc

        if not isinstance(text, str):
            raise ProviderMalformedResponseError(
                "Research Copilot provider returned a malformed response."
            )

        latency_ms = int((time.perf_counter() - started) * 1000)
        return LlmResult(
            text=text,
            model=str(model),
            latency_ms=latency_ms,
            raw_finish_reason=finish_reason,
        )


# Backward-compatible alias used by older imports/tests.
OpenAiLlmAdapter = OpenAiCompatibleLlmAdapter


class ProviderUnavailableError(Exception):
    pass


class ProviderTimeoutError(Exception):
    pass


class ProviderAuthenticationError(Exception):
    pass


class ProviderMalformedResponseError(Exception):
    pass
