"""Normalize stored validation results into the Agent's read-only evidence contract."""

from __future__ import annotations

from typing import Any

TREND_REQUIRED_EVIDENCE = (
    "execution",
    "benchmark",
    "validation",
    "oos",
    "parameter_sensitivity",
    "cost_sensitivity",
    "data_quality",
)

FACTOR_REQUIRED_EVIDENCE = (
    "factor_validation",
    "benchmark",
    "rank_ic",
)

_TREND_STAGE_KEYS = {
    "historical_backtest": "execution",
    "benchmark_comparison": "benchmark",
    "out_of_sample": "oos",
    "parameter_sensitivity": "parameter_sensitivity",
    "transaction_cost_sensitivity": "cost_sensitivity",
    "data_quality": "data_quality",
}


def normalize_stages(value: Any) -> dict[str, dict[str, Any]]:
    """Accept both the production list envelope and legacy dict fixtures."""
    if isinstance(value, dict):
        return {
            str(name): stage
            for name, stage in value.items()
            if isinstance(stage, dict)
        }
    if not isinstance(value, list):
        return {}
    stages: dict[str, dict[str, Any]] = {}
    for stage in value:
        if not isinstance(stage, dict):
            continue
        name = str(stage.get("stage") or "").strip()
        if name:
            stages[name] = stage
    return stages


def stage_completed(stage: dict[str, Any] | None) -> bool:
    return bool(stage) and str(stage.get("status") or "").lower() == "completed"


def benchmark_from_snapshot(stored: dict[str, Any]) -> dict[str, Any]:
    benchmark = stored.get("benchmark_evaluation")
    if not isinstance(benchmark, dict):
        benchmark = stored.get("benchmark")
    return benchmark if isinstance(benchmark, dict) else {}


def required_evidence(research_type: str | None) -> tuple[str, ...]:
    return (
        FACTOR_REQUIRED_EVIDENCE
        if research_type == "factor"
        else TREND_REQUIRED_EVIDENCE
    )


def _benchmark_summary(benchmark: dict[str, Any]) -> dict[str, Any]:
    checks = benchmark.get("checks") or []
    return {
        "verdict": benchmark.get("verdict"),
        "rationale": benchmark.get("rationale"),
        "primary_benchmark": benchmark.get("primary_benchmark"),
        "checks": [
            {
                "check_id": item.get("check_id"),
                "status": item.get("status"),
                "observed_value": item.get("observed_value"),
                "configured_threshold": item.get("configured_threshold"),
                "severity": item.get("severity"),
            }
            for item in checks
            if isinstance(item, dict)
        ],
    }


