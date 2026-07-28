"""Build and register consumer intelligence snapshots (Phase 4.3 / 4.4).

Registered Research Artifacts
  → Snapshot Builder (Phase 4.4) or explicit convenience builders (Phase 4.3)
  → typed in-memory snapshot
  → register_snapshot
  → serialized snapshot file
  → ResearchSnapshotReference
  → ResearchRunManifest.snapshots
"""

from __future__ import annotations

import hashlib
import hmac
import re
from datetime import datetime
from typing import Any, Mapping, Optional, Sequence, Union

from app.intelligence.artifact_registry import (
    ResearchArtifactRegistry,
    serialize_artifact_json,
)
from app.intelligence.errors import (
    IntelligenceStorageError,
    InvalidRunTransitionError,
    InvalidSnapshotError,
    SnapshotAlreadyExistsError,
    SnapshotIntegrityError,
    SnapshotNotFoundError,
    SnapshotSourceError,
)
from app.intelligence.manifest import validate_manifest
from app.intelligence.run_registry import ResearchRunRegistry
from app.intelligence.schemas import (
    CHECKSUM_ALGORITHM_SHA256,
    SNAPSHOT_REF_SCHEMA_VERSION,
    ResearchRunStatus,
    ResearchSnapshotReference,
    ResearchSnapshotType,
    SnapshotVerificationResult,
    generate_snapshot_id,
    is_valid_snapshot_id,
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
from app.intelligence.storage import SNAPSHOTS_DIRNAME, calculate_sha256

SNAPSHOT_WRITABLE_STATUSES = frozenset(
    {
        ResearchRunStatus.CREATED,
        ResearchRunStatus.RUNNING,
        ResearchRunStatus.VALIDATED,
    }
)

BUILDER_ID = "intelligence-snapshot-registry/phase-4.3"
_SAFE_NAME_RE = re.compile(r"[^a-z0-9_-]+")

SupportedSnapshotContent = Union[ResearchSummarySnapshot, SignalSnapshot]


def _assert_writable(status: ResearchRunStatus) -> None:
    if status not in SNAPSHOT_WRITABLE_STATUSES:
        raise InvalidRunTransitionError(
            f"snapshot creation forbidden for status {status.value}"
        )


def _safe_stem(name: str) -> str:
    stem = _SAFE_NAME_RE.sub("-", name.strip().lower()).strip("-_")
    return (stem or "snapshot")[:48]


def _snapshot_filename(name: str, snapshot_id: str) -> str:
    short = snapshot_id[len("snapshot_") :] if snapshot_id.startswith("snapshot_") else snapshot_id
    return f"{_safe_stem(name)}__{short}.json"


def _expected_type_for_content(content: SupportedSnapshotContent) -> ResearchSnapshotType:
    if isinstance(content, ResearchSummarySnapshot):
        return ResearchSnapshotType.RESEARCH_SUMMARY
    if isinstance(content, SignalSnapshot):
        return ResearchSnapshotType.SIGNAL
    raise InvalidSnapshotError(
        f"unsupported snapshot content type: {type(content).__name__}"
    )


class ResearchSnapshotRegistry:
    """Append-only consumer snapshot registration under a research run."""

    def __init__(
        self,
        run_registry: ResearchRunRegistry,
        *,
        artifact_registry: Optional[ResearchArtifactRegistry] = None,
    ) -> None:
        self._runs = run_registry
        self._storage = run_registry.storage
        self._artifacts = artifact_registry or ResearchArtifactRegistry(run_registry)

    def register_snapshot(
        self,
        run_id: str,
        *,
        name: str,
        snapshot_type: ResearchSnapshotType,
        content: SupportedSnapshotContent,
        source_artifact_ids: Sequence[str],
        as_of: Optional[datetime] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        require_artifact_verification: bool = False,
        now: Optional[datetime] = None,
    ) -> ResearchSnapshotReference:
        """Persist an already-constructed typed snapshot under the run."""
        expected = _expected_type_for_content(content)
        if snapshot_type != expected:
            raise InvalidSnapshotError(
                f"snapshot_type {snapshot_type.value!r} does not match content "
                f"contract for {type(content).__name__}"
            )
        stamp = now or utc_now()
        with self._storage.acquire_run_write_lock(run_id):
            manifest = self._runs.get_run(run_id)
            _assert_writable(manifest.run.status)
            sources = self._resolve_sources(
                run_id,
                manifest,
                source_artifact_ids,
                require_artifact_verification=require_artifact_verification,
            )
            ordered_source_ids = sorted({item.artifact_id for item in sources})
            content_ids = list(getattr(content.provenance, "source_artifact_ids", []) or [])
            if sorted(set(content_ids)) != ordered_source_ids:
                raise InvalidSnapshotError(
                    "snapshot content provenance.source_artifact_ids must match "
                    "register_snapshot source_artifact_ids"
                )
            return self._persist_snapshot_locked(
                run_id,
                manifest=manifest,
                name=name,
                snapshot_type=snapshot_type,
                content=content,
                source_artifact_ids=ordered_source_ids,
                as_of=as_of,
                metadata=dict(metadata or {}),
                now=stamp,
            )

    def build_research_summary_snapshot(
        self,
        run_id: str,
        *,
        name: str,
        source_artifact_ids: Sequence[str],
        research_title: Optional[str] = None,
        research_objective: Optional[str] = None,
        analysis_window: Optional[str] = None,
        validation_status: ValidationStatus = ValidationStatus.UNKNOWN,
        key_findings: Optional[Sequence[SnapshotFinding]] = None,
        limitations: Optional[Sequence[SnapshotLimitation]] = None,
        as_of: Optional[datetime] = None,
        provenance_notes: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        require_artifact_verification: bool = False,
        now: Optional[datetime] = None,
    ) -> ResearchSnapshotReference:
        """Build and register a ResearchSummarySnapshot from explicit inputs."""
        stamp = now or utc_now()
        with self._storage.acquire_run_write_lock(run_id):
            manifest = self._runs.get_run(run_id)
            _assert_writable(manifest.run.status)
            sources = self._resolve_sources(
                run_id,
                manifest,
                source_artifact_ids,
                require_artifact_verification=require_artifact_verification,
            )
            artifact_summary = [
                ArtifactSummaryItem(
                    artifact_id=item.artifact_id,
                    name=item.name,
                    artifact_type=item.artifact_type.value,
                )
                for item in sources
            ]
            # Stable order by artifact_id for deterministic content (excluding identity time).
            artifact_summary = sorted(artifact_summary, key=lambda row: row.artifact_id)
            ordered_source_ids = [item.artifact_id for item in artifact_summary]

            content = ResearchSummarySnapshot(
                generated_at=stamp,
                as_of=as_of,
                research_title=research_title,
                research_objective=research_objective,
                run_type=manifest.run.run_type,
                universe=manifest.run.universe,
                analysis_window=analysis_window,
                validation_status=validation_status,
                key_findings=list(key_findings or []),
                limitations=list(limitations or []),
                artifact_summary=artifact_summary,
                provenance=SnapshotContentProvenance(
                    source_artifact_ids=ordered_source_ids,
                    builder=BUILDER_ID,
                    notes=provenance_notes,
                ),
            )
            return self._persist_snapshot_locked(
                run_id,
                manifest=manifest,
                name=name,
                snapshot_type=ResearchSnapshotType.RESEARCH_SUMMARY,
                content=content,
                source_artifact_ids=ordered_source_ids,
                as_of=as_of,
                metadata=dict(metadata or {}),
                now=stamp,
            )

    def build_signal_snapshot(
        self,
        run_id: str,
        *,
        name: str,
        source_artifact_ids: Sequence[str],
        signals: Sequence[SignalRecord],
        universe: Optional[str] = None,
        as_of: Optional[datetime] = None,
        provenance_notes: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        require_artifact_verification: bool = False,
        now: Optional[datetime] = None,
    ) -> ResearchSnapshotReference:
        """Build and register a SignalSnapshot from explicit normalized signals."""
        stamp = now or utc_now()
        with self._storage.acquire_run_write_lock(run_id):
            manifest = self._runs.get_run(run_id)
            _assert_writable(manifest.run.status)
            sources = self._resolve_sources(
                run_id,
                manifest,
                source_artifact_ids,
                require_artifact_verification=require_artifact_verification,
            )
            ordered_source_ids = sorted({item.artifact_id for item in sources})
            # Stable signal ordering by symbol then signal_name (no semantic ranking).
            ordered_signals = sorted(
                list(signals),
                key=lambda row: (row.symbol, row.signal_name),
            )
            content = SignalSnapshot(
                generated_at=stamp,
                as_of=as_of,
                universe=universe if universe is not None else manifest.run.universe,
                signals=ordered_signals,
                provenance=SnapshotContentProvenance(
                    source_artifact_ids=ordered_source_ids,
                    builder=BUILDER_ID,
                    notes=provenance_notes,
                ),
            )
            return self._persist_snapshot_locked(
                run_id,
                manifest=manifest,
                name=name,
                snapshot_type=ResearchSnapshotType.SIGNAL,
                content=content,
                source_artifact_ids=ordered_source_ids,
                as_of=as_of,
                metadata=dict(metadata or {}),
                now=stamp,
            )

    def get_snapshot(self, run_id: str, snapshot_name_or_id: str) -> ResearchSnapshotReference:
        for item in self._runs.get_run(run_id).snapshots:
            if item.name == snapshot_name_or_id or item.snapshot_id == snapshot_name_or_id:
                return item
        raise SnapshotNotFoundError(
            f"snapshot not found on run {run_id}: {snapshot_name_or_id!r}"
        )

    def list_snapshots(self, run_id: str) -> list[ResearchSnapshotReference]:
        return list(self._runs.get_run(run_id).snapshots)

    def verify_snapshot(
        self,
        run_id: str,
        snapshot_name_or_id: str,
        *,
        now: Optional[datetime] = None,
    ) -> SnapshotVerificationResult:
        snapshot = self.get_snapshot(run_id, snapshot_name_or_id)
        stamp = now or utc_now()
        errors: list[str] = []
        path = self._storage.resolve_run_relative_path(run_id, snapshot.relative_path)
        exists = path.is_file()
        actual_checksum: Optional[str] = None
        checksum_matches = False
        size_matches = False
        if not exists:
            errors.append("snapshot file is missing")
        else:
            actual_checksum = calculate_sha256(path)
            checksum_matches = hmac.compare_digest(actual_checksum, snapshot.checksum)
            if not checksum_matches:
                errors.append("checksum mismatch")
            actual_size = path.stat().st_size
            size_matches = actual_size == snapshot.size_bytes
            if not size_matches:
                errors.append(
                    f"size mismatch: expected {snapshot.size_bytes}, found {actual_size}"
                )
        valid = exists and checksum_matches and size_matches and not errors
        return SnapshotVerificationResult(
            snapshot_id=snapshot.snapshot_id,
            exists=exists,
            checksum_matches=checksum_matches,
            size_matches=size_matches,
            valid=valid,
            expected_checksum=snapshot.checksum,
            actual_checksum=actual_checksum,
            verified_at=stamp,
            errors=errors,
        )

    def read_snapshot_bytes(
        self,
        run_id: str,
        snapshot_name_or_id: str,
        *,
        verify: bool = False,
    ) -> bytes:
        """Read registered snapshot file bytes (no free-path reads)."""
        snapshot = self.get_snapshot(run_id, snapshot_name_or_id)
        if verify:
            result = self.verify_snapshot(run_id, snapshot.snapshot_id)
            if not result.valid:
                raise SnapshotIntegrityError(
                    f"snapshot {snapshot.snapshot_id!r} failed integrity verification: "
                    + "; ".join(result.errors)
                )
        path = self._storage.resolve_run_relative_path(run_id, snapshot.relative_path)
        if not path.is_file():
            raise SnapshotNotFoundError(
                f"snapshot file missing for {snapshot.snapshot_id!r} on run {run_id}"
            )
        try:
            return path.read_bytes()
        except OSError as exc:
            raise IntelligenceStorageError(
                f"unable to read snapshot bytes for {snapshot.snapshot_id!r}"
            ) from exc

    def read_snapshot(
        self,
        run_id: str,
        snapshot_name_or_id: str,
        *,
        verify: bool = False,
    ) -> SupportedSnapshotContent:
        """Read and validate a registered typed consumer snapshot."""
        import json

        from pydantic import ValidationError

        reference = self.get_snapshot(run_id, snapshot_name_or_id)
        raw = self.read_snapshot_bytes(run_id, reference.snapshot_id, verify=verify)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise InvalidSnapshotError(
                f"snapshot {reference.snapshot_id!r} is not valid UTF-8 JSON"
            ) from exc
        except json.JSONDecodeError as exc:
            raise InvalidSnapshotError(
                f"snapshot {reference.snapshot_id!r} contains invalid JSON"
            ) from exc

        try:
            if reference.snapshot_type == ResearchSnapshotType.RESEARCH_SUMMARY:
                return ResearchSummarySnapshot.model_validate(payload)
            if reference.snapshot_type == ResearchSnapshotType.SIGNAL:
                return SignalSnapshot.model_validate(payload)
        except ValidationError as exc:
            raise InvalidSnapshotError(
                f"snapshot {reference.snapshot_id!r} failed "
                f"{reference.snapshot_type.value} contract validation"
            ) from exc

        raise InvalidSnapshotError(
            f"unsupported snapshot_type for read: {reference.snapshot_type.value!r}"
        )

    def _resolve_sources(
        self,
        run_id: str,
        manifest: Any,
        source_artifact_ids: Sequence[str],
        *,
        require_artifact_verification: bool,
    ) -> list[Any]:
        if not source_artifact_ids:
            raise SnapshotSourceError("at least one source_artifact_id is required")
        by_id = {item.artifact_id: item for item in manifest.artifacts}
        resolved = []
        seen: set[str] = set()
        for artifact_id in source_artifact_ids:
            if artifact_id in seen:
                continue
            seen.add(artifact_id)
            artifact = by_id.get(artifact_id)
            if artifact is None:
                raise SnapshotSourceError(
                    f"source artifact {artifact_id!r} is not registered on run {run_id}"
                )
            if require_artifact_verification:
                result = self._artifacts.verify_artifact(run_id, artifact_id)
                if not result.valid:
                    raise SnapshotSourceError(
                        f"source artifact {artifact_id!r} failed integrity verification: "
                        + "; ".join(result.errors)
                    )
            resolved.append(artifact)
        return resolved

    def _persist_snapshot_locked(
        self,
        run_id: str,
        *,
        manifest: Any,
        name: str,
        snapshot_type: ResearchSnapshotType,
        content: SupportedSnapshotContent,
        source_artifact_ids: Sequence[str],
        as_of: Optional[datetime],
        metadata: dict[str, Any],
        now: datetime,
    ) -> ResearchSnapshotReference:
        """Persist snapshot file + manifest. Caller must hold the run write lock."""
        cleaned_name = name.strip()
        if not cleaned_name:
            raise InvalidSnapshotError("snapshot name is required")
        if any(item.name == cleaned_name for item in manifest.snapshots):
            raise SnapshotAlreadyExistsError(
                f"snapshot name already registered: {cleaned_name!r}"
            )

        snapshot_id = generate_snapshot_id()
        while any(item.snapshot_id == snapshot_id for item in manifest.snapshots):
            snapshot_id = generate_snapshot_id()
        if not is_valid_snapshot_id(snapshot_id):
            raise InvalidSnapshotError(f"invalid generated snapshot_id: {snapshot_id}")

        relative_path = f"{SNAPSHOTS_DIRNAME}/{_snapshot_filename(cleaned_name, snapshot_id)}"
        destination = self._storage.resolve_run_relative_path(run_id, relative_path)
        if destination.exists():
            raise SnapshotAlreadyExistsError(
                f"snapshot destination already exists: {relative_path}"
            )

        payload = serialize_artifact_json(content.model_dump(mode="json"))
        checksum = hashlib.sha256(payload).hexdigest()
        reference = ResearchSnapshotReference(
            snapshot_id=snapshot_id,
            name=cleaned_name,
            snapshot_type=snapshot_type,
            schema_version=SNAPSHOT_REF_SCHEMA_VERSION,
            relative_path=relative_path,
            media_type="application/json",
            checksum_algorithm=CHECKSUM_ALGORITHM_SHA256,
            checksum=checksum,
            size_bytes=len(payload),
            created_at=now,
            as_of=as_of,
            source_artifact_ids=list(source_artifact_ids),
            metadata=metadata,
        )
        prospective = manifest.model_copy(
            update={
                "snapshots": [*manifest.snapshots, reference],
                "run": manifest.run.model_copy(update={"updated_at": now}),
            }
        )
        validate_manifest(prospective, expected_run_id=run_id)

        self._storage.ensure_snapshots_dir(run_id)
        self._storage.write_bytes_atomic(destination, payload)
        on_disk = calculate_sha256(destination)
        if not hmac.compare_digest(on_disk, checksum):
            self._safe_unlink(destination)
            raise IntelligenceStorageError(
                f"on-disk checksum mismatch after snapshot write for {relative_path}"
            )

        try:
            self._runs._write_manifest(prospective)
        except Exception as exc:
            self._safe_unlink(destination)
            if isinstance(exc, IntelligenceStorageError):
                raise
            raise IntelligenceStorageError(
                f"manifest update failed after snapshot write for {run_id}; "
                "new snapshot file was rolled back"
            ) from exc
        return reference

    @staticmethod
    def _safe_unlink(path: Any) -> None:
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass


# Focused builder entry points (thin wrappers for clarity / docs).
def build_research_summary_snapshot(
    registry: ResearchSnapshotRegistry,
    run_id: str,
    **kwargs: Any,
) -> ResearchSnapshotReference:
    return registry.build_research_summary_snapshot(run_id, **kwargs)


def build_signal_snapshot(
    registry: ResearchSnapshotRegistry,
    run_id: str,
    **kwargs: Any,
) -> ResearchSnapshotReference:
    return registry.build_signal_snapshot(run_id, **kwargs)
