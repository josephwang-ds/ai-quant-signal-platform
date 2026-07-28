"""Orchestrate Phase 1 panel → Phase 2 factor research evidence."""

from __future__ import annotations

import re
from typing import Any

from app.cross_sectional.constants import (
    DEFAULT_CORRELATION_WARNING_THRESHOLD,
    DEFAULT_LIQUIDITY_DOLLAR_VOLUME_FLOOR,
    DEFAULT_MIN_CROSS_SECTION_SIZE,
    DEFAULT_MIN_QUANTILE_SIZE,
    DEFAULT_MIN_STABILITY_PERIOD_DATES,
    DEFAULT_MIN_TURNOVER_OVERLAP,
    DEFAULT_QUANTILE_COUNT,
    DEFAULT_RESEARCH_PREVIEW_ROWS,
    FACTOR_VERSION,
    LABEL_COLUMNS,
    MAX_REQUEST_SYMBOLS,
    MAX_RESEARCH_PREVIEW_ROWS,
    RESEARCH_FACTOR_COLUMNS,
    UNIVERSE_ID_LIQUID_31,
)
from app.cross_sectional.dataset import (
    CrossSectionalDatasetError,
    CrossSectionalDatasetService,
    _as_jsonable,
)
from app.cross_sectional.research.correlation import (
    compute_factor_correlations,
    summarize_correlations,
)
from app.cross_sectional.research.decay import build_decay_summary
from app.cross_sectional.research.quantiles import (
    compute_daily_quantiles,
    summarize_quantiles,
)
from app.cross_sectional.research.rank_ic import (
    compute_daily_rank_ic,
    summarize_rank_ic,
)
from app.cross_sectional.research.stability import summarize_stability
from app.cross_sectional.research.summary import build_factor_summaries
from app.cross_sectional.research.turnover import (
    compute_factor_turnover,
    summarize_turnover,
)
from app.cross_sectional.universe import configured_universe_version, universe_disclosures
from app.research_execution.market_data_port import MarketDataPort, utc_now_iso
from app.research_reproducibility import build_reproducibility_manifest
from app.research_validation.result_store import (
    InMemoryValidationResultStore,
    ValidationResultStore,
)

RESEARCH_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9\-_]{1,63}$")
EVIDENCE_KIND = "cross_sectional_factor_research"
TEMPLATE_ID = "cross_sectional_factor"
_LABEL_BY_HORIZON = {5: "forward_return_5d", 20: "forward_return_20d"}


class CrossSectionalFactorResearchError(Exception):
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _horizon_label(horizon: int) -> str:
    label = _LABEL_BY_HORIZON.get(int(horizon))
    if label is None or label not in LABEL_COLUMNS:
        raise CrossSectionalFactorResearchError(
            f"Unsupported label horizon {horizon}. Allowed: {sorted(_LABEL_BY_HORIZON)}"
        )
    return label


