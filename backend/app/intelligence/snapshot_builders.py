"""Deterministic artifact-to-snapshot builders (Phase 4.4).

Architecture::

    Registered Artifacts
      → Artifact Registry read / optional verification
      → Deterministic Snapshot Builder
      → Typed in-memory Snapshot
      → Snapshot Registry.register_snapshot
      → snapshots/*.json + ResearchSnapshotReference

Supported input contracts
-------------------------
Domain research payloads (factor metrics, modeling responses, prediction
tables) do **not** carry ``SignalDirection`` or typed summary findings.
Builders therefore accept only **explicit publishing evidence contracts**
embedded as JSON artifact payloads with a top-level ``schema_version``:

* ``research-summary-evidence/v1``
* ``signal-evidence/v1``

Support is determined solely by that ``schema_version`` field (fail-closed).
No recursive field guessing. No score→direction inference. No LLM prose.
Duplicate ``source_artifact_ids`` are normalized (first-seen order preserved
for reading; provenance IDs are sorted for stable content).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Optional, Sequence

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.intelligence.artifact_registry import ResearchArtifactRegistry
from app.intelligence.errors import (
    ArtifactIntegrityError,
    ArtifactNotFoundError,
    InvalidArtifactError,
    SnapshotArtifactPayloadError,
    SnapshotEvidenceError,
    SnapshotSourceError,
    UnsupportedArtifactContractError,
)
from app.intelligence.schemas import (
    ResearchArtifactReference,
    ResearchSnapshotReference,
    ResearchSnapshotType,
    require_aware_utc,
    utc_now,
)
from app.intelligence.snapshot_contracts import (
    ArtifactSummaryItem,
    ResearchSummarySnapshot,
    SignalRecord,
    SignalSnapshot,
    SnapshotContentProvenance,
    SnapshotFinding,
    SnapshotLimitation,
    ValidationStatus,
)
from app.intelligence.snapshot_registry import ResearchSnapshotRegistry

RESEARCH_SUMMARY_EVIDENCE_VERSION = "research-summary-evidence/v1"
SIGNAL_EVIDENCE_VERSION = "signal-evidence/v1"


class ResearchSummaryEvidence(BaseModel):
    """Publishing-layer evidence payload for ResearchSummarySnapshotBuilder."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str
    research_title: Optional[str] = None
    research_objective: Optional[str] = None
    analysis_window: Optional[str] = None
    validation_status: ValidationStatus = ValidationStatus.UNKNOWN
    key_findings: list[SnapshotFinding] = Field(default_factory=list)
    limitations: list[SnapshotLimitation] = Field(default_factory=list)
    as_of: Optional[datetime] = None

    @field_validator("schema_version")
    @classmethod
    def _version(cls, value: str) -> str:
        if value != RESEARCH_SUMMARY_EVIDENCE_VERSION:
            raise ValueError(f"unsupported schema_version: {value!r}")
        return value

    @field_validator("as_of")
    @classmethod
    def _aware(cls, value: Optional[datetime]) -> Optional[datetime]:
        return require_aware_utc(value)


class SignalEvidence(BaseModel):
    """Publishing-layer evidence payload for SignalSnapshotBuilder."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str
    universe: Optional[str] = None
    as_of: Optional[datetime] = None
    signals: list[SignalRecord] = Field(default_factory=list)

    @field_validator("schema_version")
    @classmethod
    def _version(cls, value: str) -> str:
        if value != SIGNAL_EVIDENCE_VERSION:
            raise ValueError(f"unsupported schema_version: {value!r}")
        return value

    @field_validator("as_of")
    @classmethod
    def _aware(cls, value: Optional[datetime]) -> Optional[datetime]:
        return require_aware_utc(value)


def _normalize_source_ids(source_artifact_ids: Sequence[str]) -> list[str]:
    if not source_artifact_ids:
        raise SnapshotEvidenceError("at least one source_artifact_id is required")
    ordered: list[str] = []
    seen: set[str] = set()
    for item in source_artifact_ids:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _stable_content_dict(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Drop identity/time fields for deterministic comparisons."""
    return {
        key: value
        for key, value in payload.items()
        if key not in {"generated_at"}
    }


