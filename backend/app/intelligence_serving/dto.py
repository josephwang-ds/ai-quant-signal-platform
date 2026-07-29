"""Stable API DTO projections for the read-only intelligence query layer."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from app.intelligence.schemas import (
    ResearchArtifactType,
    ResearchRunStatus,
    ResearchRunType,
    ResearchSnapshotType,
)
from app.intelligence.snapshot_contracts import (
    ResearchSummarySnapshot,
    SignalSnapshot,
)


class IntelligenceErrorDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error_code: str
    message: str
    run_id: Optional[str] = None
    resource_id: Optional[str] = None


class ArtifactReferenceDTO(BaseModel):
    """Public artifact reference — no paths, no raw payload, no metadata."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    name: str
    artifact_type: ResearchArtifactType
    schema_version: str
    media_type: Optional[str] = None
    checksum_algorithm: str
    checksum: str
    size_bytes: int
    row_count: Optional[int] = None
    created_at: datetime


class SnapshotReferenceDTO(BaseModel):
    """Public snapshot reference — no paths, no metadata bag."""

    model_config = ConfigDict(extra="forbid")

    snapshot_id: str
    name: str
    snapshot_type: ResearchSnapshotType
    schema_version: str
    media_type: Optional[str] = None
    checksum_algorithm: str
    checksum: str
    size_bytes: int
    created_at: datetime
    as_of: Optional[datetime] = None
    source_artifact_ids: List[str] = Field(default_factory=list)


class ValidationRecordDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    checks: List[str] = Field(default_factory=list)


class ResearchRunSummaryDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    run_type: ResearchRunType
    status: ResearchRunStatus
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    universe: Optional[str] = None
    dataset_version: Optional[str] = None
    feature_version: Optional[str] = None
    model_version: Optional[str] = None
    git_commit: Optional[str] = None
    artifact_count: int
    snapshot_count: int


class ResearchRunDetailDTO(ResearchRunSummaryDTO):
    generator: Optional[str] = None
    environment: Optional[str] = None
    random_seed: Optional[int] = None
    training_window: Optional[str] = None
    prediction_window: Optional[str] = None
    notes: Optional[str] = None
    validation: ValidationRecordDTO
    errors: List[str] = Field(default_factory=list)
    artifacts: List[ArtifactReferenceDTO] = Field(default_factory=list)
    snapshots: List[SnapshotReferenceDTO] = Field(default_factory=list)


class RunListDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: List[ResearchRunSummaryDTO]
    count: int


class ArtifactListDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    items: List[ArtifactReferenceDTO]
    count: int


class SnapshotListDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    items: List[SnapshotReferenceDTO]
    count: int


class SnapshotContentDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    reference: SnapshotReferenceDTO
    content: Union[ResearchSummarySnapshot, SignalSnapshot]
