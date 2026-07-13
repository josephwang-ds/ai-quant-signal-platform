"""CreateResearch 领域与应用层单元测试。"""

from __future__ import annotations

from uuid import uuid4

import pytest

from modules.research.application.commands.create_research_command import (
    CreateResearchCommand,
)
from modules.research.application.commands.create_research_handler import (
    CreateResearchHandler,
)
from modules.research.application.commands.create_research_validator import (
    CreateResearchValidator,
)
from modules.research.domain.research import Research, ResearchState
from modules.research.infrastructure.repositories.in_memory_research_repository import (
    InMemoryResearchRepository,
)
from shared.errors.domain_error import DomainError, ValidationError


def test_research_create_starts_in_draft() -> None:
    strategy_id = uuid4()
    research = Research.create(
        strategy_id=strategy_id,
        title=" Momentum fade study ",
        objective=" Test whether short-horizon fade persists after shocks. ",
        owner=" research-owner@example.com ",
        notes="  ",
    )

    assert research.state is ResearchState.DRAFT
    assert research.title == "Momentum fade study"
    assert research.objective.startswith("Test whether")
    assert research.owner == "research-owner@example.com"
    assert research.notes is None
    assert research.strategy_id == strategy_id
    assert research.version == 1


@pytest.mark.parametrize(
    ("kwargs", "code"),
    [
        ({"title": "  ", "objective": "o", "owner": "a"}, "research.title_required"),
        ({"title": "t", "objective": " ", "owner": "a"}, "research.objective_required"),
        ({"title": "t", "objective": "o", "owner": ""}, "research.owner_required"),
    ],
)
def test_research_create_rejects_blank_fields(kwargs: dict, code: str) -> None:
    with pytest.raises(DomainError) as exc:
        Research.create(strategy_id=uuid4(), **kwargs)
    assert exc.value.code == code


def test_validator_rejects_oversized_title() -> None:
    validator = CreateResearchValidator()
    command = CreateResearchCommand(
        strategy_id=uuid4(),
        title="x" * 201,
        objective="valid objective",
        owner="owner",
    )
    with pytest.raises(ValidationError) as exc:
        validator.validate(command)
    assert exc.value.field == "title"


def test_handler_persists_and_returns_dto() -> None:
    repo = InMemoryResearchRepository()
    handler = CreateResearchHandler(repository=repo)
    strategy_id = uuid4()

    result = handler.handle(
        CreateResearchCommand(
            strategy_id=strategy_id,
            title="Mean reversion probe",
            objective="Quantify half-life of residual returns.",
            owner="alice",
            notes="slice-1",
        )
    )

    assert result.state == ResearchState.DRAFT.value
    assert result.strategy_id == strategy_id
    stored = repo.get_by_id(result.id)
    assert stored is not None
    assert stored.title == "Mean reversion probe"
    assert result.notes == "slice-1"


def test_handler_rejects_invalid_command_before_persist() -> None:
    repo = InMemoryResearchRepository()
    handler = CreateResearchHandler(repository=repo)

    with pytest.raises(ValidationError):
        handler.handle(
            CreateResearchCommand(
                strategy_id=uuid4(),
                title="",
                objective="objective",
                owner="owner",
            )
        )
    assert repo.get_by_id(uuid4()) is None
