"""Factor effectiveness across available label horizons (decay view)."""

from __future__ import annotations

from typing import Any


def build_decay_summary(
    factor_horizon_summaries: dict[tuple[str, int], dict[str, Any]],
) -> dict[str, Any]:
    """
    Compare metrics across horizons for each factor.

    Descriptive only — no causal claim. Only horizons present in inputs.
    """
    factors = sorted({f for f, _ in factor_horizon_summaries})
    by_factor: dict[str, list[dict[str, Any]]] = {}
    for factor in factors:
        rows = []
        for (f, horizon), payload in sorted(
            factor_horizon_summaries.items(), key=lambda item: (item[0][0], item[0][1])
        ):
            if f != factor:
                continue
            ic = payload.get("rank_ic") or {}
            q = payload.get("quantiles") or {}
            rows.append(
                {
                    "horizon": horizon,
                    "label": payload.get("label"),
                    "mean_rank_ic": ic.get("mean_rank_ic"),
                    "median_rank_ic": ic.get("median_rank_ic"),
                    "icir": ic.get("icir"),
                    "mean_top_minus_bottom": q.get("mean_top_minus_bottom"),
                    "available_date_count": ic.get("available_date_count"),
                }
            )
        by_factor[factor] = rows
    return {
        "by_factor": by_factor,
        "note": (
            "Descriptive horizon comparison only; no causal claim. "
            "Horizons limited to Phase 1 labels."
        ),
    }
