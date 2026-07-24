"""POST/GET Research Governance Agent runs — LangGraph workflow transport."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.research_agent.schemas import (
    AgentResumeRequest,
    AgentRunCreateRequest,
    AgentRunDetailResponse,
    AgentRunSummaryResponse,
)
from app.research_agent.service import GovernanceAgentService, ResearchAgentError
from app.api.routes.factor_validation import get_factor_validation_service
from app.api.routes.research_execution import get_research_execution_service
from app.api.routes.research_validation import get_research_validation_service
from app.research_validation.result_store import get_default_validation_result_store

router = APIRouter(prefix="/api/v1/research/agent", tags=["research-agent"])

_service: GovernanceAgentService | None = None


def get_governance_agent_service() -> GovernanceAgentService:
    global _service
    if _service is None:
        store = get_default_validation_result_store()
        _service = GovernanceAgentService(
            store,
            validation_service=get_research_validation_service(),
            factor_validation_service=get_factor_validation_service(),
            execution_service=get_research_execution_service(),
        )
    return _service


def set_governance_agent_service(service: GovernanceAgentService | None) -> None:
    global _service
    _service = service


@router.post("/runs", response_model=AgentRunSummaryResponse)
def create_agent_run(body: AgentRunCreateRequest) -> AgentRunSummaryResponse:
    try:
        result = get_governance_agent_service().create_run(body.model_dump())
    except ResearchAgentError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return AgentRunSummaryResponse(**result)


@router.get("/runs/{agent_run_id}", response_model=AgentRunDetailResponse)
def get_agent_run(agent_run_id: str) -> AgentRunDetailResponse:
    try:
        result = get_governance_agent_service().get_run(agent_run_id)
    except ResearchAgentError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return AgentRunDetailResponse(**result)


@router.post("/runs/{agent_run_id}/resume", response_model=AgentRunDetailResponse)
def resume_agent_run(agent_run_id: str, body: AgentResumeRequest) -> AgentRunDetailResponse:
    try:
        result = get_governance_agent_service().resume_run(
            agent_run_id, body.action, body.payload
        )
    except ResearchAgentError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return AgentRunDetailResponse(**result)


@router.post("/runs/{agent_run_id}/cancel", response_model=AgentRunDetailResponse)
def cancel_agent_run(agent_run_id: str) -> AgentRunDetailResponse:
    try:
        result = get_governance_agent_service().cancel_run(agent_run_id)
    except ResearchAgentError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return AgentRunDetailResponse(**result)