class ResearchSummarySnapshotBuilder:
    """Map ``research-summary-evidence/v1`` artifacts into ResearchSummarySnapshot."""

    BUILDER_ID = "research-summary-builder/v1"
    SUPPORTED_CONTRACTS = frozenset({RESEARCH_SUMMARY_EVIDENCE_VERSION})

    def __init__(
        self,
        artifact_registry: ResearchArtifactRegistry,
        snapshot_registry: ResearchSnapshotRegistry,
        *,
        require_artifact_verification: bool = False,
    ) -> None:
        self._artifacts = artifact_registry
        self._snapshots = snapshot_registry
        self._require_verify = require_artifact_verification

    def build(
        self,
        run_id: str,
        *,
        source_artifact_ids: Sequence[str],
        now: Optional[datetime] = None,
        require_artifact_verification: Optional[bool] = None,
    ) -> ResearchSummarySnapshot:
        verify = (
            self._require_verify
            if require_artifact_verification is None
            else require_artifact_verification
        )
        source_ids = _normalize_source_ids(source_artifact_ids)
        manifest = self._snapshots._runs.get_run(run_id)
        references = self._resolve_and_read(
            run_id,
            source_ids,
            verify=verify,
        )
        evidence_rows: list[ResearchSummaryEvidence] = []
        for ref, payload in references:
            evidence_rows.append(self._parse_evidence(ref, payload))

        findings: list[SnapshotFinding] = []
        limitations: list[SnapshotLimitation] = []
        title: Optional[str] = None
        objective: Optional[str] = None
        window: Optional[str] = None
        validation = ValidationStatus.UNKNOWN
        as_of: Optional[datetime] = None
        for row in evidence_rows:
            if title is None and row.research_title is not None:
                title = row.research_title
            if objective is None and row.research_objective is not None:
                objective = row.research_objective
            if window is None and row.analysis_window is not None:
                window = row.analysis_window
            if validation == ValidationStatus.UNKNOWN and row.validation_status != ValidationStatus.UNKNOWN:
                validation = row.validation_status
            if as_of is None and row.as_of is not None:
                as_of = row.as_of
            findings.extend(row.key_findings)
            limitations.extend(row.limitations)

        provenance_ids = sorted(source_ids)
        artifact_summary = sorted(
            [
                ArtifactSummaryItem(
                    artifact_id=ref.artifact_id,
                    name=ref.name,
                    artifact_type=ref.artifact_type.value,
                )
                for ref, _ in references
            ],
            key=lambda item: item.artifact_id,
        )
        stamp = now or utc_now()
        return ResearchSummarySnapshot(
            generated_at=stamp,
            as_of=as_of,
            research_title=title,
            research_objective=objective,
            run_type=manifest.run.run_type,
            universe=manifest.run.universe,
            analysis_window=window,
            validation_status=validation,
            key_findings=findings,
            limitations=limitations,
            artifact_summary=artifact_summary,
            provenance=SnapshotContentProvenance(
                source_artifact_ids=provenance_ids,
                builder=self.BUILDER_ID,
            ),
        )

    def build_and_register(
        self,
        run_id: str,
        *,
        name: str,
        source_artifact_ids: Sequence[str],
        metadata: Optional[Mapping[str, Any]] = None,
        now: Optional[datetime] = None,
        require_artifact_verification: Optional[bool] = None,
    ) -> ResearchSnapshotReference:
        content = self.build(
            run_id,
            source_artifact_ids=source_artifact_ids,
            now=now,
            require_artifact_verification=require_artifact_verification,
        )
        return self._snapshots.register_snapshot(
            run_id,
            name=name,
            snapshot_type=ResearchSnapshotType.RESEARCH_SUMMARY,
            content=content,
            source_artifact_ids=list(content.provenance.source_artifact_ids),
            as_of=content.as_of,
            metadata=metadata,
            require_artifact_verification=(
                self._require_verify
                if require_artifact_verification is None
                else require_artifact_verification
            ),
            now=content.generated_at,
        )

    def _resolve_and_read(
        self,
        run_id: str,
        source_ids: Sequence[str],
        *,
        verify: bool,
    ) -> list[tuple[ResearchArtifactReference, Any]]:
        rows: list[tuple[ResearchArtifactReference, Any]] = []
        for artifact_id in source_ids:
            try:
                ref = self._artifacts.get_artifact(run_id, artifact_id)
            except ArtifactNotFoundError as exc:
                raise SnapshotSourceError(
                    f"source artifact {artifact_id!r} is not registered on run {run_id}"
                ) from exc
            try:
                payload = self._artifacts.read_json_artifact(
                    run_id,
                    ref.artifact_id,
                    verify=verify,
                )
            except ArtifactIntegrityError as exc:
                raise SnapshotSourceError(str(exc)) from exc
            except InvalidArtifactError as exc:
                raise SnapshotArtifactPayloadError(str(exc)) from exc
            rows.append((ref, payload))
        return rows

    def _parse_evidence(
        self,
        ref: ResearchArtifactReference,
        payload: Any,
    ) -> ResearchSummaryEvidence:
        if not isinstance(payload, dict):
            raise UnsupportedArtifactContractError(
                f"artifact {ref.artifact_id!r} payload is not a supported "
                f"research-summary evidence object"
            )
        version = payload.get("schema_version")
        if version not in self.SUPPORTED_CONTRACTS:
            raise UnsupportedArtifactContractError(
                f"artifact {ref.artifact_id!r} schema_version={version!r} is not "
                f"supported by {self.BUILDER_ID}; supported={sorted(self.SUPPORTED_CONTRACTS)}"
            )
        try:
            return ResearchSummaryEvidence.model_validate(payload)
        except ValidationError as exc:
            raise SnapshotArtifactPayloadError(
                f"artifact {ref.artifact_id!r} failed research-summary evidence validation"
            ) from exc


