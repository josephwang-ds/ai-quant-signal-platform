"""Research 聚合根：有界探究程序的身份与状态。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from shared.errors.domain_error import DomainError


class ResearchState(str, Enum):
    """Research 业务状态（对齐 Architecture Bible Ch3）。"""

    DRAFT = "Draft"
    PLANNING = "Planning"
    RUNNING = "Running"
    SYNTHESIZING = "Synthesizing"
    REVIEWED = "Reviewed"
    CLOSED = "Closed"
    REOPENED = "Reopened"


@dataclass(frozen=True)
class Research:
    """
    Research 聚合根。

    CreateResearch 仅允许创建为 Draft。
    后续状态迁移由独立用例处理，禁止在本切片内隐式推进。
    """

    id: UUID
    strategy_id: UUID
    title: str
    objective: str
    owner: str
    state: ResearchState
    created_at: datetime
    notes: str | None = None
    version: int = field(default=1)

    @classmethod
    def create(
        cls,
        *,
        strategy_id: UUID,
        title: str,
        objective: str,
        owner: str,
        notes: str | None = None,
        research_id: UUID | None = None,
        created_at: datetime | None = None,
    ) -> Research:
        """工厂：新建 Research，初始状态固定为 Draft。"""
        normalized_title = title.strip()
        normalized_objective = objective.strip()
        normalized_owner = owner.strip()

        if not normalized_title:
            raise DomainError("Research title is required.", code="research.title_required")
        if not normalized_objective:
            raise DomainError(
                "Research objective is required.",
                code="research.objective_required",
            )
        if not normalized_owner:
            raise DomainError("Research owner is required.", code="research.owner_required")

        return cls(
            id=research_id or uuid4(),
            strategy_id=strategy_id,
            title=normalized_title,
            objective=normalized_objective,
            owner=normalized_owner,
            state=ResearchState.DRAFT,
            created_at=created_at or datetime.now(timezone.utc),
            notes=notes.strip() if notes and notes.strip() else None,
            version=1,
        )
