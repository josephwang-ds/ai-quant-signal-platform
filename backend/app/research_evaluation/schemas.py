"""Transport contracts for the research evaluation governance layer.

Evaluation never recalculates strategy performance. It only summarizes
evidence already produced by PR-009 validation.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class ResearchEvaluationRequest(BaseModel):
    """SummarizeEvidence input.

    ``validation_run_id`` must reference a ValidationResult already saved by
    a prior ``POST /api/v1/research/validation`` call. Evaluation never
    triggers a new Validation run, so this field has no default: callers
    without a validation_run_id must run or load Validation evidence first.
    """

    model_config = ConfigDict(extra="forbid")

    research_id: str = "ma-crossover-spy"
    validation_run_id: str


class EvidenceSummaryItem(BaseModel):
    """One implemented validation stage's status, reused verbatim (no recalculation)."""

    stage: str
    label: str
    status: str
    summary: str


class EvidenceCoverage(BaseModel):
    """Implementation coverage only — never confidence, quality, or robustness."""

    implemented_stage_count: int
    completed_stage_count: int
    coverage_percentage: float


class ResearchEvaluationResponse(BaseModel):
    research_id: str
    evaluation_status: str
    evidence_summary: list[EvidenceSummaryItem]
    evidence_coverage: EvidenceCoverage
    completed_stages: list[str]
    incomplete_stages: list[str]
    unavailable_stages: list[str]
    blockers: list[str]
    limitations: list[str]
    outstanding_evidence: list[str]
    provenance: dict[str, Any]
    generated_at: str
