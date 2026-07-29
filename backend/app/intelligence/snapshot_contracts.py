"""Consumer-facing intelligence snapshot contracts (Phase 4.3).

These are stable, immutable projections for intelligence consumers.
They summarize registered research artifacts but are not unrestricted copies
of domain research payloads.

Identity timestamps (``generated_at``) and ``snapshot_id`` may differ across
builds; content fields excluding identity/time must remain deterministic for
identical explicit inputs.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.intelligence.schemas import ResearchRunType, require_aware_utc

RESEARCH_SUMMARY_SCHEMA_VERSION = "research-summary-snapshot/v1"
SIGNAL_SNAPSHOT_SCHEMA_VERSION = "signal-snapshot/v1"


class ValidationStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    UNKNOWN = "unknown"


class SignalDirection(str, Enum):
    STRONG_NEGATIVE = "strong_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    STRONG_POSITIVE = "strong_positive"


class SnapshotFinding(BaseModel):
    """Typed key finding — supplied explicitly; never invented by the builder."""

    model_config = ConfigDict(extra="forbid")

    code: Optional[str] = None
    statement: str
    category: Optional[str] = None

    @field_validator("statement")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("finding statement must be non-empty")
        return cleaned


class SnapshotLimitation(BaseModel):
    """Typed limitation — supplied explicitly; never invented by the builder."""

    model_config = ConfigDict(extra="forbid")

    code: Optional[str] = None
    statement: str

    @field_validator("statement")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("limitation statement must be non-empty")
        return cleaned


class ArtifactSummaryItem(BaseModel):
    """Lightweight registry-facing artifact index entry (not domain metrics)."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    name: str
    artifact_type: str


class SnapshotContentProvenance(BaseModel):
    """Provenance embedded in snapshot *content* (consumer contract)."""

    model_config = ConfigDict(extra="forbid")

    source_artifact_ids: list[str] = Field(default_factory=list)
    builder: str
    notes: Optional[str] = None


class ResearchSummarySnapshot(BaseModel):
    """Consumer contract: research summary for one published research path."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = RESEARCH_SUMMARY_SCHEMA_VERSION
    generated_at: datetime
    as_of: Optional[datetime] = None
    research_title: Optional[str] = None
    research_objective: Optional[str] = None
    run_type: Optional[ResearchRunType] = None
    universe: Optional[str] = None
    analysis_window: Optional[str] = None
    validation_status: ValidationStatus = ValidationStatus.UNKNOWN
    key_findings: list[SnapshotFinding] = Field(default_factory=list)
    limitations: list[SnapshotLimitation] = Field(default_factory=list)
    artifact_summary: list[ArtifactSummaryItem] = Field(default_factory=list)
    provenance: SnapshotContentProvenance

    @field_validator("generated_at", "as_of")
    @classmethod
    def _aware(cls, value: Optional[datetime]) -> Optional[datetime]:
        return require_aware_utc(value)


class SignalRecord(BaseModel):
    """One normalized consumer-facing signal — not auto-derived from factors."""

    model_config = ConfigDict(extra="forbid")

    symbol: str
    signal_name: str
    direction: SignalDirection
    score: Optional[float] = Field(
        default=None,
        description=(
            "Optional normalized score supplied by the caller. "
            "Not assumed to be a probability. Null when unavailable."
        ),
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional confidence in [0, 1] when the producer supplies it.",
    )
    horizon: Optional[str] = None
    evidence_artifact_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("symbol", "signal_name")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("symbol and signal_name must be non-empty")
        return cleaned

    @field_validator("score", "confidence")
    @classmethod
    def _finite(cls, value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError("score/confidence cannot be NaN or Infinity")
        return value


class SignalSnapshot(BaseModel):
    """Consumer contract: normalized signals with evidence provenance."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = SIGNAL_SNAPSHOT_SCHEMA_VERSION
    generated_at: datetime
    as_of: Optional[datetime] = None
    universe: Optional[str] = None
    signals: list[SignalRecord] = Field(default_factory=list)
    provenance: SnapshotContentProvenance

    @field_validator("generated_at", "as_of")
    @classmethod
    def _aware(cls, value: Optional[datetime]) -> Optional[datetime]:
        return require_aware_utc(value)