def _bounded(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    return [{k: _as_jsonable(v) for k, v in row.items()} for row in rows[:limit]]


class CrossSectionalFactorResearchService:
    """Phase 2 research on a Phase 1 panel (no model training)."""

    def __init__(
        self,
        market_data: MarketDataPort,
        result_store: ValidationResultStore | None = None,
        dataset_service: CrossSectionalDatasetService | None = None,
    ) -> None:
        store = result_store or InMemoryValidationResultStore()
        self._result_store = store
        # Dedicated dataset helper that does not share the research store writes
        # for panel builds (load_panel does not persist).
        self._dataset = dataset_service or CrossSectionalDatasetService(
            market_data, InMemoryValidationResultStore()
        )

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        research_id = str(
            payload.get("research_id") or "cross-sectional-factor-research-v1"
        ).strip()
        if not RESEARCH_ID_PATTERN.match(research_id):
            raise CrossSectionalFactorResearchError(
                "research_id must be 2–64 chars of lowercase letters, digits, -, _."
            )

        factors = list(payload.get("factor_columns") or list(RESEARCH_FACTOR_COLUMNS))
        allowed = set(RESEARCH_FACTOR_COLUMNS)
        bad = [f for f in factors if f not in allowed]
        if bad:
            raise CrossSectionalFactorResearchError(
                f"Unsupported factor_columns: {bad}. Allowed: {sorted(allowed)}"
            )

        horizons = list(
            dict.fromkeys(int(h) for h in (payload.get("label_horizons") or [5, 20]))
        )
        for h in horizons:
            _horizon_label(h)

        quantile_count = int(payload.get("quantile_count", DEFAULT_QUANTILE_COUNT))
        min_cs = int(
            payload.get("minimum_cross_section_size", DEFAULT_MIN_CROSS_SECTION_SIZE)
        )
        min_q = int(payload.get("minimum_quantile_size", DEFAULT_MIN_QUANTILE_SIZE))
        if quantile_count < 2 or quantile_count > 10:
            raise CrossSectionalFactorResearchError(
                "quantile_count must be between 2 and 10."
            )
        if min_cs < 3:
            raise CrossSectionalFactorResearchError(
                "minimum_cross_section_size must be >= 3."
            )
        if min_cs < quantile_count * min_q:
            raise CrossSectionalFactorResearchError(
                "minimum_cross_section_size must be >= quantile_count * minimum_quantile_size."
            )

        apply_liq = bool(payload.get("apply_liquidity_filter", False))
        corr_thresh = float(
            payload.get(
                "correlation_warning_threshold",
                DEFAULT_CORRELATION_WARNING_THRESHOLD,
            )
        )
        min_overlap = int(
            payload.get("minimum_turnover_overlap", DEFAULT_MIN_TURNOVER_OVERLAP)
        )
        min_period_dates = int(
            payload.get(
                "minimum_stability_period_dates",
                DEFAULT_MIN_STABILITY_PERIOD_DATES,
            )
        )
        preview_rows = int(payload.get("preview_rows", DEFAULT_RESEARCH_PREVIEW_ROWS))
        if preview_rows < 0 or preview_rows > MAX_RESEARCH_PREVIEW_ROWS:
            raise CrossSectionalFactorResearchError(
                f"preview_rows must be between 0 and {MAX_RESEARCH_PREVIEW_ROWS}."
            )

        universe_id = str(
            payload.get("universe_id") or UNIVERSE_ID_LIQUID_31
        ).strip().lower()
        symbols_override = payload.get("symbols")
        if symbols_override is not None and len(symbols_override) > MAX_REQUEST_SYMBOLS:
            raise CrossSectionalFactorResearchError(
                f"symbols must contain at most {MAX_REQUEST_SYMBOLS} tickers."
            )

        dataset_payload = {
            "research_id": research_id,
            "universe_id": universe_id,
            "symbols": symbols_override,
            "start_date": payload.get("start_date", "2019-01-01"),
            "end_date": payload.get("end_date"),
            "liquidity_dollar_volume_floor": payload.get(
                "liquidity_dollar_volume_floor",
                DEFAULT_LIQUIDITY_DOLLAR_VOLUME_FLOOR,
            ),
            "preview_rows": 0,
            "min_history_days": payload.get("min_history_days", 60),
        }
        try:
            panel, dataset_meta = self._dataset.load_panel(dataset_payload)
        except CrossSectionalDatasetError as exc:
            raise CrossSectionalFactorResearchError(
                exc.message, status_code=exc.status_code
            ) from exc

        warnings = list(dataset_meta.get("warnings") or [])
        warnings.extend(universe_disclosures(universe_id))
        unavailable = list(dataset_meta.get("unavailable_evidence") or [])
        if "sector_analysis" not in unavailable:
            unavailable.append("sector_analysis")

        factor_results: dict[tuple[str, int], dict[str, Any]] = {}
        all_ic_preview: list[dict[str, Any]] = []
        all_spread_preview: list[dict[str, Any]] = []
        rank_ic_by_key: dict[str, Any] = {}
        quintile_by_key: dict[str, Any] = {}
        spread_by_key: dict[str, Any] = {}
        turnover_by_key: dict[str, Any] = {}
        stability_by_key: dict[str, Any] = {}
        eligibility_totals = {
            "factor_label_date_evaluations": 0,
            "available_ic_dates": 0,
            "unavailable_ic_dates": 0,
        }

        for factor in factors:
            for horizon in horizons:
                label = _horizon_label(horizon)
                daily_ic = compute_daily_rank_ic(
                    panel,
                    factor=factor,
                    label=label,
                    horizon=horizon,
                    minimum_cross_section_size=min_cs,
                    apply_liquidity_filter=apply_liq,
                )
                ic_summary = summarize_rank_ic(daily_ic)
                q_rows, spread_rows = compute_daily_quantiles(
                    panel,
                    factor=factor,
                    label=label,
                    horizon=horizon,
                    quantile_count=quantile_count,
                    minimum_cross_section_size=min_cs,
                    minimum_quantile_size=min_q,
                    apply_liquidity_filter=apply_liq,
                )
                q_summary = summarize_quantiles(
                    q_rows, spread_rows, quantile_count=quantile_count
                )
                turnover_daily = compute_factor_turnover(
                    panel,
                    factor=factor,
                    label=label,
                    apply_liquidity_filter=apply_liq,
                    minimum_overlap=min_overlap,
                )
                turn_summary = summarize_turnover(turnover_daily)
                stab = summarize_stability(
                    daily_ic,
                    spread_rows,
                    minimum_period_dates=min_period_dates,
                )
                key = (factor, horizon)
                factor_results[key] = {
                    "label": label,
                    "rank_ic": ic_summary,
                    "quantiles": q_summary,
                    "turnover": turn_summary,
                    "stability": stab,
                    "unavailable_evidence": [
                        r.get("unavailable_reason")
                        for r in daily_ic
                        if r.get("status") != "available" and r.get("unavailable_reason")
                    ][:20],
                }
                key_s = f"{factor}|{horizon}"
                rank_ic_by_key[key_s] = ic_summary
                quintile_by_key[key_s] = q_summary
                spread_by_key[key_s] = {
                    "mean_top_minus_bottom": q_summary.get("mean_top_minus_bottom"),
                    "spread_volatility": q_summary.get("spread_volatility"),
                    "positive_spread_ratio": q_summary.get("positive_spread_ratio"),
                    "available_date_count": q_summary.get("available_date_count"),
                    "unavailable_date_count": q_summary.get("unavailable_date_count"),
                }
                turnover_by_key[key_s] = turn_summary
                stability_by_key[key_s] = stab
                eligibility_totals["factor_label_date_evaluations"] += len(daily_ic)
                eligibility_totals["available_ic_dates"] += int(
                    ic_summary.get("available_date_count") or 0
                )
                eligibility_totals["unavailable_ic_dates"] += int(
                    ic_summary.get("unavailable_date_count") or 0
                )
                all_ic_preview.extend(daily_ic)
                all_spread_preview.extend(spread_rows)

        corr_daily = compute_factor_correlations(
            panel,
            factors=factors,
            minimum_pairwise_size=min_cs,
            apply_liquidity_filter=apply_liq,
        )
        corr_summary = summarize_correlations(
            corr_daily, warning_threshold=corr_thresh
        )
        decay = build_decay_summary(factor_results)
        factor_summaries = build_factor_summaries(
            factor_results=factor_results,
            decay=decay,
            correlation_warnings=corr_summary.get("redundancy_warnings") or [],
        )

        seen: set[str] = set()
        unique_warnings: list[str] = []
        for w in warnings:
            text = str(w).strip()
            if text and text not in seen:
                seen.add(text)
                unique_warnings.append(text)

        configuration = {
            "research_id": research_id,
            "universe_id": universe_id,
            "universe_version": configured_universe_version(universe_id),
            "symbols": dataset_meta.get("symbols"),
            "start_date": dataset_meta.get("start_date"),
            "end_date": dataset_meta.get("end_date"),
            "factor_columns": factors,
            "label_horizons": horizons,
            "quantile_count": quantile_count,
            "minimum_cross_section_size": min_cs,
            "minimum_quantile_size": min_q,
            "apply_liquidity_filter": apply_liq,
            "correlation_warning_threshold": corr_thresh,
            "minimum_turnover_overlap": min_overlap,
            "minimum_stability_period_dates": min_period_dates,
            "preview_rows": preview_rows,
            "factor_version": FACTOR_VERSION,
            "conventions": {
                "rank_ic": "Spearman; average-rank ties; per date cross-section",
                "icir": "mean_rank_ic / std(rank_ic, ddof=1); not annualized",
                "quantiles": "Q1=lowest factor … Qn=highest; equal-weight forward returns; no costs",
                "turnover": "1 - Spearman(factor ranks) on adjacent-date overlap; range [0, 2]",
                "correlation": "pairwise Spearman of factor values; unordered pairs",
                "stability": "calendar-year grouping",
            },
        }

        if panel.empty:
            status = "failed"
        elif dataset_meta.get("quality_status") in {"failed", "incomplete"}:
            status = "incomplete"
        elif eligibility_totals["unavailable_ic_dates"] > 0:
            status = "incomplete"
        else:
            status = "completed"

        generated_at = utc_now_iso()
        result = {
            "research_id": research_id,
            "template": TEMPLATE_ID,
            "evidence_kind": EVIDENCE_KIND,
            "configuration": configuration,
            "dataset_summary": dataset_meta.get("dataset_summary") or {},
            "eligibility_summary": eligibility_totals,
            "rank_ic_summary": rank_ic_by_key,
            "quintile_summary": quintile_by_key,
            "spread_summary": spread_by_key,
            "decay_summary": decay,
            "turnover_summary": turnover_by_key,
            "correlation_summary": corr_summary,
            "stability_summary": stability_by_key,
            "factor_summaries": factor_summaries,
            "unavailable_evidence": unavailable,
            "previews": {
                "rank_ic": _bounded(all_ic_preview, preview_rows),
                "spreads": _bounded(all_spread_preview, preview_rows),
                "correlations": _bounded(corr_daily, preview_rows),
            },
            "warnings": unique_warnings,
            "provenance": dataset_meta.get("provenance") or {},
            "generated_at": generated_at,
            "validation_status": status,
        }
        providers = (dataset_meta.get("provenance") or {}).get("providers") or []
        result["reproducibility_manifest"] = build_reproducibility_manifest(
            data_source=providers[0] if len(providers) == 1 else (providers or None),
            universe={
                "universe_id": universe_id,
                "symbols": dataset_meta.get("loaded_symbols"),
            },
            requested_start_date=dataset_meta.get("start_date"),
            requested_end_date=dataset_meta.get("end_date"),
            row_count=(dataset_meta.get("dataset_summary") or {}).get("n_rows"),
            adjustment_mode="auto",
            protocol={
                "research_id": research_id,
                "evidence_kind": EVIDENCE_KIND,
                "universe_id": universe_id,
                "factors": factors,
                "horizons": horizons,
                "quantile_count": quantile_count,
                "minimum_cross_section_size": min_cs,
            },
            created_at=generated_at,
        )
        research_run_id = self._result_store.save(result)
        result["research_run_id"] = research_run_id
        return result
