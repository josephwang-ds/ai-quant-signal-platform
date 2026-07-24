from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.research_guidance.schemas import (
    ResearchGuidanceRequest,
    ResearchGuidanceResponse,
)
from app.research_guidance.service import (
    ResearchGuidanceError,
    ResearchGuidanceService,
)
from app.research_copilot.reviewer_service import ResearchReviewerService

router = APIRouter(prefix="/api/v1/research", tags=["research-guidance"])


def get_research_guidance_service(use_llm: bool) -> ResearchGuidanceService:
    if not use_llm:
        return ResearchGuidanceService()
    try:
        from app.research_copilot.service import resolve_llm_adapter

        return ResearchGuidanceService(
            ResearchReviewerService(resolve_llm_adapter())
        )
    except ResearchGuidanceError:
        raise
    except Exception as exc:
        raise ResearchGuidanceError(
            "Optional LLM guidance is not configured. The deterministic "
            "research-definition template remains available.",
            status_code=503,
        ) from exc


@router.post("/guidance/definition", response_model=ResearchGuidanceResponse)
def research_definition_guidance(
    body: ResearchGuidanceRequest,
) -> ResearchGuidanceResponse:
    try:
        result = get_research_guidance_service(body.use_llm).execute(
            body.model_dump()
        )
    except ResearchGuidanceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return ResearchGuidanceResponse(**result)
