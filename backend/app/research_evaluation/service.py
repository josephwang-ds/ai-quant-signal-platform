"""SummarizeEvidence use case: the research governance layer.

PR-010 answers one question only: "Do we have enough trustworthy evidence to
continue research?" It never answers "should we buy?"

Evaluation is pure evidence aggregation over an *already-produced*
ValidationResult, identified by a ``validation_run_id`` minted by Validation.
It is not a second validation engine:

- It performs no market-data reads.
- It performs no MA-crossover, OOS, sensitivity, or cost calculations.
- It never calls ``ResearchValidationService.execute`` and has no dependency
  on ``ResearchValidationService`` at all — it depends only on
  ``ValidationResultStore``, reading exactly one stored payload per request.
- Allowed evaluation_status values are strictly ``completed``, ``incomplete``,
  or ``blocked`` — never a quality, confidence, or investment judgement.
"""

from __future__ import annotations

from typing import Any

from app.research_execution.market_data_port import utc_now_iso
from app.research_validation.result_store import ValidationResultStore
from app.research_validation.service import CANONICAL_RESEARCH_ID

# Implemented validation stages (PR-009), in canonical order. Labels match
# app.research_validation.service._stage(...) calls exactly so evidence_summary
# is a verbatim passthrough, not a re-derivation.
IMPLEMENTED_STAGE_LABELS: dict[str, str] = {
    "historical_backtest": "Historical backtest",
    "benchmark_comparison": "Benchmark comparison",
    "out_of_sample": "Out-of-sample validation",
    "parameter_sensitivity": "Parameter sensitivity",
    "transaction_cost_sensitivity": "Transaction-cost sensitivity",
    "data_quality": "Data quality",
}

# Validation capabilities that do not exist yet in this codebase. Always
# unavailable regardless of the outcome of implemented stages.
UNAVAILABLE_STAGES: tuple[str, ...] = (
    "Stress testing",
    "Regime analysis",
    "Walk-forward validation",
    "Monte Carlo simulation",
)

# Remaining evidence a reviewer would need before further governance
# decisions. Deliberately not phrased as strategy advice (no "improve Sharpe").
OUTSTANDING_EVIDENCE: tuple[str, ...] = UNAVAILABLE_STAGES + ("Paper trading",)

# Fixed, informational limitations. Never derived from this run's numbers.
LIMITATIONS: tuple[str, ...] = (
    "Evaluation is based on historical evidence only; it performs no new "
    "calculations.",
    "Independent benchmark comparison is unavailable; benchmark evidence "
    "uses same-asset buy-and-hold only.",
    "Stress testing is not implemented.",
    "Regime analysis is not implemented.",
    "Walk-forward validation is not implemented.",
    "Monte Carlo simulation is not implemented.",
    "Research has not been published.",
    "Paper trading is unavailable.",
)


class ResearchEvaluationError(Exception):
    """Application failure mapped by the HTTP adapter."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _deduplicate(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


class ResearchEvaluationService:
    """Aggregate one stored ValidationResult into a governance summary.

    This service depends only on ``ValidationResultStore``. It has no
    market-data-port dependency and no ``ResearchValidationService``
    dependency, so it is structurally unable to trigger a new Validation run.
    """

    def __init__(self, store: ValidationResultStore) -> None:
        self.store = store

    def execute(self, request: dict[str, Any]) -> dict[str, Any]:
        research_id = str(
            request.get("research_id", CANONICAL_RESEARCH_ID) or ""
        ).strip()
        if research_id != CANONICAL_RESEARCH_ID:
            raise ResearchEvaluationError(
                f"Unsupported research_id '{research_id}'. "
                f"Supported: ['{CANONICAL_RESEARCH_ID}']."
            )

        validation_run_id = str(request.get("validation_run_id") or "").strip()
        if not validation_run_id:
            raise ResearchEvaluationError(
                "validation_run_id is required. Run or load Validation "
                "evidence before Evaluation can be generated.",
                status_code=400,
            )

        # Exactly one read from storage. Evaluation never re-runs or
        # re-derives evidence, and never calls ResearchValidationService.
        stored = self.store.get(validation_run_id)
        if stored is None:
            raise ResearchEvaluationError(
                f"Unknown validation_run_id '{validation_run_id}'. Run or "
                "load Validation evidence before Evaluation can be "
                "generated.",
                status_code=404,
            )

        stored_research_id = stored.get("research_id")
        if stored_research_id != research_id:
            raise ResearchEvaluationError(
                f"validation_run_id '{validation_run_id}' belongs to "
                f"research '{stored_research_id}', not '{research_id}'.",
                status_code=400,
            )

        generated_at = utc_now_iso()
        return self._summarize(research_id, validation_run_id, stored, generated_at)

    def _summarize(
        self,
        research_id: str,
        validation_run_id: str,
        validation: dict[str, Any],
        generated_at: str,
    ) -> dict[str, Any]:
        stages = validation["stages"]
        evidence_summary = [
            {
                "stage": stage["stage"],
                "label": stage["label"],
                "status": stage["status"],
                "summary": stage["summary"],
            }
            for stage in stages
        ]
        completed_stages = [
            stage["label"] for stage in stages if stage["status"] == "completed"
        ]
        incomplete_stages = [
            stage["label"] for stage in stages if stage["status"] != "completed"
        ]
        has_failed = any(stage["status"] == "failed" for stage in stages)
        has_incomplete = any(stage["status"] == "incomplete" for stage in stages)
        evaluation_status = (
            "blocked"
            if has_failed
            else "incomplete"
            if has_incomplete
            else "completed"
        )

        implemented_count = len(stages)
        completed_count = len(completed_stages)
        coverage_percentage = (
            round(completed_count / implemented_count * 100, 2)
            if implemented_count
            else 0.0
        )

        blockers = _deduplicate(
            [blocker for stage in stages for blocker in stage["blockers"]]
        )

        return {
            "research_id": research_id,
            "evaluation_status": evaluation_status,
            "evidence_summary": evidence_summary,
            "evidence_coverage": {
                "implemented_stage_count": implemented_count,
                "completed_stage_count": completed_count,
                "coverage_percentage": coverage_percentage,
            },
            "completed_stages": completed_stages,
            "incomplete_stages": incomplete_stages,
            "unavailable_stages": list(UNAVAILABLE_STAGES),
            "blockers": blockers,
            "limitations": list(LIMITATIONS),
            "outstanding_evidence": list(OUTSTANDING_EVIDENCE),
            "provenance": {
                "research_id": research_id,
                "validation_run_id": validation_run_id,
                "validation_generated_at": validation["generated_at"],
                "market_data_provenance": validation["provenance"],
            },
            "generated_at": generated_at,
        }
