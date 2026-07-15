"""Post-generation grounding and safety checks."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

PROHIBITED_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bbuy\s+now\b", "buy_now"),
    (r"\bsell\s+now\b", "sell_now"),
    (r"\bhold\s+position\b", "hold_position"),
    (r"\bposition\s+size\b", "position_size"),
    (r"\btarget\s+price\b", "target_price"),
    (r"\bguaranteed\b", "guaranteed"),
    (r"\bsafe\s+investment\b", "safe_investment"),
    (r"\bcertain\s+profit\b", "certain_profit"),
    (r"\bapproved\s+strategy\b", "approved_strategy"),
    (r"\brobust\s+strategy\b", "robust_strategy"),
)

STANDALONE_TRADE_DIRECTIVE = re.compile(
    r"\b(?P<word>buy|sell|hold)\b(?!\s*-?\s*and\s*-?\s*hold)",
    re.IGNORECASE,
)


@dataclass
class SafetyVerdict:
    safe: bool
    grounding_status: str
    warnings: list[str] = field(default_factory=list)
    sanitized_answer: str | None = None


def _allowed_buy_sell_context(text: str, match: re.Match[str]) -> bool:
    window = text[max(0, match.start() - 12) : match.end() + 16].lower()
    return "buy-and-hold" in window or "buy and hold" in window


def evaluate_answer(
    answer: str,
    *,
    citations: list[dict[str, str]],
    context_blob: str,
) -> SafetyVerdict:
    warnings: list[str] = []
    normalized = answer.strip()
    if not normalized:
        return SafetyVerdict(
            safe=False,
            grounding_status="unavailable",
            warnings=["empty_answer"],
            sanitized_answer=(
                "The Copilot could not produce a grounded answer from the "
                "available workspace evidence."
            ),
        )

    lowered = normalized.lower()
    for pattern, code in PROHIBITED_PATTERNS:
        if re.search(pattern, lowered):
            return SafetyVerdict(
                safe=False,
                grounding_status="unavailable",
                warnings=[f"prohibited_language:{code}"],
                sanitized_answer=(
                    "This Copilot cannot provide investment recommendations "
                    "or trading directives. Ask about existing research "
                    "evidence, validation stages, or evaluation governance."
                ),
            )

    for match in STANDALONE_TRADE_DIRECTIVE.finditer(normalized):
        if not _allowed_buy_sell_context(normalized, match):
            return SafetyVerdict(
                safe=False,
                grounding_status="unavailable",
                warnings=[f"prohibited_language:{match.group('word').lower()}"],
                sanitized_answer=(
                    "This Copilot cannot provide investment recommendations "
                    "or trading directives. Ask about existing research "
                    "evidence, validation stages, or evaluation governance."
                ),
            )

    fabricated = re.findall(r"\b\d+(?:\.\d+)?%?\b", normalized)
    context_numbers = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", context_blob))
    unknown_numbers = [
        number for number in fabricated if number.rstrip("%") not in context_numbers
    ]
    grounding_status = "grounded"
    if unknown_numbers[:3]:
        grounding_status = "partially_grounded"
        warnings.append("unsupported_numeric_claim")

    if not citations and len(normalized) > 80:
        return SafetyVerdict(
            safe=True,
            grounding_status="unavailable",
            warnings=["missing_citations"],
            sanitized_answer=normalized,
        )

    return SafetyVerdict(
        safe=True,
        grounding_status=grounding_status,
        warnings=warnings,
        sanitized_answer=normalized,
    )
