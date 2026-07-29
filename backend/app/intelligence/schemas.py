"""Typed schemas for research run registration (Phase 4.1 / 4.2).

Unknown research versions are ``None`` — never fabricated placeholders such as
``\"v1\"``. Registry schema_version identifies the *manifest contract*, not a
research model version.

Authority split
---------------
* **Domain research structures** (factor metrics, model evaluations, prediction
  tables, validation reports, reproducibility evidence, …) belong to the Quant
  Research Engine / Evidence Layer. This package treats their serialized bytes
  as opaque content and does not redesign their business fields.
* **Publishing / registry structures** in this module
  (``ResearchRunMetadata``, ``ResearchRunManifest``,
  ``ResearchArtifactReference``, ``ArtifactVerificationResult``) carry only
  registry, storage, versioning, provenance, and integrity metadata.

Artifact relationship::

    Domain Research Object
      → serialized artifact file
      → ResearchArtifactReference
      → ResearchRunManifest.artifacts

Snapshot relationship::

    Registered Research Artifacts
      → Snapshot Builder
      → serialized snapshot file
      → ResearchSnapshotReference
      → ResearchRunManifest.snapshots

``ResearchRunManifest`` is the aggregate root. ``ResearchArtifactReference`` and
``ResearchSnapshotReference`` are child records. Consumer snapshot *content*
(``ResearchSummarySnapshot``, ``SignalSnapshot``) is serialized separately under
``snapshots/`` and pointed to by ``ResearchSnapshotReference``.
"""

from __future__ import annotations

import re
import secrets
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

MANIFEST_SCHEMA_VERSION = "research-run-manifest/v1"
LATEST_POINTER_SCHEMA_VERSION = "research-run-latest/v1"
ARTIFACT_SCHEMA_VERSION = "research-artifact/v1"
SNAPSHOT_REF_SCHEMA_VERSION = "research-snapshot-ref/v1"
CHECKSUM_ALGORITHM_SHA256 = "sha256"

RUN_ID_PATTERN = re.compile(r"^run_\d{8}T\d{6}Z_[0-9a-f]{8}$")
ARTIFACT_ID_PATTERN = re.compile(r"^artifact_[0-9a-f]{8}$")
SNAPSHOT_ID_PATTERN = re.compile(r"^snapshot_[0-9a-f]{8}$")
SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ResearchRunStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    VALIDATED = "VALIDATED"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


class ResearchRunType(str, Enum):
    TREND = "TREND"
    FACTOR = "FACTOR"
    MODEL = "MODEL"
    GENERAL = "GENERAL"


class ResearchArtifactType(str, Enum):
    """Bounded artifact taxonomy for Phase 4.2."""

    REPRODUCIBILITY_MANIFEST = "reproducibility_manifest"
    DATA_VALIDATION_REPORT = "data_validation_report"
    FACTOR_METRICS = "factor_metrics"
    FACTOR_REPORT = "factor_report"
    MODEL_EVALUATION = "model_evaluation"
    PREDICTION_TABLE = "prediction_table"
    FEATURE_IMPORTANCE = "feature_importance"
    VALIDATION_REPORT = "validation_report"
    GENERIC_JSON = "generic_json"
    GENERIC_PARQUET = "generic_parquet"


class ResearchSnapshotType(str, Enum):
    """Bounded consumer snapshot taxonomy for Phase 4.3."""

    RESEARCH_SUMMARY = "research_summary"
    SIGNAL = "signal"


def require_aware_utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        raise ValueError("datetime must be timezone-aware UTC")
    return value.astimezone(timezone.utc)


def utc_now() -> datetime:
    """Timezone-aware UTC timestamp (microseconds stripped for stable JSON)."""
    return datetime.now(timezone.utc).replace(microsecond=0)


def generate_run_id(*, when: Optional[datetime] = None) -> str:
    """Create a sortable, directory-safe run id with no user-controlled text.

    Format: ``run_<UTC timestamp>_<8-hex suffix>``
    Example: ``run_20260728T041530Z_a1b2c3d4``
    """
    stamp = when or utc_now()
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    else:
        stamp = stamp.astimezone(timezone.utc)
    stamp = stamp.replace(microsecond=0)
    timestamp = stamp.strftime("%Y%m%dT%H%M%SZ")
    suffix = secrets.token_hex(4)
    return f"run_{timestamp}_{suffix}"


def generate_artifact_id() -> str:
    """Create a collision-resistant artifact id independent of names / run ids."""
    return f"artifact_{secrets.token_hex(4)}"


def generate_snapshot_id() -> str:
    """Create a collision-resistant snapshot id independent of names / run ids."""
    return f"snapshot_{secrets.token_hex(4)}"


