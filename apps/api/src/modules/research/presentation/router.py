"""Research 模块 HTTP 适配器。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from modules.research.application.commands.create_research_command import (
    CreateResearchCommand,
)
from modules.research.application.commands.create_research_handler import (
    CreateResearchHandler,
)
from modules.research.application.dto.research_dto import (
    CreateResearchRequest,
    ResearchResponse,
)
from shared.errors.domain_error import DomainError, ValidationError

router = APIRouter(prefix="/api/research", tags=["research"])


def get_create_research_handler(request: Request) -> CreateResearchHandler:
    """从应用状态解析 CreateResearchHandler（由 bootstrap 注入）。"""
    handler = getattr(request.app.state, "create_research_handler", None)
    if handler is None:
        raise RuntimeError("CreateResearchHandler is not configured on app.state.")
    return handler


@router.post(
    "",
    response_model=ResearchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Research",
)
def create_research(
    body: CreateResearchRequest,
    handler: CreateResearchHandler = Depends(get_create_research_handler),
) -> ResearchResponse:
    """CreateResearch 用例入口。"""
    command = CreateResearchCommand(
        strategy_id=body.strategy_id,
        title=body.title,
        objective=body.objective,
        owner=body.owner,
        notes=body.notes,
    )
    try:
        return handler.handle(command)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": exc.code, "message": exc.message, "field": exc.field},
        ) from exc
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": exc.code, "message": exc.message},
        ) from exc
