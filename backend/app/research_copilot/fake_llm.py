"""Deterministic fake LLM for offline CI — no API key required."""

from __future__ import annotations

import json
import time

from app.research_copilot.llm_port import ContextItem, LlmPort, LlmResult

DEFAULT_FAKE_MODEL = "fake-copilot-v1"


def _available_ids(context: list[ContextItem]) -> set[str]:
    return {item.citation_id for item in context}


def _select_citation_ids(question: str, available: set[str]) -> list[str]:
    lowered = question.lower()
    requested: list[str]

    if any(token in available for token in ("factor:rank_ic", "factor:icir", "factor:turnover")):
        if "icir" in lowered:
            requested = ["factor:icir", "factor:rank_ic"]
        elif "turnover" in lowered or "cost" in lowered:
            requested = ["factor:turnover", "factor:long_short"]
        elif "long" in lowered or "short" in lowered or "quantile" in lowered:
            requested = ["factor:long_short", "factor:rank_ic"]
        elif "stabil" in lowered:
            requested = ["factor:stability", "factor:rank_ic"]
        elif "warning" in lowered:
            requested = ["factor:warnings"]
        elif "rank" in lowered or "ic" in lowered:
            requested = ["factor:rank_ic", "factor:icir"]
        else:
            requested = [
                "factor:rank_ic",
                "factor:icir",
                "factor:turnover",
                "factor:long_short",
                "factor:stability",
                "factor:warnings",
            ]
        return [citation_id for citation_id in requested if citation_id in available]

    if "incomplete" in lowered or "outstanding" in lowered or "blocker" in lowered:
        requested = ["evaluation:status", "evaluation:outstanding_evidence"]
    elif "oos" in lowered or "out-of-sample" in lowered or "out of sample" in lowered:
        requested = [
            "validation:out_of_sample",
            "documentation:validation_methodology",
        ]
    elif "transaction" in lowered or "cost" in lowered:
        requested = ["validation:transaction_cost_sensitivity"]
    elif "look-ahead" in lowered or "lookahead" in lowered or "bias" in lowered:
        requested = ["notebook:methodology", "documentation:look_ahead_policy"]
    elif "sharpe" in lowered or "drawdown" in lowered or "metric" in lowered:
        requested = ["execution:metrics"]
    elif "hypothesis" in lowered:
        requested = ["notebook:hypothesis"]
    else:
        requested = ["research_definition:definition"]

    return [citation_id for citation_id in requested if citation_id in available]


def _extract_factor_summary_from_context(context: list[ContextItem]) -> dict[str, object]:
    """Pull metric strings already present in factor context items."""
    summary = {
        "rank_ic": "unavailable",
        "icir": "unavailable",
        "turnover": "unavailable",
        "long_short_return": "unavailable",
        "stability": "unavailable",
        "warnings": [],
    }
    for item in context:
        try:
            payload = json.loads(item.content)
        except (TypeError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        if item.citation_id == "factor:rank_ic" and "rank_ic" in payload:
            summary["rank_ic"] = str(payload["rank_ic"])
        if item.citation_id == "factor:icir" and "icir" in payload:
            summary["icir"] = str(payload["icir"])
        if item.citation_id == "factor:turnover" and "turnover" in payload:
            summary["turnover"] = str(payload["turnover"])
        if item.citation_id == "factor:long_short" and "long_short_return" in payload:
            summary["long_short_return"] = str(payload["long_short_return"])
        if item.citation_id == "factor:stability" and "stability" in payload:
            summary["stability"] = str(payload["stability"])
        if item.citation_id == "factor:warnings" and isinstance(payload.get("warnings"), list):
            summary["warnings"] = [str(x) for x in payload["warnings"]]
    return summary


def _build_answer(question: str, *, factor_mode: bool = False) -> str:
    lowered = question.lower()
    if factor_mode:
        return (
            "Based on the stored factor-validation evidence, RankIC, ICIR, "
            "turnover, long–short return, stability, and warnings are summarized "
            "from the completed Factor Validation run only. This is historical "
            "research evidence — not a forecast or investment recommendation."
        )
    if "incomplete" in lowered or "outstanding" in lowered:
        return (
            "Evaluation is incomplete because some implemented validation stages "
            "did not complete and outstanding evidence such as stress testing "
            "and regime analysis remains unavailable. This is a governance "
            "summary only — not an investment recommendation."
        )
    if "oos" in lowered or "out-of-sample" in lowered or "out of sample" in lowered:
        return (
            "The out-of-sample validation stage summarizes whether the "
            "chronological split evidence completed, failed, or remains "
            "incomplete. Refer to the validation stage status and summary "
            "in the assembled evidence."
        )
    if "transaction" in lowered or "cost" in lowered:
        return (
            "Transaction-cost sensitivity evidence is reported in the "
            "validation stage results. The Copilot does not recalculate cost "
            "grids — it explains what the stored validation evidence already "
            "contains."
        )
    if "look-ahead" in lowered or "lookahead" in lowered or "bias" in lowered:
        return (
            "Look-ahead bias is mitigated by using completed bars only and "
            "applying positions with a one-day lag. Signals cannot trade the "
            "same bar that generated them."
        )
    if "sharpe" in lowered:
        return (
            "Any Sharpe ratio shown in this workspace comes from backend "
            "execution or validation evidence already stored for this "
            "research. The Copilot explains that metric; it does not calculate "
            "a new value."
        )
    return (
        "Based on the assembled workspace evidence, the canonical MA20/MA60 SPY "
        "research combines execution metrics, validation stage outcomes, and "
        "evaluation governance. Ask a more specific question about a stage, "
        "blocker, or methodology topic."
    )


def _structured_payload(
    answer: str,
    citation_ids: list[str],
    *,
    factor_summary: dict[str, object] | None = None,
) -> str:
    payload: dict[str, object] = {"answer": answer, "citation_ids": citation_ids}
    if factor_summary is not None:
        payload.update(
            {
                "rank_ic": factor_summary.get("rank_ic", "unavailable"),
                "icir": factor_summary.get("icir", "unavailable"),
                "turnover": factor_summary.get("turnover", "unavailable"),
                "long_short_return": factor_summary.get(
                    "long_short_return", "unavailable"
                ),
                "stability": factor_summary.get("stability", "unavailable"),
                "warnings": factor_summary.get("warnings") or [],
            }
        )
    return json.dumps(payload, ensure_ascii=False)


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
            text=_structured_payload(
                "You should buy SPY now with Sharpe 9.99 for guaranteed profit.",
                ["execution:metrics"],
            ),
            model="fabricating-fake",
            latency_ms=1,
        )


class EmptyCitationFakeLlm(LlmPort):
    """Test-only adapter that returns a substantive answer without citations."""

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        context: list[ContextItem],
    ) -> LlmResult:
        return LlmResult(
            text=_structured_payload(
                "This is a substantive grounded explanation about evaluation "
                "governance and outstanding evidence gaps that should not be "
                "marked grounded without explicit citations.",
                [],
            ),
            model="empty-citation-fake",
            latency_ms=1,
        )


class UnknownCitationFakeLlm(LlmPort):
    """Test-only adapter that cites IDs outside the assembled context."""

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        context: list[ContextItem],
    ) -> LlmResult:
        return LlmResult(
            text=_structured_payload(
                "The answer references evidence using an unknown citation id.",
                ["validation:nonexistent_stage", "evaluation:status"],
            ),
            model="unknown-citation-fake",
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
        available = _available_ids(context)
        factor_mode = "factor:rank_ic" in available
        citation_ids = _select_citation_ids(user_prompt, available)
        answer = _build_answer(user_prompt, factor_mode=factor_mode)
        factor_summary = (
            _extract_factor_summary_from_context(context) if factor_mode else None
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        return LlmResult(
            text=_structured_payload(
                answer, citation_ids, factor_summary=factor_summary
            ),
            model=self.model,
            latency_ms=latency_ms,
        )


class FabricatingFactorFakeLlm(LlmPort):
    """Test-only adapter that invents factor metrics and trade advice."""

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        context: list[ContextItem],
    ) -> LlmResult:
        return LlmResult(
            text=_structured_payload(
                "Buy the Q5 basket now; RankIC will be 0.99 next month.",
                ["factor:rank_ic"],
                factor_summary={
                    "rank_ic": "0.99",
                    "icir": "9.99",
                    "turnover": "0",
                    "long_short_return": "1.0",
                    "stability": "perfect forever",
                    "warnings": [],
                },
            ),
            model="fabricating-factor-fake",
            latency_ms=1,
        )
