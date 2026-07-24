from __future__ import annotations

from typing import Any

from app.research_copilot.reviewer_schemas import DraftResearchDefinitionRequest
from app.research_copilot.reviewer_service import (
    ResearchReviewerError,
    ResearchReviewerService,
)
from app.research_guidance.schemas import ResearchGuidanceResponse
from app.research_guidance.templates import build_definition_template


class ResearchGuidanceError(Exception):
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ResearchGuidanceService:
    def __init__(
        self, reviewer: ResearchReviewerService | None = None
    ) -> None:
        self.reviewer = reviewer

    def execute(self, request: dict[str, Any]) -> dict[str, Any]:
        template = build_definition_template(request)
        if not request.get("use_llm"):
            return ResearchGuidanceResponse(**template).model_dump()
        if self.reviewer is None:
            raise ResearchGuidanceError(
                "Optional LLM guidance is not configured. The deterministic "
                "research-definition template remains available.",
                status_code=503,
            )

        try:
            reviewed = self.reviewer.draft_definition(
                DraftResearchDefinitionRequest(
                    research_type=request["research_type"],
                    symbol_or_universe=request["universe"],
                    parameters=request.get("parameters", {}),
                    date_range={
                        "start": request.get("start_date"),
                        "end": request.get("end_date"),
                    },
                    benchmark={
                        "type": request["benchmark_type"],
                        "name": template["primary_benchmark"],
                    },
                    transaction_cost=request.get("transaction_cost", 0.001),
                    available_validation_methods=request.get(
                        "available_validation", []
                    ),
                    known_system_limitations=request.get(
                        "known_limitations", []
                    ),
                )
            )
        except ResearchReviewerError as exc:
            raise ResearchGuidanceError(
                exc.message, status_code=exc.status_code
            ) from exc
        result = reviewed["result"]
        response = ResearchGuidanceResponse(
            research_question=result["research_question"],
            hypothesis=result["hypothesis"],
            null_hypothesis=result["null_hypothesis"],
            mechanism=result["mechanism"],
            primary_benchmark=result["primary_benchmark"]["name"],
            success_criteria=[
                {
                    "metric": item["metric"],
                    "operator": item["operator"],
                    "threshold_placeholder": item["threshold_guidance"],
                    "reason": item["reason"],
                }
                for item in result["proposed_success_criteria"]
            ],
            failure_criteria=[
                f"{item['condition']} — {item['reason']}"
                for item in result["failure_criteria"]
            ],
            required_validation=result["required_validation"],
            known_limitations=result["known_limitations"],
            clarifications_needed=result["clarifications_needed"],
            source="llm",
            model=reviewed["model"],
        )
        return response.model_dump()
