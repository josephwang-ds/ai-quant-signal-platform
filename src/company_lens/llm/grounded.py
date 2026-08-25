"""Provider-neutral contracts and guards for grounded explanations."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Protocol

CLAIM_SECTIONS = ("what_changed", "why_it_matters", "uncertainties")
NUMBER_LITERAL = re.compile(
    r"(?<![A-Za-z0-9_.])[+-]?\$?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?"
)
MONTH_NUMBERS = {
    "january": "1",
    "february": "2",
    "march": "3",
    "april": "4",
    "may": "5",
    "june": "6",
    "july": "7",
    "august": "8",
    "september": "9",
    "october": "10",
    "november": "11",
    "december": "12",
}
UNSUPPORTED_PATTERNS = (
    re.compile(
        r"\b(?:(?:should|recommend(?:ed)?)\s+)?(?:buy|sell|short)\s+"
        r"(?:the\s+)?(?:stock|shares?)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bprice target\b", re.IGNORECASE),
    re.compile(
        r"\bwill\s+(?:rise|fall|increase|decrease|outperform|underperform)\b",
        re.IGNORECASE,
    ),
    re.compile(r"(?:买入|卖出|做空|目标价|建议持有)"),
    re.compile(r"(?:股价|股票).{0,8}(?:将会|预计|必然)?(?:上涨|下跌|跑赢|跑输)"),
)


class ExplanationProvider(Protocol):
    """Thin provider adapter; evidence assembly and validation stay outside it."""

    provider_name: str
    model: str

    def generate(self, request: GroundedExplanationRequest) -> dict:
        """Return the common explanation shape from one provider."""


@dataclass(frozen=True)
class GroundedExplanationRequest:
    ticker: str
    accession: str
    prompt_version: str
    language: str
    depth: str
    evidence: dict
    allowed_citations: frozenset[str]
    allowed_number_literals: frozenset[str]


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: tuple[str, ...]


class GroundedOutputRejected(ValueError):
    """Raised when a provider response violates the grounded-output contract."""

    def __init__(self, errors: tuple[str, ...]) -> None:
        super().__init__("; ".join(errors))
        self.errors = errors


def validate_grounded_explanation(
    explanation: dict,
    *,
    allowed_citations: set[str] | frozenset[str],
    allowed_number_literals: set[str] | frozenset[str] | None = None,
) -> ValidationResult:
    """Reject malformed, uncited, numerically invented, or advisory output."""
    errors: list[str] = []
    if not isinstance(explanation, dict):
        return ValidationResult(False, ("response must be an object",))
    if explanation.get("mode") != "grounded_llm":
        errors.append("mode must be grounded_llm")
    unexpected_sections = sorted(set(explanation) - {"mode", *CLAIM_SECTIONS})
    if unexpected_sections:
        errors.append(f"response has unexpected fields: {unexpected_sections}")

    for section in CLAIM_SECTIONS:
        claims = explanation.get(section)
        if not isinstance(claims, list) or not claims:
            errors.append(f"{section} must be a non-empty list")
            continue
        for index, claim in enumerate(claims):
            path = f"{section}[{index}]"
            if not isinstance(claim, dict):
                errors.append(f"{path} must be an object")
                continue
            unexpected_fields = sorted(set(claim) - {"text", "citations"})
            if unexpected_fields:
                errors.append(f"{path} has unexpected fields: {unexpected_fields}")
            text = claim.get("text")
            citations = claim.get("citations")
            if not isinstance(text, str) or not text.strip():
                errors.append(f"{path}.text must be non-empty")
                continue
            if not isinstance(citations, list) or not all(
                isinstance(value, str) for value in citations
            ):
                errors.append(f"{path}.citations must be a string list")
                citations = []
            unknown = sorted(set(citations) - set(allowed_citations))
            if unknown:
                errors.append(f"{path} has unsupported citations: {unknown}")
            if section != "uncertainties" and not citations:
                errors.append(f"{path} requires at least one supplied citation")
            if any(pattern.search(text) for pattern in UNSUPPORTED_PATTERNS):
                errors.append(f"{path} contains advice or a directional forecast")
            if allowed_number_literals is not None:
                invented = sorted(
                    set(NUMBER_LITERAL.findall(text)) - set(allowed_number_literals)
                )
                if invented:
                    errors.append(f"{path} has unsupported numbers: {invented}")

    return ValidationResult(not errors, tuple(errors))


def localized_month_number_literals(evidence: dict) -> frozenset[str]:
    """Allow faithful Chinese localization of named English calendar months."""
    text = json.dumps(evidence, ensure_ascii=False).casefold()
    return frozenset(
        number
        for month, number in MONTH_NUMBERS.items()
        if re.search(rf"\b{month}\b", text)
    )


def explanation_cache_key(
    *,
    accession: str,
    prompt_version: str,
    provider: str,
    model: str,
    evidence: dict,
) -> str:
    """Key cached output by every input that can change its meaning."""
    payload = {
        "accession": accession,
        "prompt_version": prompt_version,
        "provider": provider,
        "model": model,
        "evidence": evidence,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
