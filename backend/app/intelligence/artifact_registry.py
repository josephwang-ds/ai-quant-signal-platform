"""Register immutable, checksummed research artifacts on a research run.

Domain research objects remain opaque file content. This module only manages
publishing references under ``ResearchRunManifest`` (the aggregate root).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Mapping, Optional, Union

from app.intelligence.errors import (
    ArtifactAlreadyExistsError,
    ArtifactIntegrityError,
    ArtifactNotFoundError,
    IntelligenceStorageError,
    InvalidArtifactError,
    InvalidRunTransitionError,
)
from app.intelligence.manifest import (
    sync_artifact_checksums,
    validate_manifest,
)
from app.intelligence.run_registry import ResearchRunRegistry
from app.intelligence.schemas import (
    ARTIFACT_SCHEMA_VERSION,
    CHECKSUM_ALGORITHM_SHA256,
    ResearchArtifactReference,
    ArtifactVerificationResult,
    ResearchArtifactType,
    ResearchRunManifest,
    ResearchRunStatus,
    generate_artifact_id,
    is_valid_artifact_id,
    utc_now,
)
from app.intelligence.storage import ARTIFACTS_DIRNAME, calculate_sha256

ARTIFACT_WRITABLE_STATUSES = frozenset(
    {
        ResearchRunStatus.CREATED,
        ResearchRunStatus.RUNNING,
        ResearchRunStatus.VALIDATED,
    }
)

_SAFE_NAME_RE = re.compile(r"[^a-z0-9_-]+")
_MEDIA_BY_SUFFIX = {
    ".json": "application/json",
    ".parquet": "application/vnd.apache.parquet",
    ".csv": "text/csv",
    ".txt": "text/plain",
}


def serialize_artifact_json(payload: Any) -> bytes:
    """Deterministic UTF-8 JSON bytes (sorted keys, no NaN/Infinity)."""
    from datetime import timezone as _tz

    def _normalize(value: Any) -> Any:
        if value is None or isinstance(value, (str, int, bool)):
            return value
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                raise InvalidArtifactError("JSON artifacts cannot contain NaN or Infinity")
            return value
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%S")
            return (
                value.astimezone(_tz.utc)
                .replace(microsecond=0)
                .strftime("%Y-%m-%dT%H:%M:%SZ")
            )
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, Mapping):
            return {str(key): _normalize(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [_normalize(item) for item in value]
        raise InvalidArtifactError(
            f"unsupported JSON artifact value type: {type(value).__name__}"
        )

    normalized = _normalize(payload)
    try:
        text = json.dumps(
            normalized,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise InvalidArtifactError("payload is not JSON-serializable") from exc
    return (text + "\n").encode("utf-8")


def _safe_artifact_stem(name: str) -> str:
    stem = _SAFE_NAME_RE.sub("-", name.strip().lower()).strip("-_")
    if not stem:
        stem = "artifact"
    return stem[:48]


def _artifact_filename(name: str, artifact_id: str, extension: str) -> str:
    short_id = artifact_id[len("artifact_") :] if artifact_id.startswith("artifact_") else artifact_id
    ext = extension if extension.startswith(".") else f".{extension}"
    return f"{_safe_artifact_stem(name)}__{short_id}{ext}"


def _infer_media_type(path: Path, explicit: Optional[str]) -> Optional[str]:
    if explicit:
        return explicit
    return _MEDIA_BY_SUFFIX.get(path.suffix.lower())


def _assert_writable(status: ResearchRunStatus) -> None:
    if status not in ARTIFACT_WRITABLE_STATUSES:
        raise InvalidRunTransitionError(
            f"artifact registration forbidden for status {status.value}"
        )


class ResearchArtifactRegistry:
    """Append-only artifact registration owned by the intelligence publishing layer."""

    def __init__(self, run_registry: ResearchRunRegistry) -> None:
        self._runs = run_registry
        self._storage = run_registry.storage

    def register_json_artifact(
        self,
        run_id: str,
        *,
        name: str,
        artifact_type: ResearchArtifactType,
        payload: Any,
        media_type: str = "application/json",
        row_count: Optional[int] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        now: Optional[datetime] = None,
    ) -> ResearchArtifactReference:
        body = serialize_artifact_json(payload)
        resolved_rows = row_count
        if resolved_rows is None and isinstance(payload, list):
            resolved_rows = len(payload)
        if resolved_rows is not None and resolved_rows < 0:
            raise InvalidArtifactError("row_count must be non-negative")
        return self._register_bytes(
            run_id,
            name=name,
            artifact_type=artifact_type,
            payload=body,
            extension=".json",
            media_type=media_type,
            row_count=resolved_rows,
            metadata=dict(metadata or {}),
            now=now,
        )

    def register_file_artifact(
        self,
        run_id: str,
        *,
        name: str,
        artifact_type: ResearchArtifactType,
        source_path: Union[str, Path],
        media_type: Optional[str] = None,
        row_count: Optional[int] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        now: Optional[datetime] = None,
    ) -> ResearchArtifactReference:
        source = Path(source_path)
        if source.is_symlink():
            raise InvalidArtifactError("source must be a regular file, not a symlink")
        if not source.is_file():
            raise InvalidArtifactError(f"source file does not exist: {source}")

        if row_count is not None and row_count < 0:
            raise InvalidArtifactError("row_count must be non-negative")

        try:
            payload = source.read_bytes()
        except OSError as exc:
            raise IntelligenceStorageError(f"unable to read source file: {source}") from exc

        extension = source.suffix.lower() or ".bin"
        return self._register_bytes(
            run_id,
            name=name,
            artifact_type=artifact_type,
            payload=payload,
            extension=extension,
            media_type=_infer_media_type(source, media_type),
            row_count=row_count,
            metadata=dict(metadata or {}),
            now=now,
        )

    def get_artifact(
        self,
        run_id: str,
        artifact_name_or_id: str,
    ) -> ResearchArtifactReference:
        manifest = self._runs.get_run(run_id)
        for artifact in manifest.artifacts:
            if (
                artifact.name == artifact_name_or_id
                or artifact.artifact_id == artifact_name_or_id
            ):
                return artifact
        raise ArtifactNotFoundError(
            f"artifact not found on run {run_id}: {artifact_name_or_id!r}"
        )

    def list_artifacts(self, run_id: str) -> list[ResearchArtifactReference]:
        return list(self._runs.get_run(run_id).artifacts)

    def verify_artifact(
        self,
        run_id: str,
        artifact_name_or_id: str,
        *,
        now: Optional[datetime] = None,
    ) -> ArtifactVerificationResult:
        artifact = self.get_artifact(run_id, artifact_name_or_id)
        stamp = now or utc_now()
        errors: list[str] = []
        path = self._storage.resolve_run_relative_path(run_id, artifact.relative_path)
        exists = path.is_file()
        actual_checksum: Optional[str] = None
        checksum_matches = False
        size_matches = False

        if not exists:
            errors.append("artifact file is missing")
        else:
            try:
                path.relative_to(self._storage.run_dir(run_id).resolve())
            except ValueError:
                exists = False
                errors.append("artifact path escapes run directory")
            else:
                actual_checksum = calculate_sha256(path)
                checksum_matches = hmac.compare_digest(
                    actual_checksum, artifact.checksum
                )
                if not checksum_matches:
                    errors.append("checksum mismatch")
                actual_size = path.stat().st_size
                size_matches = actual_size == artifact.size_bytes
                if not size_matches:
                    errors.append(
                        f"size mismatch: expected {artifact.size_bytes}, found {actual_size}"
                    )

        valid = exists and checksum_matches and size_matches and not errors
        return ArtifactVerificationResult(
            artifact_id=artifact.artifact_id,
            exists=exists,
            checksum_matches=checksum_matches,
            size_matches=size_matches,
            valid=valid,
            expected_checksum=artifact.checksum,
            actual_checksum=actual_checksum,
            verified_at=stamp,
            errors=errors,
        )

    def read_artifact_bytes(
        self,
        run_id: str,
        artifact_name_or_id: str,
        *,
        verify: bool = False,
    ) -> bytes:
        """Read registered artifact bytes through the registry (no free-path reads)."""
        artifact = self.get_artifact(run_id, artifact_name_or_id)
        if verify:
            result = self.verify_artifact(run_id, artifact.artifact_id)
            if not result.valid:
                raise ArtifactIntegrityError(
                    f"artifact {artifact.artifact_id!r} failed integrity verification: "
                    + "; ".join(result.errors)
                )
        path = self._storage.resolve_run_relative_path(run_id, artifact.relative_path)
        if not path.is_file():
            raise ArtifactNotFoundError(
                f"artifact file missing for {artifact.artifact_id!r} on run {run_id}"
            )
        try:
            return path.read_bytes()
        except OSError as exc:
            raise IntelligenceStorageError(
                f"unable to read artifact bytes for {artifact.artifact_id!r}"
            ) from exc

    def read_json_artifact(
        self,
        run_id: str,
        artifact_name_or_id: str,
        *,
        verify: bool = False,
    ) -> Any:
        """Read and parse a registered JSON artifact payload."""
        artifact = self.get_artifact(run_id, artifact_name_or_id)
        media = (artifact.media_type or "").lower()
        if media and "json" not in media and not artifact.relative_path.endswith(".json"):
            raise InvalidArtifactError(
                f"artifact {artifact.artifact_id!r} is not a JSON media type "
                f"(media_type={artifact.media_type!r})"
            )
        raw = self.read_artifact_bytes(run_id, artifact.artifact_id, verify=verify)
        try:
            return json.loads(raw.decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise InvalidArtifactError(
                f"artifact {artifact.artifact_id!r} is not valid UTF-8 JSON"
            ) from exc
        except json.JSONDecodeError as exc:
            raise InvalidArtifactError(
                f"artifact {artifact.artifact_id!r} contains invalid JSON"
            ) from exc

    def _register_bytes(
        self,
        run_id: str,
        *,
        name: str,
        artifact_type: ResearchArtifactType,
        payload: bytes,
        extension: str,
        media_type: Optional[str],
        row_count: Optional[int],
        metadata: dict[str, Any],
        now: Optional[datetime],
    ) -> ResearchArtifactReference:
        cleaned_name = name.strip()
        if not cleaned_name:
            raise InvalidArtifactError("artifact name is required")

        with self._storage.acquire_run_write_lock(run_id):
            manifest = self._runs.get_run(run_id)
            _assert_writable(manifest.run.status)

            if any(item.name == cleaned_name for item in manifest.artifacts):
                raise ArtifactAlreadyExistsError(
                    f"artifact name already registered: {cleaned_name!r}"
                )

            artifact_id = generate_artifact_id()
            # Extremely unlikely; still guard duplicates within the run.
            while any(item.artifact_id == artifact_id for item in manifest.artifacts):
                artifact_id = generate_artifact_id()
            if not is_valid_artifact_id(artifact_id):
                raise InvalidArtifactError(f"invalid generated artifact_id: {artifact_id}")

            filename = _artifact_filename(cleaned_name, artifact_id, extension)
            relative_path = f"{ARTIFACTS_DIRNAME}/{filename}"
            destination = self._storage.resolve_run_relative_path(run_id, relative_path)
            if destination.exists():
                raise ArtifactAlreadyExistsError(
                    f"artifact destination already exists: {relative_path}"
                )

            checksum = hashlib.sha256(payload).hexdigest()
            stamp = now or utc_now()
            reference = ResearchArtifactReference(
                artifact_id=artifact_id,
                name=cleaned_name,
                artifact_type=artifact_type,
                schema_version=ARTIFACT_SCHEMA_VERSION,
                relative_path=relative_path,
                media_type=media_type,
                checksum_algorithm=CHECKSUM_ALGORITHM_SHA256,
                checksum=checksum,
                size_bytes=len(payload),
                row_count=row_count,
                created_at=stamp,
                metadata=metadata,
            )

            # Validate the prospective manifest before writing bytes.
            prospective = sync_artifact_checksums(
                manifest.model_copy(
                    update={
                        "artifacts": [*manifest.artifacts, reference],
                        "run": manifest.run.model_copy(update={"updated_at": stamp}),
                    }
                )
            )
            validate_manifest(prospective, expected_run_id=run_id)

            self._storage.ensure_artifacts_dir(run_id)
            self._storage.write_bytes_atomic(destination, payload)

            # Confirm on-disk digest matches the bytes we intended to store.
            on_disk = calculate_sha256(destination)
            if not hmac.compare_digest(on_disk, checksum):
                self._safe_unlink(destination)
                raise ArtifactIntegrityError(
                    f"on-disk checksum mismatch after write for {relative_path}"
                )

            try:
                self._runs._write_manifest(prospective)
            except Exception as exc:
                self._safe_unlink(destination)
                if isinstance(exc, IntelligenceStorageError):
                    raise
                raise IntelligenceStorageError(
                    f"manifest update failed after artifact write for {run_id}; "
                    "new artifact file was rolled back"
                ) from exc

            return reference

    @staticmethod
    def _safe_unlink(path: Path) -> None:
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass
