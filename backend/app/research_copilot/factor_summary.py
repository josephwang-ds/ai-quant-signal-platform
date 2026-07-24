"""Deterministic Factor Copilot evidence summary — never invents metrics."""

from __future__ import annotations

from typing import Any

UNAVAILABLE = "unavailable"


def is_factor_validation_evidence(stored: dict[str, Any] | None) -> bool:
    if not isinstance(stored, dict):
        return False
    if stored.get("evidence_kind") == "factor_validation":
        return True
    return stored.get("template") == "cross_sectional_factor"


def _fmt_metric(value: Any) -> str:
    if value is None:
        return UNAVAILABLE
    try:
        number = float(value)
    except (TypeError, ValueError):
        return UNAVAILABLE
    if number != number:  # NaN
        return UNAVAILABLE
    return f"{number:.6g}"


def _stability_from_benchmark(benchmark: dict[str, Any] | None) -> str:
    if not isinstance(benchmark, dict):
        return UNAVAILABLE
    checks = benchmark.get("checks")
    if not isinstance(checks, list):
        rationale = benchmark.get("rationale")
        if isinstance(rationale, str) and rationale.strip():
            return rationale.strip()
        return UNAVAILABLE
    for check in checks:
        if not isinstance(check, dict):
            continue
        check_id = check.get("check_id") or check.get("id") or check.get("name")
        if check_id == "subperiod_stability":
            explanation = (
                check.get("explanation")
                or check.get("summary")
                or check.get("rationale")
                or check.get("detail")
            )
            status = check.get("status")
            if isinstance(explanation, str) and explanation.strip():
                return explanation.strip()
            if status:
                return f"subperiod_stability: {status}"
    rationale = benchmark.get("rationale")
    if isinstance(rationale, str) and rationale.strip():
        return rationale.strip()
    return UNAVAILABLE


def build_factor_summary(stored: dict[str, Any]) -> dict[str, Any]:
    """
    Build Factor Copilot summary strings exclusively from stored evidence.

    Fields are strings so unavailable evidence is the literal \"unavailable\".
    """
    ic_summary = (stored.get("ic") or {}).get("summary") or {}
    quantiles = stored.get("quantiles") or {}
    turnover = quantiles.get("turnover") or {}
    long_short = stored.get("long_short") or {}
    warnings_raw = stored.get("warnings") or []
    warnings = [str(item) for item in warnings_raw if str(item).strip()]

    net_ls = long_short.get("cumulative_final_net_of_cost")
    if net_ls is None:
        net_ls = long_short.get("cumulative_final")

    citation_ids = [
        "factor:rank_ic",
        "factor:icir",
        "factor:turnover",
        "factor:long_short",
        "factor:stability",
        "factor:warnings",
    ]

    return {
        "rank_ic": _fmt_metric(ic_summary.get("mean_rank_ic")),
        "icir": _fmt_metric(ic_summary.get("icir")),
        "turnover": _fmt_metric(turnover.get("mean")),
        "long_short_return": _fmt_metric(net_ls),
        "stability": _stability_from_benchmark(stored.get("benchmark")),
        "warnings": warnings,
        "citation_ids": citation_ids,
    }


def prose_from_factor_summary(summary: dict[str, Any]) -> str:
    """Compact grounded prose derived only from validated factor_summary fields."""
    warnings = summary.get("warnings") or []
    warning_text = (
        "; ".join(str(item) for item in warnings)
        if warnings
        else UNAVAILABLE
    )
    return (
        "Factor validation evidence summary (historical research only; "
        "not a forecast or investment recommendation). "
        f"RankIC (mean): {summary.get('rank_ic', UNAVAILABLE)}. "
        f"ICIR: {summary.get('icir', UNAVAILABLE)}. "
        f"Mean turnover: {summary.get('turnover', UNAVAILABLE)}. "
        f"Long–short return (prefer net of cost): "
        f"{summary.get('long_short_return', UNAVAILABLE)}. "
        f"Stability: {summary.get('stability', UNAVAILABLE)}. "
        f"Warnings: {warning_text}."
    )


def validate_llm_factor_fields(
    llm_payload: dict[str, Any],
    evidence_summary: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """
    Prefer evidence values. If the LLM invents a different metric string,
    replace with evidence and warn.
    """
    warnings: list[str] = []
    out = dict(evidence_summary)
    for key in ("rank_ic", "icir", "turnover", "long_short_return", "stability"):
        llm_value = llm_payload.get(key)
        if llm_value is None:
            continue
        text = str(llm_value).strip()
        evidence_text = str(evidence_summary.get(key, UNAVAILABLE))
        if text and text != evidence_text and text.lower() != UNAVAILABLE:
            # Allow LLM to echo unavailable when evidence is unavailable
            if evidence_text == UNAVAILABLE and text.lower() == UNAVAILABLE:
                continue
            warnings.append(f"factor_summary_field_overridden:{key}")
    # Always keep evidence warnings list; merge LLM warning strings only if already in evidence
    llm_warnings = llm_payload.get("warnings")
    if isinstance(llm_warnings, list):
        for item in llm_warnings:
            text = str(item).strip()
            if text and text not in out["warnings"]:
                # Do not invent new engine warnings from the model
                warnings.append("factor_summary_unknown_warning_ignored")
                break
    out["citation_ids"] = list(evidence_summary.get("citation_ids") or [])
    return out, warnings
