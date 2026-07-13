"""CreateResearch 命令校验器。"""

from __future__ import annotations

from modules.research.application.commands.create_research_command import (
    CreateResearchCommand,
)
from shared.errors.domain_error import ValidationError

_MAX_TITLE_LEN = 200
_MAX_OBJECTIVE_LEN = 4000
_MAX_OWNER_LEN = 120
_MAX_NOTES_LEN = 4000


class CreateResearchValidator:
    """校验 CreateResearchCommand 的语法与基础业务约束。"""

    def validate(self, command: CreateResearchCommand) -> None:
        if command.strategy_id is None:
            raise ValidationError("strategy_id is required.", field="strategy_id")

        title = (command.title or "").strip()
        if not title:
            raise ValidationError("title is required.", field="title")
        if len(title) > _MAX_TITLE_LEN:
            raise ValidationError(
                f"title must be at most {_MAX_TITLE_LEN} characters.",
                field="title",
            )

        objective = (command.objective or "").strip()
        if not objective:
            raise ValidationError("objective is required.", field="objective")
        if len(objective) > _MAX_OBJECTIVE_LEN:
            raise ValidationError(
                f"objective must be at most {_MAX_OBJECTIVE_LEN} characters.",
                field="objective",
            )

        owner = (command.owner or "").strip()
        if not owner:
            raise ValidationError("owner is required.", field="owner")
        if len(owner) > _MAX_OWNER_LEN:
            raise ValidationError(
                f"owner must be at most {_MAX_OWNER_LEN} characters.",
                field="owner",
            )

        if command.notes is not None and len(command.notes) > _MAX_NOTES_LEN:
            raise ValidationError(
                f"notes must be at most {_MAX_NOTES_LEN} characters.",
                field="notes",
            )