def _trend_stage_summaries(
    stages: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    summaries: dict[str, dict[str, Any]] = {}
    selected_evidence_keys = {
        "historical_backtest": ("metrics",),
        "benchmark_comparison": (
            "excess_total_return",
            "excess_sharpe_ratio",
        ),
        "out_of_sample": (
            "split_date",
            "in_sample_ratio",
            "out_of_sample_return_rows",
            "minimum_oos_observations",
            "out_of_sample_metrics",
            "oos_benchmark_metrics",
        ),
        "parameter_sensitivity": (
            "status",
            "valid_combination_count",
            "profitable_combination_count",
            "positive_sharpe_count",
            "median_sharpe",
            "sharpe_range",
            "canonical_percentile_by_sharpe",
        ),
        "transaction_cost_sensitivity": (
            "status",
            "canonical_cost",
            "canonical_cost_result",
            "descriptive_summary",
        ),
        "data_quality": ("checks", "informational"),
    }
    for name, stage in stages.items():
        evidence = stage.get("evidence") or {}
        if not isinstance(evidence, dict):
            evidence = {}
        selected = selected_evidence_keys.get(name, ())
        selected_evidence = {
            key: evidence.get(key) for key in selected if key in evidence
        }
        if name == "data_quality":
            checks = evidence.get("checks") or []
            selected_evidence["checks"] = [
                {
                    "name": item.get("name"),
                    "severity": item.get("severity"),
                    "status": item.get("status"),
                    "summary": item.get("summary"),
                }
                for item in checks
                if isinstance(item, dict)
            ]
        summaries[name] = {
            "status": stage.get("status"),
            "summary": stage.get("summary"),
            "evidence": selected_evidence,
            "warnings": stage.get("warnings") or [],
            "blockers": stage.get("blockers") or [],
        }
    return summaries


def build_evidence_snapshot(
    stored: dict[str, Any],
    *,
    research_type: str | None,
) -> dict[str, Any]:
    """Build the stable evidence view consumed by completeness and LLM context."""
    stages = normalize_stages(stored.get("stages"))
    benchmark = benchmark_from_snapshot(stored)
    validation_status = str(stored.get("validation_status") or "").lower()
    is_factor = (
        research_type == "factor"
        or stored.get("evidence_kind") == "factor_validation"
        or stored.get("template") == "cross_sectional_factor"
    )
    ic_summary = ((stored.get("ic") or {}).get("summary")) or {}
    if not isinstance(ic_summary, dict):
        ic_summary = {}

    completed_stages = {
        name for name, stage in stages.items() if stage_completed(stage)
    }
    failed_stages = {
        name
        for name, stage in stages.items()
        if str(stage.get("status") or "").lower() == "failed"
    }

    if is_factor:
        factor_complete = validation_status == "completed"
        availability = {
            "execution": False,
            "benchmark": bool(benchmark),
            "validation": factor_complete,
            "factor_validation": factor_complete,
            "oos": False,
            "parameter_sensitivity": False,
            "cost_sensitivity": False,
            "data_quality": False,
            "rank_ic": ic_summary.get("mean_rank_ic") is not None,
            "robustness": factor_complete,
            "validation_failed": validation_status == "failed",
            "known_limitations": False,
        }
    else:
        availability = {
            "execution": "historical_backtest" in completed_stages
            or bool(stored.get("execution") or stored.get("metrics")),
            "benchmark": "benchmark_comparison" in completed_stages
            and bool(benchmark),
            "validation": validation_status == "completed",
            "factor_validation": False,
            "oos": "out_of_sample" in completed_stages,
            "parameter_sensitivity": "parameter_sensitivity" in completed_stages,
            "cost_sensitivity": "transaction_cost_sensitivity"
            in completed_stages,
            "data_quality": "data_quality" in completed_stages,
            "rank_ic": False,
            "robustness": all(
                name in completed_stages
                for name in (
                    "out_of_sample",
                    "parameter_sensitivity",
                    "transaction_cost_sensitivity",
                )
            ),
            "validation_failed": validation_status == "failed"
            or bool(failed_stages),
            "known_limitations": False,
        }

    evidence_ids = ["snapshot:root"]
    if availability["benchmark"]:
        evidence_ids.append("evidence:benchmark")
    if availability["rank_ic"]:
        evidence_ids.extend(["evidence:mean_rank_ic", "evidence:icir"])
    for stage_name, availability_key in _TREND_STAGE_KEYS.items():
        if availability.get(availability_key):
            evidence_ids.append(f"evidence:{availability_key}")

    return {
        "validation_run_id": stored.get("validation_run_id"),
        "generated_at": stored.get("generated_at"),
        "evidence_kind": stored.get("evidence_kind") or stored.get("template"),
        "research_type": "factor" if is_factor else "trend_following",
        "validation_status": validation_status or None,
        "availability": availability,
        "required_evidence": list(required_evidence("factor" if is_factor else research_type)),
        "evidence_ids": list(dict.fromkeys(evidence_ids)),
        "ic_summary": ic_summary or None,
        "benchmark": _benchmark_summary(benchmark),
        "evidence_details": (
            {
                "ic_summary": ic_summary,
                "long_short": stored.get("long_short") or {},
                "quantiles": {
                    "n_rebalances": (stored.get("quantiles") or {}).get(
                        "n_rebalances"
                    ),
                    "turnover": (stored.get("quantiles") or {}).get("turnover"),
                    "transaction_cost": (stored.get("quantiles") or {}).get(
                        "transaction_cost"
                    ),
                },
            }
            if is_factor
            else {"stages": _trend_stage_summaries(stages)}
        ),
        "warnings": stored.get("warnings") or [],
        "metric_refs": {
            "mean_rank_ic": ic_summary.get("mean_rank_ic"),
            "icir": ic_summary.get("icir"),
            "stages_present": sorted(stages),
            "stages_completed": sorted(completed_stages),
            "stages_failed": sorted(failed_stages),
        },
    }


def robustness_results(stored: dict[str, Any]) -> dict[str, dict[str, Any]]:
    stages = normalize_stages(stored.get("stages"))
    return {
        name: stages[name]
        for name in (
            "out_of_sample",
            "parameter_sensitivity",
            "transaction_cost_sensitivity",
            "data_quality",
        )
        if name in stages
    }