class SignalSnapshotBuilder:
    """Map ``signal-evidence/v1`` artifacts into SignalSnapshot."""

    BUILDER_ID = "signal-builder/v1"
    SUPPORTED_CONTRACTS = frozenset({SIGNAL_EVIDENCE_VERSION})

    def __init__(
        self,
        artifact_registry: ResearchArtifactRegistry,
        snapshot_registry: ResearchSnapshotRegistry,
        *,
        require_artifact_verification: bool = False,
    ) -> None:
        self._artifacts = artifact_registry
        self._snapshots = snapshot_registry
        self._require_verify = require_artifact_verification

    def build(
        self,
        run_id: str,
        *,
        source_artifact_ids: Sequence[str],
        now: Optional[datetime] = None,
        require_artifact_verification: Optional[bool] = None,
    ) -> SignalSnapshot:
        verify = (
            self._require_verify
            if require_artifact_verification is None
            else require_artifact_verification
        )
        source_ids = _normalize_source_ids(source_artifact_ids)
        manifest = self._snapshots._runs.get_run(run_id)
        references = self._resolve_and_read(run_id, source_ids, verify=verify)
        evidence_rows: list[SignalEvidence] = []
        for ref, payload in references:
            evidence_rows.append(self._parse_evidence(ref, payload))

        signals: list[SignalRecord] = []
        universe: Optional[str] = None
        as_of: Optional[datetime] = None
        for row in evidence_rows:
            if universe is None and row.universe is not None:
                universe = row.universe
            if as_of is None and row.as_of is not None:
                as_of = row.as_of
            signals.extend(row.signals)

        ordered_signals = sorted(signals, key=lambda row: (row.symbol, row.signal_name))
        provenance_ids = sorted(source_ids)
        stamp = now or utc_now()
        return SignalSnapshot(
            generated_at=stamp,
            as_of=as_of,
            universe=universe if universe is not None else manifest.run.universe,
            signals=ordered_signals,
            provenance=SnapshotContentProvenance(
                source_artifact_ids=provenance_ids,
                builder=self.BUILDER_ID,
            ),
        )

    def build_and_register(
        self,
        run_id: str,
        *,
        name: str,
        source_artifact_ids: Sequence[str],
        metadata: Optional[Mapping[str, Any]] = None,
        now: Optional[datetime] = None,
        require_artifact_verification: Optional[bool] = None,
    ) -> ResearchSnapshotReference:
        content = self.build(
            run_id,
            source_artifact_ids=source_artifact_ids,
            now=now,
            require_artifact_verification=require_artifact_verification,
        )
        return self._snapshots.register_snapshot(
            run_id,
            name=name,
            snapshot_type=ResearchSnapshotType.SIGNAL,
            content=content,
            source_artifact_ids=list(content.provenance.source_artifact_ids),
            as_of=content.as_of,
            metadata=metadata,
            require_artifact_verification=(
                self._require_verify
                if require_artifact_verification is None
                else require_artifact_verification
            ),
            now=content.generated_at,
        )

    def _resolve_and_read(
        self,
        run_id: str,
        source_ids: Sequence[str],
        *,
        verify: bool,
    ) -> list[tuple[ResearchArtifactReference, Any]]:
        rows: list[tuple[ResearchArtifactReference, Any]] = []
        for artifact_id in source_ids:
            try:
                ref = self._artifacts.get_artifact(run_id, artifact_id)
            except ArtifactNotFoundError as exc:
                raise SnapshotSourceError(
                    f"source artifact {artifact_id!r} is not registered on run {run_id}"
                ) from exc
            try:
                payload = self._artifacts.read_json_artifact(
                    run_id,
                    ref.artifact_id,
                    verify=verify,
                )
            except ArtifactIntegrityError as exc:
                raise SnapshotSourceError(str(exc)) from exc
            except InvalidArtifactError as exc:
                raise SnapshotArtifactPayloadError(str(exc)) from exc
            rows.append((ref, payload))
        return rows

    def _parse_evidence(
        self,
        ref: ResearchArtifactReference,
        payload: Any,
    ) -> SignalEvidence:
        if not isinstance(payload, dict):
            raise UnsupportedArtifactContractError(
                f"artifact {ref.artifact_id!r} payload is not a supported "
                f"signal evidence object"
            )
        version = payload.get("schema_version")
        if version not in self.SUPPORTED_CONTRACTS:
            raise UnsupportedArtifactContractError(
                f"artifact {ref.artifact_id!r} schema_version={version!r} is not "
                f"supported by {self.BUILDER_ID}; supported={sorted(self.SUPPORTED_CONTRACTS)}"
            )
        try:
            return SignalEvidence.model_validate(payload)
        except ValidationError as exc:
            raise SnapshotArtifactPayloadError(
                f"artifact {ref.artifact_id!r} failed signal evidence validation"
            ) from exc


# Re-export helper for tests comparing stable content.
stable_snapshot_content = _stable_content_dict

__all__ = [
    "RESEARCH_SUMMARY_EVIDENCE_VERSION",
    "SIGNAL_EVIDENCE_VERSION",
    "ResearchSummaryEvidence",
    "ResearchSummarySnapshotBuilder",
    "SignalEvidence",
    "SignalSnapshotBuilder",
    "stable_snapshot_content",
]