def is_valid_run_id(run_id: str) -> bool:
    return bool(RUN_ID_PATTERN.fullmatch(run_id))


def is_valid_artifact_id(artifact_id: str) -> bool:
    return bool(ARTIFACT_ID_PATTERN.fullmatch(artifact_id))


def is_valid_snapshot_id(snapshot_id: str) -> bool:
    return bool(SNAPSHOT_ID_PATTERN.fullmatch(snapshot_id))


class ResearchArtifactReference(BaseModel):
    """Publishing-layer pointer to an opaque research artifact file.

    This is a **child record** of ``ResearchRunManifest`` — not a domain research
    object and not a second independent artifact manifest.

    Allowed concerns: identity, type taxonomy, storage path, media type,
    integrity (checksum/size), optional structural ``row_count``, and small
    publishing provenance in ``metadata``.

    Forbidden concerns: IC, Sharpe, predictions, feature values, factor values,
    model metrics, or any duplication of Quant Research Engine business fields.
    Domain content lives only in the serialized artifact file referenced by
    ``relative_path``. Run ownership comes from the parent manifest / run dir —
    do not embed ``run_id`` or other run metadata here.
    """

    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    name: str
    artifact_type: ResearchArtifactType
    schema_version: str = ARTIFACT_SCHEMA_VERSION
    relative_path: str
    media_type: Optional[str] = None
    checksum_algorithm: str = CHECKSUM_ALGORITHM_SHA256
    checksum: str
    size_bytes: int = Field(ge=0)
    row_count: Optional[int] = Field(default=None, ge=0)
    created_at: datetime
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Small JSON-compatible publishing provenance only "
            "(e.g. producer module). Never store research metrics here."
        ),
    )

    @field_validator("artifact_id")
    @classmethod
    def _validate_artifact_id(cls, value: str) -> str:
        if not is_valid_artifact_id(value):
            raise ValueError(f"invalid artifact_id format: {value!r}")
        return value

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned or cleaned != value:
            raise ValueError("artifact name must be non-empty and unpadded")
        if "/" in cleaned or "\\" in cleaned or ".." in cleaned:
            raise ValueError("artifact name must not contain path separators")
        return cleaned

    @field_validator("checksum_algorithm")
    @classmethod
    def _validate_algorithm(cls, value: str) -> str:
        if value != CHECKSUM_ALGORITHM_SHA256:
            raise ValueError("only sha256 checksums are supported")
        return value

    @field_validator("checksum")
    @classmethod
    def _validate_checksum(cls, value: str) -> str:
        lowered = value.lower()
        if not SHA256_HEX_PATTERN.fullmatch(lowered):
            raise ValueError("checksum must be a 64-character lowercase sha256 hex digest")
        return lowered

    @field_validator("created_at")
    @classmethod
    def _require_aware_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("datetime must be timezone-aware UTC")
        return value.astimezone(timezone.utc)

    @field_validator("metadata")
    @classmethod
    def _validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("metadata must be a mapping")
        forbidden = {
            "ic",
            "rank_ic",
            "sharpe",
            "predictions",
            "feature_values",
            "factor_values",
            "model_metrics",
            "returns",
            "weights",
            "run_id",
            "git_commit",
            "dataset_version",
            "feature_version",
            "model_version",
        }
        overlap = forbidden.intersection(str(key).lower() for key in value)
        if overlap:
            raise ValueError(
                "metadata must not embed domain research fields or run metadata: "
                + ", ".join(sorted(overlap))
            )
        return value


# Backward-compatible alias — prefer ResearchArtifactReference.
ArtifactReference = ResearchArtifactReference


