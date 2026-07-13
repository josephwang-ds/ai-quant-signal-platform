"""CreateResearch 命令处理器。"""

from __future__ import annotations

from modules.research.application.commands.create_research_command import (
    CreateResearchCommand,
)
from modules.research.application.commands.create_research_validator import (
    CreateResearchValidator,
)
from modules.research.application.dto.research_dto import ResearchResponse
from modules.research.domain.repository import ResearchRepository
from modules.research.domain.research import Research


class CreateResearchHandler:
    """编排校验 → 领域构造 → 持久化 → DTO 映射。"""

    def __init__(
        self,
        repository: ResearchRepository,
        validator: CreateResearchValidator | None = None,
    ) -> None:
        self._repository = repository
        self._validator = validator or CreateResearchValidator()

    def handle(self, command: CreateResearchCommand) -> ResearchResponse:
        self._validator.validate(command)
        research = Research.create(
            strategy_id=command.strategy_id,
            title=command.title,
            objective=command.objective,
            owner=command.owner,
            notes=command.notes,
        )
        saved = self._repository.save(research)
        return ResearchResponse.from_entity(saved)
