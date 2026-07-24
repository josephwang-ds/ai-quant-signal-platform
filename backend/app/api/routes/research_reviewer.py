from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.research_copilot.reviewer_schemas import (
    CompletionReviewRequest,
    DraftResearchDefinitionRequest,
    EvidenceReviewRequest,
    HypothesisReviewRequest,
    ResearchReviewerResponse,
)
from app.research_copilot.reviewer_service import (
    ResearchReviewerError,
    ResearchReviewerService,
)

router = APIRouter(prefix="/api/v1/research/reviewer", tags=["research-reviewer"])


def get_research_reviewer_service() -> ResearchReviewerService:
    try:
        from app.research_copilot.service import resolve_llm_adapter

        return ResearchReviewerService(resolve_llm_adapter())
    except ResearchReviewerError:
        raise
    except Exception as exc:
        raise ResearchReviewerError(
            "AI Research Reviewer is not configured for this deployment. "
            "Deterministic research remains available.",
            status_code=503,
        ) from exc


def _run(method: str, body) -> ResearchReviewerResponse:
    try:
        service = get_research_reviewer_service()
        result = getattr(service, method)(body)
    except ResearchReviewerError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return ResearchReviewerResponse(**result)


@router.post("/draft-definition", response_model=ResearchReviewerResponse)
def draft_definition(
    body: DraftResearchDefinitionRequest,
) -> ResearchReviewerResponse:
    return _run("draft_definition", body)


@router.post("/review-hypothesis", response_model=ResearchReviewerResponse)
def review_hypothesis(body: HypothesisReviewRequest) -> ResearchReviewerResponse:
    return _run("review_hypothesis", body)


@router.post("/review-evidence", response_model=ResearchReviewerResponse)
def review_evidence(body: EvidenceReviewRequest) -> ResearchReviewerResponse:
    return _run("review_evidence", body)


@router.post("/identify-missing-steps", response_model=ResearchReviewerResponse)
def identify_missing_steps(
    body: CompletionReviewRequest,
) -> ResearchReviewerResponse:
    return _run("identify_missing_steps", body)
