"""Pydantic contracts for Research Copilot API."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.security.limits import (
    MAX_CONVERSATION_TURN_LENGTH,
    MAX_QUESTION_LENGTH,
)

GroundingStatus = Literal["grounded", "partially_grounded", "unavailable"]


class CopilotConversationTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=MAX_CONVERSATION_TURN_LENGTH)


class ResearchCopilotRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_id: str = "ma-crossover-spy"
    validation_run_id: str = Field(min_length=1)
    question: str = Field(min_length=1, max_length=MAX_QUESTION_LENGTH)
    conversation: list[CopilotConversationTurn] = Field(default_factory=list, max_length=6)


class EvidenceCitation(BaseModel):
    source_type: str
    source_id: str
    label: str
    excerpt: str


class CopilotWarning(BaseModel):
    code: str
    message: str


class FactorCopilotSummary(BaseModel):
    """Evidence-only Factor Research summary. Metrics are strings from stored evidence."""

    model_config = ConfigDict(extra="forbid")

    rank_ic: str
    icir: str
    turnover: str
    long_short_return: str
    stability: str
    warnings: list[str] = Field(default_factory=list)
    citation_ids: list[str] = Field(default_factory=list)


class ResearchCopilotResponse(BaseModel):
    research_id: str
    answer: str
    citations: list[EvidenceCitation]
    warnings: list[CopilotWarning]
    grounding_status: GroundingStatus
    model: str
    generated_at: str
    factor_summary: Optional[FactorCopilotSummary] = None