class ResearchSnapshotReference(BaseModel):
    """Publishing-layer pointer to a consumer snapshot file.

    Child of ``ResearchRunManifest``. Describes the snapshot file without
    embedding the full consumer snapshot payload. ``source_artifact_ids`` must
    reference artifacts registered on the same run.
    """

    model_config = ConfigDict(extra="forbid")

    snapshot_id: str
    name: str
    snapshot_type: ResearchSnapshotType
    schema_version: str = SNAPSHOT_REF_SCHEMA_VERSION
    relative_path: str
    media_type: Optional[str] = "application/json"
    checksum_algorithm: str = CHECKSUM_ALGORITHM_SHA256
    checksum: str
    size_bytes: int = Field(ge=0)
    created_at: datetime
    as_of: Optional[datetime] = None
    source_artifact_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Publishing context for the snapshot file — not full content.",
    )

    @field_validator("snapshot_id")
    @classmethod
    def _validate_snapshot_id(cls, value: str) -> str:
        if not is_valid_snapshot_id(value):
            raise ValueError(f"invalid snapshot_id format: {value!r}")
        return value

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned or cleaned != value:
            raise ValueError("snapshot name must be non-empty and unpadded")
        if "/" in cleaned or "\\" in cleaned or ".." in cleaned:
            raise ValueError("snapshot name must not contain path separators")
        return cleaned

    @field_validator("checksum_algorithm")
    @classmethod
    def _validate_algorithm(cls, value: str) -> str:
        if value != CHECKSUM_ALGORITHM_SHA256:
            raise ValueError("only sha256 checksums are supported")
        return value

    @field_validator("checksum")
    @classmethod
    def _validate_checksum(cls, value: str) -> str:
        lowered = value.lower()
        if not SHA256_HEX_PATTERN.fullmatch(lowered):
            raise ValueError("checksum must be a 64-character lowercase sha256 hex digest")
        return lowered

    @field_validator("created_at", "as_of")
    @classmethod
    def _aware(cls, value: Optional[datetime]) -> Optional[datetime]:
        return require_aware_utc(value)

    @field_validator("source_artifact_ids")
    @classmethod
    def _validate_sources(cls, value: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for item in value:
            if not is_valid_artifact_id(item):
                raise ValueError(f"invalid source artifact_id: {item!r}")
            if item not in seen:
                seen.add(item)
                ordered.append(item)
        return ordered


class SnapshotVerificationResult(BaseModel):
    """Read-only integrity check against a registered snapshot."""

    model_config = ConfigDict(extra="forbid")

    snapshot_id: str
    exists: bool
    checksum_matches: bool
    size_matches: bool
    valid: bool
    expected_checksum: str
    actual_checksum: Optional[str] = None
    verified_at: datetime
    errors: list[str] = Field(default_factory=list)


class ArtifactVerificationResult(BaseModel):
    """Read-only integrity check against a registered artifact."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    exists: bool
    checksum_matches: bool
    size_matches: bool
    valid: bool
    expected_checksum: str
    actual_checksum: Optional[str] = None
    verified_at: datetime
    errors: list[str] = Field(default_factory=list)


class ValidationRecord(BaseModel):
    """Registry-level validation notes for a research run."""

    model_config = ConfigDict(extra="forbid")

    ok: bool = True
    checks: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class ResearchRunMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = MANIFEST_SCHEMA_VERSION
    run_id: str
    run_type: ResearchRunType
    status: ResearchRunStatus
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    dataset_version: Optional[str] = None
    feature_version: Optional[str] = None
    model_version: Optional[str] = None
    git_commit: Optional[str] = None
    generator: Optional[str] = None
    environment: Optional[str] = None
    random_seed: Optional[int] = None
    training_window: Optional[str] = None
    prediction_window: Optional[str] = None
    universe: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("run_id")
    @classmethod
    def _validate_run_id(cls, value: str) -> str:
        if not is_valid_run_id(value):
            raise ValueError(f"invalid run_id format: {value!r}")
        return value

    @field_validator("created_at", "updated_at", "published_at")
    @classmethod
    def _require_aware_utc(cls, value: Optional[datetime]) -> Optional[datetime]:
        return require_aware_utc(value)


class ResearchRunManifest(BaseModel):
    """Aggregate root for one research run's publishing record.

    Domain research objects are **not** embedded here. They are serialized to
    artifact files and referenced by ``artifacts`` (``ResearchArtifactReference``
    children). Consumer snapshot payloads live under ``snapshots/`` and are
    referenced by ``snapshots`` (``ResearchSnapshotReference`` children).
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: str = MANIFEST_SCHEMA_VERSION
    run: ResearchRunMetadata
    artifacts: list[ResearchArtifactReference] = Field(default_factory=list)
    snapshots: list[ResearchSnapshotReference] = Field(default_factory=list)
    # Keys are artifact_id → sha256 digest; kept in sync with ResearchArtifactReference.checksum.
    checksums: dict[str, str] = Field(default_factory=dict)
    validation: ValidationRecord = Field(default_factory=ValidationRecord)
    errors: list[str] = Field(default_factory=list)


class LatestRunPointer(BaseModel):
    """Lightweight pointer written to ``outputs/latest.json`` after publish."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = LATEST_POINTER_SCHEMA_VERSION
    run_id: str
    manifest_path: str
    published_at: datetime

    @field_validator("run_id")
    @classmethod
    def _validate_run_id(cls, value: str) -> str:
        if not is_valid_run_id(value):
            raise ValueError(f"invalid run_id format: {value!r}")
        return value

    @field_validator("published_at")
    @classmethod
    def _require_aware_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("datetime must be timezone-aware UTC")
        return value.astimezone(timezone.utc)
