"""Research 读写 DTO。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.research.domain.research import Research


class CreateResearchRequest(BaseModel):
    """HTTP / 外部边界入参。"""

    model_config = ConfigDict(extra="forbid")

    strategy_id: UUID
    title: str = Field(min_length=1, max_length=200)
    objective: str = Field(min_length=1, max_length=4000)
    owner: str = Field(min_length=1, max_length=120)
    notes: Optional[str] = Field(default=None, max_length=4000)


class ResearchResponse(BaseModel):
    """Research 对外只读投影。"""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    strategy_id: UUID
    title: str
    objective: str
    owner: str
    state: str
    notes: Optional[str]
    version: int
    created_at: datetime

    @classmethod
    def from_entity(cls, research: Research) -> ResearchResponse:
        return cls(
            id=research.id,
            strategy_id=research.strategy_id,
            title=research.title,
            objective=research.objective,
            owner=research.owner,
            state=research.state.value,
            notes=research.notes,
            version=research.version,
            created_at=research.created_at,
        )
