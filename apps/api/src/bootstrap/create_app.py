"""API 应用装配：仅挂载已实现的垂直切片。"""

from __future__ import annotations

from fastapi import FastAPI

from modules.research.application.commands.create_research_handler import (
    CreateResearchHandler,
)
from modules.research.application.commands.create_research_validator import (
    CreateResearchValidator,
)
from modules.research.infrastructure.repositories.in_memory_research_repository import (
    InMemoryResearchRepository,
)
from modules.research.presentation.router import router as research_router


def create_app(
    *,
    research_repository: InMemoryResearchRepository | None = None,
) -> FastAPI:
    """
    创建 FastAPI 应用并注入 Research CreateResearch 依赖。

    仓储默认为内存 Stub；生产替换点在此装配，不渗入 Handler。
    """
    app = FastAPI(
        title="AI Quant Research Workspace API",
        description="Modular monolith API. First vertical slice: Research / CreateResearch.",
    )

    repository = research_repository or InMemoryResearchRepository()
    handler = CreateResearchHandler(
        repository=repository,
        validator=CreateResearchValidator(),
    )
    app.state.research_repository = repository
    app.state.create_research_handler = handler
    app.include_router(research_router)
    return app
