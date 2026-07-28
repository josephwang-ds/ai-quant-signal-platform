"""Deterministic per-factor research summaries (no opaque score)."""

from __future__ import annotations

from typing import Any


def build_factor_summaries(
    *,
    factor_results: dict[tuple[str, int], dict[str, Any]],
    decay: dict[str, Any],
    correlation_warnings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Assemble evidence-style summaries per factor × horizon."""
    warnings_by_factor: dict[str, list[dict[str, Any]]] = {}
    for w in correlation_warnings:
        warnings_by_factor.setdefault(w["factor_a"], []).append(w)
        warnings_by_factor.setdefault(w["factor_b"], []).append(w)

    out: list[dict[str, Any]] = []
    for (factor, horizon), payload in sorted(
        factor_results.items(), key=lambda item: (item[0][0], item[0][1])
    ):
        ic = payload.get("rank_ic") or {}
        q = payload.get("quantiles") or {}
        turn = payload.get("turnover") or {}
        stab = payload.get("stability") or {}
        available = int(ic.get("available_date_count") or 0)
        unavailable = int(ic.get("unavailable_date_count") or 0)
        if available == 0 and unavailable == 0:
            status = "unavailable"
        elif available == 0:
            status = "failed"
        elif unavailable > 0:
            status = "incomplete"
        else:
            status = "complete"

        out.append(
            {
                "factor": factor,
                "horizon": horizon,
                "label": payload.get("label"),
                "evidence_status": status,
                "coverage": {
                    "available_date_count": available,
                    "unavailable_date_count": unavailable,
                    "observation_count": ic.get("observation_count"),
                },
                "mean_rank_ic": ic.get("mean_rank_ic"),
                "median_rank_ic": ic.get("median_rank_ic"),
                "rank_ic_volatility": ic.get("rank_ic_std"),
                "icir": ic.get("icir"),
                "positive_ic_ratio": ic.get("positive_ic_ratio"),
                "mean_top_minus_bottom": q.get("mean_top_minus_bottom"),
                "spread_volatility": q.get("spread_volatility"),
                "monotonicity_diagnostic": q.get("monotonicity_spearman"),
                "turnover": turn.get("mean_turnover"),
                "horizon_comparison": (decay.get("by_factor") or {}).get(factor),
                "period_stability": {
                    "periods_positive": stab.get("periods_positive"),
                    "periods_negative": stab.get("periods_negative"),
                    "sign_consistency_ratio": stab.get("sign_consistency_ratio"),
                    "worst_period_mean_ic": stab.get("worst_period_mean_ic"),
                    "best_period_mean_ic": stab.get("best_period_mean_ic"),
                },
                "redundancy_warnings": warnings_by_factor.get(factor, []),
                "unavailable_evidence": payload.get("unavailable_evidence", []),
                "limitations": [
                    "Descriptive factor evidence only — not a trading signal.",
                    "No transaction costs or portfolio construction in Phase 2.",
                    "Static universe survivorship bias is not solved.",
                ],
            }
        )
    return out
