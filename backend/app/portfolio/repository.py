"""Portfolio repository port and filesystem adapter (Phase 5.1B).

Storage publication only — does not validate Phase 4 source runs.
"""

from __future__ import annotations

import hmac
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.portfolio.errors import (
    PortfolioDraftNotFoundError,
    PortfolioIntegrityError,
    PortfolioInvalidStateError,
    PortfolioInvalidStoredManifestError,
    PortfolioNotFoundError,
    PortfolioPublicationConflictError,
    PortfolioRepositoryError,
    PortfolioStorageError,
    PortfolioVersionNotFoundError,
)
from app.portfolio.schemas import (
    PortfolioLifecycleStatus,
    PortfolioManifest,
    is_valid_portfolio_id,
)
from app.portfolio.serialization import (
    parse_portfolio_manifest_bytes,
    serialize_portfolio_manifest,
)
from app.portfolio.storage import (
    CHECKSUM_ALGORITHM,
    INTEGRITY_SCHEMA_VERSION,
    LATEST_SCHEMA_VERSION,
    MANIFEST_FILENAME,
    PortfolioStorage,
    sha256_bytes,
    sha256_file,
    version_dirname,
)
from app.portfolio.validation import validate_portfolio_manifest


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


class PortfolioIntegrityRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = INTEGRITY_SCHEMA_VERSION
    algorithm: str = CHECKSUM_ALGORITHM
    content_checksum: str
    portfolio_id: str
    portfolio_version: int
    created_at: datetime


class PortfolioIntegrityResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    portfolio_id: str
    portfolio_version: Optional[int] = None
    draft: bool = False
    valid: bool
    manifest_exists: bool
    integrity_exists: bool
    checksum_matches: bool
    parsed: bool
    identity_matches: bool
    errors: list[str] = Field(default_factory=list)
    content_checksum: Optional[str] = None
    expected_checksum: Optional[str] = None


class PortfolioLatestPointer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = LATEST_SCHEMA_VERSION
    portfolio_id: str
    portfolio_version: int
    content_checksum: str


class PortfolioRepository(ABC):
    """Port for durable Portfolio draft and published-version storage."""

    @abstractmethod
    def save_draft(self, manifest: PortfolioManifest) -> PortfolioManifest:
        """Atomically replace the DRAFT for ``manifest.portfolio_id``."""

    @abstractmethod
    def publish(self, manifest: PortfolioManifest) -> PortfolioManifest:
        """Persist an immutable PUBLISHED version (idempotent on same checksum)."""

    @abstractmethod
    def get_draft(self, portfolio_id: str) -> PortfolioManifest:
        ...

    @abstractmethod
    def get_published(
        self,
        portfolio_id: str,
        version: Optional[int] = None,
    ) -> PortfolioManifest:
        """Load a published version, or latest when ``version`` is None."""

    @abstractmethod
    def list_portfolios(self, *, include_draft_only: bool = True) -> list[str]:
        """Return sorted portfolio IDs present in the registry."""

    @abstractmethod
    def list_versions(self, portfolio_id: str) -> list[int]:
        """Return sorted published versions (draft excluded)."""

    @abstractmethod
    def latest(self, portfolio_id: str) -> PortfolioManifest:
        ...

    @abstractmethod
    def exists(
        self,
        portfolio_id: str,
        *,
        version: Optional[int] = None,
        draft: bool = False,
    ) -> bool:
        ...

    @abstractmethod
    def verify_integrity(
        self,
        portfolio_id: str,
        *,
        version: Optional[int] = None,
        draft: bool = False,
    ) -> PortfolioIntegrityResult:
        ...


