"""OpenAI Chat Completions adapter — backend-only; stdlib HTTP, no SDK."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

from app.research_copilot.llm_port import ContextItem, LlmPort, LlmResult

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


class OpenAiLlmAdapter(LlmPort):
    def __init__(
        self,
        *,
        api_key: str,
        model: str | None = None,
        timeout_seconds: float = 45.0,
    ) -> None:
        self.api_key = api_key
        self.model = (model or os.getenv("COPILOT_MODEL") or DEFAULT_OPENAI_MODEL).strip()
        self.timeout_seconds = timeout_seconds

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
        payload = {
            "model": self.model,
            "response_format": {"type": "json_object"},
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
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
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
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise ProviderUnavailableError(
                f"OpenAI request failed with status {exc.code}."
            ) from exc
        except TimeoutError as exc:
            raise ProviderTimeoutError("OpenAI request timed out.") from exc
        except urllib.error.URLError as exc:
            raise ProviderUnavailableError("OpenAI provider unreachable.") from exc

        text = body["choices"][0]["message"]["content"].strip()
        latency_ms = int((time.perf_counter() - started) * 1000)
        return LlmResult(
            text=text,
            model=body.get("model", self.model),
            latency_ms=latency_ms,
            raw_finish_reason=body["choices"][0].get("finish_reason"),
        )


class ProviderUnavailableError(Exception):
    pass


class ProviderTimeoutError(Exception):
    pass
