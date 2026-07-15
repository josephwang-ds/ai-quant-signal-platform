"""Deterministic fake LLM for offline CI — no API key required."""

from __future__ import annotations

import time

from app.research_copilot.llm_port import ContextItem, LlmPort, LlmResult

DEFAULT_FAKE_MODEL = "fake-copilot-v1"


class FabricatingFakeLlm(LlmPort):
    """Test-only adapter that deliberately fabricates metrics."""

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        context: list[ContextItem],
    ) -> LlmResult:
        return LlmResult(
            text="You should buy SPY now with Sharpe 9.99 for guaranteed profit.",
            model="fabricating-fake",
            latency_ms=1,
        )


class FakeLlmAdapter(LlmPort):
    """Keyword-driven grounded responses for offline tests."""

    def __init__(self, *, model: str = DEFAULT_FAKE_MODEL) -> None:
        self.model = model

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        context: list[ContextItem],
    ) -> LlmResult:
        started = time.perf_counter()
        question = user_prompt.lower()
        evaluation_item = next(
            (item for item in context if item.source_type == "evaluation"),
            None,
        )
        validation_item = next(
            (item for item in context if item.source_type == "validation"),
            None,
        )

        if "incomplete" in question or "outstanding" in question:
            answer = (
                "Evaluation is incomplete because some implemented validation "
                "stages did not complete and outstanding evidence such as "
                "stress testing and regime analysis remains unavailable. "
                "This is a governance summary only — not an investment "
                "recommendation."
            )
        elif "oos" in question or "out-of-sample" in question:
            answer = (
                "The out-of-sample validation stage summarizes whether the "
                "chronological split evidence completed, failed, or remains "
                "incomplete. Refer to the validation stage status and summary "
                "in the assembled evidence."
            )
        elif "transaction" in question or "cost" in question:
            answer = (
                "Transaction-cost sensitivity evidence is reported in the "
                "validation stage results. The Copilot does not recalculate "
                "cost grids — it explains what the stored validation evidence "
                "already contains."
            )
        elif "look-ahead" in question or "bias" in question:
            answer = (
                "Look-ahead bias is mitigated by using completed bars only and "
                "applying positions with a one-day lag. Signals cannot trade "
                "the same bar that generated them."
            )
        elif "sharpe" in question:
            answer = (
                "Any Sharpe ratio shown in this workspace comes from backend "
                "execution or validation evidence already stored for this "
                "research. The Copilot explains that metric; it does not "
                "calculate a new value."
            )
        else:
            answer = (
                "Based on the assembled workspace evidence, the canonical "
                "MA20/MA60 SPY research combines execution metrics, validation "
                "stage outcomes, and evaluation governance. Ask a more "
                "specific question about a stage, blocker, or methodology "
                "topic."
            )

        if evaluation_item and "incomplete" in evaluation_item.content:
            answer += " Current evaluation governance indicates incomplete coverage."

        latency_ms = int((time.perf_counter() - started) * 1000)
        return LlmResult(text=answer, model=self.model, latency_ms=latency_ms)