class FilesystemPortfolioRepository(PortfolioRepository):
    """Filesystem-backed Portfolio registry under ``PORTFOLIO_OUTPUT_DIR``."""

    def __init__(
        self,
        root: Optional[Path] = None,
        *,
        env: Optional[dict[str, str]] = None,
        storage: Optional[PortfolioStorage] = None,
        now_fn: Optional[Any] = None,
    ) -> None:
        self._storage = storage or PortfolioStorage(root=root, env=env)
        self._now_fn = now_fn or _utc_now

    @property
    def storage(self) -> PortfolioStorage:
        return self._storage

    def save_draft(self, manifest: PortfolioManifest) -> PortfolioManifest:
        if manifest.lifecycle_status is not PortfolioLifecycleStatus.DRAFT:
            raise PortfolioInvalidStateError(
                "save_draft accepts DRAFT manifests only",
                portfolio_id=manifest.portfolio_id,
                portfolio_version=manifest.portfolio_version,
                operation="save_draft",
            )
        if manifest.published_at is not None:
            raise PortfolioInvalidStateError(
                "DRAFT manifests must not set published_at",
                portfolio_id=manifest.portfolio_id,
                operation="save_draft",
            )
        result = validate_portfolio_manifest(manifest)
        if not result.ok:
            codes = ", ".join(issue.code.value for issue in result.issues)
            raise PortfolioInvalidStateError(
                f"draft manifest failed validation: {codes}",
                portfolio_id=manifest.portfolio_id,
                operation="save_draft",
            )

        portfolio_id = manifest.portfolio_id
        self._storage.ensure_root()
        with self._storage.acquire_write_lock(portfolio_id):
            body = serialize_portfolio_manifest(manifest)
            checksum = sha256_bytes(body)
            integrity = PortfolioIntegrityRecord(
                content_checksum=checksum,
                portfolio_id=portfolio_id,
                portfolio_version=manifest.portfolio_version,
                created_at=self._now_fn(),
            )
            self._storage.draft_dir(portfolio_id).mkdir(parents=True, exist_ok=True)
            self._storage.write_bytes_atomic(
                self._storage.draft_manifest_path(portfolio_id),
                body,
                overwrite=True,
            )
            self._storage.write_json_atomic(
                self._storage.draft_integrity_path(portfolio_id),
                integrity.model_dump(mode="json"),
                overwrite=True,
            )
        return parse_portfolio_manifest_bytes(body)

    def publish(self, manifest: PortfolioManifest) -> PortfolioManifest:
        if manifest.lifecycle_status is not PortfolioLifecycleStatus.PUBLISHED:
            raise PortfolioInvalidStateError(
                "publish accepts PUBLISHED manifests only",
                portfolio_id=manifest.portfolio_id,
                portfolio_version=manifest.portfolio_version,
                operation="publish",
            )
        if manifest.published_at is None:
            raise PortfolioInvalidStateError(
                "PUBLISHED manifests require published_at",
                portfolio_id=manifest.portfolio_id,
                operation="publish",
            )
        result = validate_portfolio_manifest(manifest)
        if not result.ok:
            codes = ", ".join(issue.code.value for issue in result.issues)
            raise PortfolioInvalidStateError(
                f"published manifest failed validation: {codes}",
                portfolio_id=manifest.portfolio_id,
                portfolio_version=manifest.portfolio_version,
                operation="publish",
            )

        portfolio_id = manifest.portfolio_id
        version = manifest.portfolio_version
        body = serialize_portfolio_manifest(manifest)
        checksum = sha256_bytes(body)

        self._storage.ensure_root()
        with self._storage.acquire_write_lock(portfolio_id):
            manifest_path = self._storage.published_manifest_path(portfolio_id, version)
            integrity_path = self._storage.published_integrity_path(portfolio_id, version)

            if manifest_path.is_file():
                existing_integrity = self._read_integrity_record(
                    integrity_path,
                    portfolio_id=portfolio_id,
                    portfolio_version=version,
                    require=True,
                )
                if hmac.compare_digest(existing_integrity.content_checksum, checksum):
                    # Idempotent success — do not rewrite immutable files.
                    return self._load_verified_manifest(
                        manifest_path,
                        integrity_path,
                        expected_portfolio_id=portfolio_id,
                        expected_version=version,
                        expected_status=PortfolioLifecycleStatus.PUBLISHED,
                    )
                raise PortfolioPublicationConflictError(
                    "published version already exists with a different content checksum",
                    portfolio_id=portfolio_id,
                    portfolio_version=version,
                    operation="publish",
                    path_category="published",
                )

            integrity = PortfolioIntegrityRecord(
                content_checksum=checksum,
                portfolio_id=portfolio_id,
                portfolio_version=version,
                created_at=self._now_fn(),
            )
            version_dir = self._storage.published_version_dir(portfolio_id, version)
            version_dir.mkdir(parents=True, exist_ok=True)

            # Write integrity after manifest so a lone integrity file cannot appear
            # without a completed manifest; latest pointer last.
            self._storage.write_bytes_atomic(manifest_path, body, overwrite=False)
            on_disk = sha256_file(manifest_path)
            if not hmac.compare_digest(on_disk, checksum):
                raise PortfolioIntegrityError(
                    "on-disk checksum mismatch after publish write",
                    portfolio_id=portfolio_id,
                    portfolio_version=version,
                    operation="publish",
                )
            self._storage.write_json_atomic(
                integrity_path,
                integrity.model_dump(mode="json"),
                overwrite=False,
            )
            self._write_latest_pointer(
                portfolio_id,
                version=version,
                content_checksum=checksum,
            )
            return parse_portfolio_manifest_bytes(body)

    def get_draft(self, portfolio_id: str) -> PortfolioManifest:
        self._storage.validate_portfolio_id(portfolio_id)
        path = self._storage.draft_manifest_path(portfolio_id)
        integrity_path = self._storage.draft_integrity_path(portfolio_id)
        if not path.is_file():
            raise PortfolioDraftNotFoundError(
                f"portfolio draft not found: {portfolio_id}",
                portfolio_id=portfolio_id,
                operation="get_draft",
                path_category="draft",
            )
        return self._load_verified_manifest(
            path,
            integrity_path,
            expected_portfolio_id=portfolio_id,
            expected_version=None,
            expected_status=PortfolioLifecycleStatus.DRAFT,
        )

    def get_published(
        self,
        portfolio_id: str,
        version: Optional[int] = None,
    ) -> PortfolioManifest:
        self._storage.validate_portfolio_id(portfolio_id)
        if version is None:
            return self.latest(portfolio_id)
        if version < 1:
            raise PortfolioVersionNotFoundError(
                f"portfolio version not found: {portfolio_id} v{version}",
                portfolio_id=portfolio_id,
                portfolio_version=version,
                operation="get_published",
            )
        path = self._storage.published_manifest_path(portfolio_id, version)
        integrity_path = self._storage.published_integrity_path(portfolio_id, version)
        if not path.is_file():
            raise PortfolioVersionNotFoundError(
                f"portfolio version not found: {portfolio_id} v{version}",
                portfolio_id=portfolio_id,
                portfolio_version=version,
                operation="get_published",
                path_category="published",
            )
        return self._load_verified_manifest(
            path,
            integrity_path,
            expected_portfolio_id=portfolio_id,
            expected_version=version,
            expected_status=PortfolioLifecycleStatus.PUBLISHED,
        )

    def list_portfolios(self, *, include_draft_only: bool = True) -> list[str]:
        ids: list[str] = []
        for portfolio_id in self._storage.list_portfolio_ids():
            has_published = bool(self._storage.list_published_versions(portfolio_id))
            has_draft = self._storage.draft_manifest_path(portfolio_id).is_file()
            if has_published or (include_draft_only and has_draft):
                ids.append(portfolio_id)
        return ids

    def list_versions(self, portfolio_id: str) -> list[int]:
        self._storage.validate_portfolio_id(portfolio_id)
        if not self._storage.portfolio_dir(portfolio_id).is_dir():
            raise PortfolioNotFoundError(
                f"portfolio not found: {portfolio_id}",
                portfolio_id=portfolio_id,
                operation="list_versions",
            )
        return self._storage.list_published_versions(portfolio_id)

    def latest(self, portfolio_id: str) -> PortfolioManifest:
        self._storage.validate_portfolio_id(portfolio_id)
        versions = self._storage.list_published_versions(portfolio_id)
        if not versions:
            raise PortfolioVersionNotFoundError(
                f"no published versions for portfolio: {portfolio_id}",
                portfolio_id=portfolio_id,
                operation="latest",
                path_category="published",
            )
        pointer_path = self._storage.latest_path(portfolio_id)
        highest = max(versions)
        if pointer_path.is_file():
            pointer = self._read_latest_pointer(pointer_path, portfolio_id)
            if pointer.portfolio_version not in versions:
                raise PortfolioIntegrityError(
                    "latest pointer references a missing published version",
                    portfolio_id=portfolio_id,
                    portfolio_version=pointer.portfolio_version,
                    operation="latest",
                    path_category="latest",
                )
            if pointer.portfolio_version != highest:
                raise PortfolioIntegrityError(
                    "latest pointer does not match highest published version",
                    portfolio_id=portfolio_id,
                    portfolio_version=pointer.portfolio_version,
                    operation="latest",
                    path_category="latest",
                )
            target_version = pointer.portfolio_version
        else:
            target_version = highest
        return self.get_published(portfolio_id, target_version)

    def exists(
        self,
        portfolio_id: str,
        *,
        version: Optional[int] = None,
        draft: bool = False,
    ) -> bool:
        if not is_valid_portfolio_id(portfolio_id):
            return False
        if draft:
            return self._storage.draft_manifest_path(portfolio_id).is_file()
        if version is not None:
            return self._storage.published_manifest_path(portfolio_id, version).is_file()
        return bool(self._storage.list_published_versions(portfolio_id)) or (
            self._storage.draft_manifest_path(portfolio_id).is_file()
        )

    def verify_integrity(
        self,
        portfolio_id: str,
        *,
        version: Optional[int] = None,
        draft: bool = False,
    ) -> PortfolioIntegrityResult:
        errors: list[str] = []
        if not is_valid_portfolio_id(portfolio_id):
            return PortfolioIntegrityResult(
                portfolio_id=portfolio_id,
                portfolio_version=version,
                draft=draft,
                valid=False,
                manifest_exists=False,
                integrity_exists=False,
                checksum_matches=False,
                parsed=False,
                identity_matches=False,
                errors=["invalid portfolio_id"],
            )

        if draft:
            manifest_path = self._storage.draft_manifest_path(portfolio_id)
            integrity_path = self._storage.draft_integrity_path(portfolio_id)
            expected_version = None
            expected_status = PortfolioLifecycleStatus.DRAFT
        else:
            if version is None:
                versions = self._storage.list_published_versions(portfolio_id)
                if not versions:
                    return PortfolioIntegrityResult(
                        portfolio_id=portfolio_id,
                        draft=False,
                        valid=False,
                        manifest_exists=False,
                        integrity_exists=False,
                        checksum_matches=False,
                        parsed=False,
                        identity_matches=False,
                        errors=["no published versions"],
                    )
                version = max(versions)
            manifest_path = self._storage.published_manifest_path(portfolio_id, version)
            integrity_path = self._storage.published_integrity_path(portfolio_id, version)
            expected_version = version
            expected_status = PortfolioLifecycleStatus.PUBLISHED

        manifest_exists = manifest_path.is_file()
        integrity_exists = integrity_path.is_file()
        if not manifest_exists:
            errors.append("manifest missing")
        if not integrity_exists:
            errors.append("integrity record missing")

        expected_checksum: Optional[str] = None
        actual_checksum: Optional[str] = None
        checksum_matches = False
        parsed = False
        identity_matches = False

        if integrity_exists:
            try:
                record = self._read_integrity_record(
                    integrity_path,
                    portfolio_id=portfolio_id,
                    portfolio_version=expected_version,
                    require=True,
                )
                expected_checksum = record.content_checksum
                if record.algorithm != CHECKSUM_ALGORITHM:
                    errors.append(f"unsupported checksum algorithm: {record.algorithm}")
            except PortfolioRepositoryError as exc:
                errors.append(str(exc))

        if manifest_exists:
            try:
                raw = self._storage.read_bytes(manifest_path)
                actual_checksum = sha256_bytes(raw)
                if expected_checksum is not None:
                    checksum_matches = hmac.compare_digest(actual_checksum, expected_checksum)
                    if not checksum_matches:
                        errors.append("checksum mismatch")
                manifest = parse_portfolio_manifest_bytes(raw)
                parsed = True
                identity_matches = manifest.portfolio_id == portfolio_id
                if expected_version is not None:
                    identity_matches = identity_matches and (
                        manifest.portfolio_version == expected_version
                    )
                if manifest.lifecycle_status is not expected_status:
                    errors.append(
                        f"lifecycle_status is {manifest.lifecycle_status.value}, "
                        f"expected {expected_status.value}"
                    )
                    identity_matches = False
                if not identity_matches:
                    errors.append("stored identity/version mismatch")
            except (
                PortfolioStorageError,
                PortfolioInvalidStoredManifestError,
                PortfolioIntegrityError,
            ) as exc:
                errors.append(str(exc))

        valid = (
            manifest_exists
            and integrity_exists
            and checksum_matches
            and parsed
            and identity_matches
            and not errors
        )
        return PortfolioIntegrityResult(
            portfolio_id=portfolio_id,
            portfolio_version=version if not draft else None,
            draft=draft,
            valid=valid,
            manifest_exists=manifest_exists,
            integrity_exists=integrity_exists,
            checksum_matches=checksum_matches,
            parsed=parsed,
            identity_matches=identity_matches,
            errors=errors,
            content_checksum=actual_checksum,
            expected_checksum=expected_checksum,
        )

    def _write_latest_pointer(
        self,
        portfolio_id: str,
        *,
        version: int,
        content_checksum: str,
    ) -> None:
        versions = self._storage.list_published_versions(portfolio_id)
        if not versions:
            return
        highest = max(versions)
        # Publishing an older version must not move latest backward.
        if version < highest:
            return
        pointer = PortfolioLatestPointer(
            portfolio_id=portfolio_id,
            portfolio_version=version,
            content_checksum=content_checksum,
        )
        self._storage.write_json_atomic(
            self._storage.latest_path(portfolio_id),
            pointer.model_dump(mode="json"),
            overwrite=True,
        )

    def _read_latest_pointer(
        self,
        path: Path,
        portfolio_id: str,
    ) -> PortfolioLatestPointer:
        try:
            payload = self._storage.read_json(path)
            pointer = PortfolioLatestPointer.model_validate(payload)
        except Exception as exc:  # noqa: BLE001
            raise PortfolioIntegrityError(
                "latest pointer is corrupt or invalid",
                portfolio_id=portfolio_id,
                operation="latest",
                path_category="latest",
            ) from exc
        if pointer.portfolio_id != portfolio_id:
            raise PortfolioIntegrityError(
                "latest pointer portfolio_id mismatch",
                portfolio_id=portfolio_id,
                operation="latest",
                path_category="latest",
            )
        if pointer.schema_version != LATEST_SCHEMA_VERSION:
            raise PortfolioIntegrityError(
                f"unsupported latest pointer schema: {pointer.schema_version}",
                portfolio_id=portfolio_id,
                operation="latest",
                path_category="latest",
            )
        return pointer

    def _read_integrity_record(
        self,
        path: Path,
        *,
        portfolio_id: str,
        portfolio_version: Optional[int],
        require: bool,
    ) -> PortfolioIntegrityRecord:
        if not path.is_file():
            if require:
                raise PortfolioIntegrityError(
                    "integrity record missing",
                    portfolio_id=portfolio_id,
                    portfolio_version=portfolio_version,
                    path_category="integrity",
                )
            raise PortfolioIntegrityError(
                "integrity record missing",
                portfolio_id=portfolio_id,
                portfolio_version=portfolio_version,
                path_category="integrity",
            )
        try:
            payload = self._storage.read_json(path)
            record = PortfolioIntegrityRecord.model_validate(payload)
        except Exception as exc:  # noqa: BLE001
            raise PortfolioIntegrityError(
                "integrity record is corrupt or invalid",
                portfolio_id=portfolio_id,
                portfolio_version=portfolio_version,
                path_category="integrity",
            ) from exc
        if record.algorithm != CHECKSUM_ALGORITHM:
            raise PortfolioIntegrityError(
                f"unsupported checksum algorithm: {record.algorithm}",
                portfolio_id=portfolio_id,
                portfolio_version=portfolio_version,
                path_category="integrity",
            )
        if record.schema_version != INTEGRITY_SCHEMA_VERSION:
            raise PortfolioIntegrityError(
                f"unsupported integrity schema: {record.schema_version}",
                portfolio_id=portfolio_id,
                portfolio_version=portfolio_version,
                path_category="integrity",
            )
        if record.portfolio_id != portfolio_id:
            raise PortfolioIntegrityError(
                "integrity record portfolio_id mismatch",
                portfolio_id=portfolio_id,
                portfolio_version=portfolio_version,
                path_category="integrity",
            )
        if (
            portfolio_version is not None
            and record.portfolio_version != portfolio_version
        ):
            raise PortfolioIntegrityError(
                "integrity record portfolio_version mismatch",
                portfolio_id=portfolio_id,
                portfolio_version=portfolio_version,
                path_category="integrity",
            )
        return record

    def _load_verified_manifest(
        self,
        manifest_path: Path,
        integrity_path: Path,
        *,
        expected_portfolio_id: str,
        expected_version: Optional[int],
        expected_status: PortfolioLifecycleStatus,
    ) -> PortfolioManifest:
        record = self._read_integrity_record(
            integrity_path,
            portfolio_id=expected_portfolio_id,
            portfolio_version=expected_version,
            require=True,
        )
        raw = self._storage.read_bytes(manifest_path)
        actual = sha256_bytes(raw)
        if not hmac.compare_digest(actual, record.content_checksum):
            raise PortfolioIntegrityError(
                "portfolio manifest checksum mismatch",
                portfolio_id=expected_portfolio_id,
                portfolio_version=expected_version,
                path_category="manifest",
            )
        manifest = parse_portfolio_manifest_bytes(raw)
        if manifest.portfolio_id != expected_portfolio_id:
            raise PortfolioIntegrityError(
                "stored portfolio_id does not match registry location",
                portfolio_id=expected_portfolio_id,
                portfolio_version=expected_version,
                path_category="manifest",
            )
        if (
            expected_version is not None
            and manifest.portfolio_version != expected_version
        ):
            raise PortfolioIntegrityError(
                "stored portfolio_version does not match registry location",
                portfolio_id=expected_portfolio_id,
                portfolio_version=expected_version,
                path_category="manifest",
            )
        if manifest.lifecycle_status is not expected_status:
            raise PortfolioInvalidStoredManifestError(
                f"stored lifecycle_status is {manifest.lifecycle_status.value}, "
                f"expected {expected_status.value}",
                portfolio_id=expected_portfolio_id,
                portfolio_version=expected_version,
                path_category="manifest",
            )
        return manifest
