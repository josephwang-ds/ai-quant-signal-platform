"""Pydantic contracts for Research Copilot API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

GroundingStatus = Literal["grounded", "partially_grounded", "unavailable"]


class CopilotConversationTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ResearchCopilotRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_id: str = "ma-crossover-spy"
    validation_run_id: str = Field(min_length=1)
    question: str = Field(min_length=1, max_length=1000)
    conversation: list[CopilotConversationTurn] = Field(default_factory=list, max_length=6)


class EvidenceCitation(BaseModel):
    source_type: str
    source_id: str
    label: str
    excerpt: str


class CopilotWarning(BaseModel):
    code: str
    message: str


class ResearchCopilotResponse(BaseModel):
    research_id: str
    answer: str
    citations: list[EvidenceCitation]
    warnings: list[CopilotWarning]
    grounding_status: GroundingStatus
    model: str
    generated_at: str
