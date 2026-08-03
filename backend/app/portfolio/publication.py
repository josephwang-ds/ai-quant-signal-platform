"""Portfolio publication application service (Phase 5.1C)."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.intelligence.schemas import ResearchSnapshotType
from app.portfolio.errors import (
    PortfolioPublicationConflictError,
    PortfolioRepositoryError,
)
from app.portfolio.ports import (
    PublishedResearchQueryPort,
    PublishedSnapshotReference,
)
from app.portfolio.repository import PortfolioRepository
from app.portfolio.research_adapter import PublishedResearchResolutionError
from app.portfolio.schemas import (
    MemberPublicationProvenance,
    PortfolioLifecycleStatus,
    PortfolioManifest,
    PortfolioPublicationProvenance,
    SelectedSnapshotProvenance,
)
from app.portfolio.validation import validate_portfolio_manifest

SUPPORTED_SOURCE_SNAPSHOT_TYPES = frozenset(
    {
        ResearchSnapshotType.RESEARCH_SUMMARY.value,
        ResearchSnapshotType.SIGNAL.value,
    }
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


class PortfolioPublicationStatus(str, Enum):
    VALIDATED = "VALIDATED"
    PUBLISHED = "PUBLISHED"
    ALREADY_PUBLISHED = "ALREADY_PUBLISHED"
    REJECTED = "REJECTED"
    CONFLICT = "CONFLICT"
    FAILED = "FAILED"


class PortfolioPublicationIssueCode(str, Enum):
    PORTFOLIO_DOMAIN_INVALID = "PORTFOLIO_DOMAIN_INVALID"
    PORTFOLIO_NOT_DRAFT = "PORTFOLIO_NOT_DRAFT"
    SOURCE_RUN_NOT_FOUND = "SOURCE_RUN_NOT_FOUND"
    SOURCE_RUN_NOT_PUBLISHED = "SOURCE_RUN_NOT_PUBLISHED"
    SOURCE_RUN_VALIDATION_FAILED = "SOURCE_RUN_VALIDATION_FAILED"
    SOURCE_RUN_INTEGRITY_FAILED = "SOURCE_RUN_INTEGRITY_FAILED"
    SOURCE_IDENTITY_MISMATCH = "SOURCE_IDENTITY_MISMATCH"
    SOURCE_SNAPSHOT_SELECTION_REQUIRED = "SOURCE_SNAPSHOT_SELECTION_REQUIRED"
    SOURCE_SNAPSHOT_NOT_FOUND = "SOURCE_SNAPSHOT_NOT_FOUND"
    SOURCE_SNAPSHOT_NOT_AVAILABLE = "SOURCE_SNAPSHOT_NOT_AVAILABLE"
    SOURCE_SNAPSHOT_INVALID = "SOURCE_SNAPSHOT_INVALID"
    SOURCE_SNAPSHOT_OWNERSHIP_MISMATCH = "SOURCE_SNAPSHOT_OWNERSHIP_MISMATCH"
    SOURCE_SNAPSHOT_UNSUPPORTED_TYPE = "SOURCE_SNAPSHOT_UNSUPPORTED_TYPE"
    PUBLICATION_VERSION_CONFLICT = "PUBLICATION_VERSION_CONFLICT"
    PUBLICATION_STORAGE_FAILED = "PUBLICATION_STORAGE_FAILED"
    PUBLICATION_INTEGRITY_FAILED = "PUBLICATION_INTEGRITY_FAILED"


class PortfolioPublicationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: PortfolioPublicationIssueCode
    message: str
    field: Optional[str] = None
    context: dict[str, Any] = Field(default_factory=dict)


class PortfolioPublicationCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest: PortfolioManifest
    dry_run: bool = False
    requested_by: Optional[str] = None
    publication_note: Optional[str] = None


class PortfolioPublicationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    dry_run: bool
    portfolio_id: str
    portfolio_version: int
    status: PortfolioPublicationStatus
    idempotent: bool = False
    published_at: Optional[datetime] = None
    prepared_manifest: Optional[PortfolioManifest] = None
    resolved_members: list[MemberPublicationProvenance] = Field(default_factory=list)
    issues: list[PortfolioPublicationIssue] = Field(default_factory=list)
    integrity_verified: bool = False


def logical_publication_fingerprint(manifest: PortfolioManifest) -> dict[str, Any]:
    """Stable logical content for idempotent publication comparison.

    Excludes repository-generated integrity sidecar timestamps and ``published_at``.
    Excludes per-attempt ``resolved_at`` timestamps while retaining source evidence.
    """
    members = []
    for member in sorted(manifest.members, key=lambda item: item.member_order):
        weight = None
        if member.analytical_weight is not None:
            weight = str(member.analytical_weight.value)
        members.append(
            {
                "member_order": member.member_order,
                "source_run_id": member.source_run_id,
                "display_name": member.display_name,
                "analytical_weight": weight,
                "selected_snapshot_ids": list(member.selected_snapshot_ids),
                "metadata": member.metadata,
            }
        )

    provenance_members: list[dict[str, Any]] = []
    if manifest.publication_provenance is not None:
        for item in manifest.publication_provenance.members:
            provenance_members.append(
                {
                    "source_run_id": item.source_run_id,
                    "source_published_at": (
                        item.source_published_at.isoformat()
                        if item.source_published_at is not None
                        else None
                    ),
                    "source_validation_ok": item.source_validation_ok,
                    "selected_snapshot_ids": list(item.selected_snapshot_ids),
                    "selected_snapshot_types": list(item.selected_snapshot_types),
                    "selected_snapshot_checksums": [
                        checksum.model_dump(mode="json")
                        for checksum in item.selected_snapshot_checksums
                    ],
                    "source_methodology_version": item.source_methodology_version,
                }
            )

    return {
        "schema_version": manifest.schema_version,
        "portfolio_id": manifest.portfolio_id,
        "portfolio_version": manifest.portfolio_version,
        "mandate": manifest.mandate.model_dump(mode="json"),
        "members": members,
        "constraints": manifest.constraints.model_dump(mode="json"),
        "weight_method": manifest.weight_method.value,
        "methodology_version": manifest.methodology_version,
        "publication_provenance_members": provenance_members,
    }


class PortfolioPublicationService:
    """Application workflow: DRAFT → admitted PUBLISHED Portfolio."""

    def __init__(
        self,
        repository: PortfolioRepository,
        research_query: PublishedResearchQueryPort,
        *,
        now_fn: Optional[Callable[[], datetime]] = None,
    ) -> None:
        self._repository = repository
        self._research = research_query
        self._now_fn = now_fn or _utc_now

    def publish(
        self,
        command: PortfolioPublicationCommand,
    ) -> PortfolioPublicationResult:
        draft = command.manifest
        portfolio_id = draft.portfolio_id
        portfolio_version = draft.portfolio_version
        issues: list[PortfolioPublicationIssue] = []

        if draft.lifecycle_status is not PortfolioLifecycleStatus.DRAFT:
            issues.append(
                PortfolioPublicationIssue(
                    code=PortfolioPublicationIssueCode.PORTFOLIO_NOT_DRAFT,
                    message="publication requires a DRAFT portfolio manifest",
                    field="lifecycle_status",
                    context={"lifecycle_status": draft.lifecycle_status.value},
                )
            )
            return self._rejected(
                draft,
                dry_run=command.dry_run,
                issues=issues,
            )

        domain = validate_portfolio_manifest(draft)
        if not domain.ok:
            for item in domain.issues:
                issues.append(
                    PortfolioPublicationIssue(
                        code=PortfolioPublicationIssueCode.PORTFOLIO_DOMAIN_INVALID,
                        message=item.message,
                        field=item.field,
                        context=dict(item.context),
                    )
                )
            return self._rejected(
                draft,
                dry_run=command.dry_run,
                issues=self._sorted_issues(issues),
            )

        resolved_at = self._now_fn()
        member_provenance: list[MemberPublicationProvenance] = []
        for index, member in enumerate(draft.members):
            member_issues, provenance = self._admit_member(
                member_index=index,
                source_run_id=member.source_run_id,
                selected_snapshot_ids=list(member.selected_snapshot_ids),
                resolved_at=resolved_at,
            )
            issues.extend(member_issues)
            if provenance is not None:
                member_provenance.append(provenance)

        if issues:
            return self._rejected(
                draft,
                dry_run=command.dry_run,
                issues=self._sorted_issues(issues),
                resolved_members=member_provenance,
            )

        published_at = resolved_at
        prepared = self._prepare_published_manifest(
            draft,
            published_at=published_at,
            member_provenance=member_provenance,
        )
        prepared_validation = validate_portfolio_manifest(prepared)
        if not prepared_validation.ok:
            for item in prepared_validation.issues:
                issues.append(
                    PortfolioPublicationIssue(
                        code=PortfolioPublicationIssueCode.PORTFOLIO_DOMAIN_INVALID,
                        message=item.message,
                        field=item.field,
                        context=dict(item.context),
                    )
                )
            return self._rejected(
                draft,
                dry_run=command.dry_run,
                issues=self._sorted_issues(issues),
                resolved_members=member_provenance,
            )

        if command.dry_run:
            # Read-only logical conflict / idempotency checks (no mutations).
            existing = self._try_load_existing(
                portfolio_id,
                portfolio_version,
                draft=draft,
                dry_run=True,
                member_provenance=member_provenance,
            )
            if isinstance(existing, PortfolioPublicationResult):
                return existing
            if existing is not None:
                if logical_publication_fingerprint(
                    existing
                ) == logical_publication_fingerprint(prepared):
                    return PortfolioPublicationResult(
                        ok=True,
                        dry_run=True,
                        portfolio_id=portfolio_id,
                        portfolio_version=portfolio_version,
                        status=PortfolioPublicationStatus.ALREADY_PUBLISHED,
                        idempotent=True,
                        published_at=existing.published_at,
                        prepared_manifest=existing,
                        resolved_members=list(
                            existing.publication_provenance.members
                            if existing.publication_provenance is not None
                            else member_provenance
                        ),
                        issues=[],
                        integrity_verified=False,
                    )
                return self._conflict(
                    draft,
                    dry_run=True,
                    issues=[
                        PortfolioPublicationIssue(
                            code=PortfolioPublicationIssueCode.PUBLICATION_VERSION_CONFLICT,
                            message=(
                                "published portfolio version already exists with "
                                "different logical content"
                            ),
                            field="portfolio_version",
                            context={
                                "portfolio_id": portfolio_id,
                                "portfolio_version": portfolio_version,
                            },
                        )
                    ],
                    resolved_members=member_provenance,
                )
            return PortfolioPublicationResult(
                ok=True,
                dry_run=True,
                portfolio_id=portfolio_id,
                portfolio_version=portfolio_version,
                status=PortfolioPublicationStatus.VALIDATED,
                idempotent=False,
                published_at=published_at,
                prepared_manifest=prepared,
                resolved_members=member_provenance,
                issues=[],
                integrity_verified=False,
            )

        existing = self._try_load_existing(
            portfolio_id,
            portfolio_version,
            draft=draft,
            dry_run=False,
            member_provenance=member_provenance,
        )
        if isinstance(existing, PortfolioPublicationResult):
            return existing
        if existing is not None:
            if logical_publication_fingerprint(
                existing
            ) == logical_publication_fingerprint(prepared):
                integrity = self._repository.verify_integrity(
                    portfolio_id,
                    version=portfolio_version,
                )
                return PortfolioPublicationResult(
                    ok=True,
                    dry_run=False,
                    portfolio_id=portfolio_id,
                    portfolio_version=portfolio_version,
                    status=PortfolioPublicationStatus.ALREADY_PUBLISHED,
                    idempotent=True,
                    published_at=existing.published_at,
                    prepared_manifest=existing,
                    resolved_members=list(
                        existing.publication_provenance.members
                        if existing.publication_provenance is not None
                        else member_provenance
                    ),
                    issues=[],
                    integrity_verified=integrity.valid,
                )
            return self._conflict(
                draft,
                dry_run=False,
                issues=[
                    PortfolioPublicationIssue(
                        code=PortfolioPublicationIssueCode.PUBLICATION_VERSION_CONFLICT,
                        message=(
                            "published portfolio version already exists with "
                            "different logical content"
                        ),
                        field="portfolio_version",
                        context={
                            "portfolio_id": portfolio_id,
                            "portfolio_version": portfolio_version,
                        },
                    )
                ],
                resolved_members=member_provenance,
            )

        try:
            self._repository.publish(prepared)
        except PortfolioPublicationConflictError as exc:
            return self._conflict(
                draft,
                dry_run=False,
                issues=[
                    PortfolioPublicationIssue(
                        code=PortfolioPublicationIssueCode.PUBLICATION_VERSION_CONFLICT,
                        message=str(exc),
                        field="portfolio_version",
                        context=dict(exc.context),
                    )
                ],
                resolved_members=member_provenance,
            )
        except PortfolioRepositoryError as exc:
            return self._failed(
                draft,
                dry_run=False,
                issues=[
                    PortfolioPublicationIssue(
                        code=PortfolioPublicationIssueCode.PUBLICATION_STORAGE_FAILED,
                        message=str(exc),
                        context=dict(exc.context),
                    )
                ],
                resolved_members=member_provenance,
            )
        except Exception as exc:  # noqa: BLE001 — map unexpected storage failures
            return self._failed(
                draft,
                dry_run=False,
                issues=[
                    PortfolioPublicationIssue(
                        code=PortfolioPublicationIssueCode.PUBLICATION_STORAGE_FAILED,
                        message=str(exc),
                    )
                ],
                resolved_members=member_provenance,
            )

        verify_issues = self._verify_persisted(
            prepared,
            expected_published_at=published_at,
        )
        if verify_issues:
            return self._failed(
                draft,
                dry_run=False,
                issues=self._sorted_issues(verify_issues),
                resolved_members=member_provenance,
            )

        return PortfolioPublicationResult(
            ok=True,
            dry_run=False,
            portfolio_id=portfolio_id,
            portfolio_version=portfolio_version,
            status=PortfolioPublicationStatus.PUBLISHED,
            idempotent=False,
            published_at=published_at,
            prepared_manifest=prepared,
            resolved_members=member_provenance,
            issues=[],
            integrity_verified=True,
        )

    def _admit_member(
        self,
        *,
        member_index: int,
        source_run_id: str,
        selected_snapshot_ids: list[str],
        resolved_at: datetime,
    ) -> tuple[list[PortfolioPublicationIssue], Optional[MemberPublicationProvenance]]:
        issues: list[PortfolioPublicationIssue] = []
        field_prefix = f"members[{member_index}]"

        if not selected_snapshot_ids:
            issues.append(
                PortfolioPublicationIssue(
                    code=PortfolioPublicationIssueCode.SOURCE_SNAPSHOT_SELECTION_REQUIRED,
                    message=(
                        "each portfolio member must reference at least one "
                        "eligible published research snapshot"
                    ),
                    field=f"{field_prefix}.selected_snapshot_ids",
                    context={"source_run_id": source_run_id},
                )
            )
            return issues, None

        try:
            run = self._research.get_published_run(source_run_id)
        except PublishedResearchResolutionError as exc:
            issues.append(self._map_resolution_error(exc, field_prefix=field_prefix))
            return issues, None

        if run.run_id != source_run_id:
            issues.append(
                PortfolioPublicationIssue(
                    code=PortfolioPublicationIssueCode.SOURCE_IDENTITY_MISMATCH,
                    message="resolved run identity does not match source_run_id",
                    field=f"{field_prefix}.source_run_id",
                    context={
                        "requested": source_run_id,
                        "resolved": run.run_id,
                    },
                )
            )
            return issues, None

        if run.publication_status != "PUBLISHED":
            issues.append(
                PortfolioPublicationIssue(
                    code=PortfolioPublicationIssueCode.SOURCE_RUN_NOT_PUBLISHED,
                    message=(
                        "source research run is not in the canonical Published state"
                    ),
                    field=f"{field_prefix}.source_run_id",
                    context={
                        "source_run_id": source_run_id,
                        "publication_status": run.publication_status,
                    },
                )
            )
            return issues, None

        if run.published_at is None:
            issues.append(
                PortfolioPublicationIssue(
                    code=PortfolioPublicationIssueCode.SOURCE_RUN_NOT_PUBLISHED,
                    message="source research run is missing published_at metadata",
                    field=f"{field_prefix}.source_run_id",
                    context={"source_run_id": source_run_id},
                )
            )
            return issues, None

        if not run.validation_ok:
            issues.append(
                PortfolioPublicationIssue(
                    code=PortfolioPublicationIssueCode.SOURCE_RUN_VALIDATION_FAILED,
                    message="source research run validation.ok is false",
                    field=f"{field_prefix}.source_run_id",
                    context={"source_run_id": source_run_id},
                )
            )
            return issues, None

        if run.source_integrity_status != "ok":
            issues.append(
                PortfolioPublicationIssue(
                    code=PortfolioPublicationIssueCode.SOURCE_RUN_INTEGRITY_FAILED,
                    message="source research run failed integrity admission",
                    field=f"{field_prefix}.source_run_id",
                    context={
                        "source_run_id": source_run_id,
                        "source_integrity_status": run.source_integrity_status,
                    },
                )
            )
            return issues, None

        by_id = {item.snapshot_id: item for item in run.snapshot_references}
        selected_checksums: list[SelectedSnapshotProvenance] = []
        for snapshot_id in selected_snapshot_ids:
            listed = by_id.get(snapshot_id)
            if listed is None:
                issues.append(
                    PortfolioPublicationIssue(
                        code=PortfolioPublicationIssueCode.SOURCE_SNAPSHOT_NOT_FOUND,
                        message="selected snapshot is not registered on the source run",
                        field=f"{field_prefix}.selected_snapshot_ids",
                        context={
                            "source_run_id": source_run_id,
                            "snapshot_id": snapshot_id,
                        },
                    )
                )
                continue

            if listed.snapshot_type not in SUPPORTED_SOURCE_SNAPSHOT_TYPES:
                issues.append(
                    PortfolioPublicationIssue(
                        code=PortfolioPublicationIssueCode.SOURCE_SNAPSHOT_UNSUPPORTED_TYPE,
                        message=(
                            "selected snapshot type is not supported as portfolio "
                            "provenance input"
                        ),
                        field=f"{field_prefix}.selected_snapshot_ids",
                        context={
                            "source_run_id": source_run_id,
                            "snapshot_id": snapshot_id,
                            "snapshot_type": listed.snapshot_type,
                            "supported": sorted(SUPPORTED_SOURCE_SNAPSHOT_TYPES),
                        },
                    )
                )
                continue

            try:
                verified = self._research.verify_snapshot(source_run_id, snapshot_id)
            except PublishedResearchResolutionError as exc:
                issues.append(
                    self._map_resolution_error(exc, field_prefix=field_prefix)
                )
                continue

            ownership_issue = self._check_snapshot_ownership(
                source_run_id=source_run_id,
                snapshot_id=snapshot_id,
                verified=verified,
                listed=listed,
                field_prefix=field_prefix,
            )
            if ownership_issue is not None:
                issues.append(ownership_issue)
                continue

            selected_checksums.append(
                SelectedSnapshotProvenance(
                    snapshot_id=verified.snapshot_id,
                    checksum=verified.checksum,
                    snapshot_type=verified.snapshot_type,
                    schema_version=verified.schema_version,
                )
            )

        if issues:
            return issues, None

        return [], MemberPublicationProvenance(
            source_run_id=run.run_id,
            source_published_at=run.published_at,
            source_validation_ok=run.validation_ok,
            selected_snapshot_ids=list(selected_snapshot_ids),
            selected_snapshot_types=[item.snapshot_type for item in selected_checksums],
            selected_snapshot_checksums=selected_checksums,
            source_methodology_version=run.methodology_version,
            resolved_at=resolved_at,
        )

    def _check_snapshot_ownership(
        self,
        *,
        source_run_id: str,
        snapshot_id: str,
        verified: PublishedSnapshotReference,
        listed: PublishedSnapshotReference,
        field_prefix: str,
    ) -> Optional[PortfolioPublicationIssue]:
        if verified.snapshot_id != snapshot_id:
            return PortfolioPublicationIssue(
                code=PortfolioPublicationIssueCode.SOURCE_SNAPSHOT_OWNERSHIP_MISMATCH,
                message="verified snapshot identity mismatch",
                field=f"{field_prefix}.selected_snapshot_ids",
                context={
                    "source_run_id": source_run_id,
                    "snapshot_id": snapshot_id,
                    "resolved_snapshot_id": verified.snapshot_id,
                },
            )
        if verified.checksum != listed.checksum:
            return PortfolioPublicationIssue(
                code=PortfolioPublicationIssueCode.SOURCE_SNAPSHOT_INVALID,
                message="verified snapshot checksum does not match run reference",
                field=f"{field_prefix}.selected_snapshot_ids",
                context={
                    "source_run_id": source_run_id,
                    "snapshot_id": snapshot_id,
                },
            )
        return None

    def _prepare_published_manifest(
        self,
        draft: PortfolioManifest,
        *,
        published_at: datetime,
        member_provenance: list[MemberPublicationProvenance],
    ) -> PortfolioManifest:
        payload = draft.model_dump(mode="python")
        payload["lifecycle_status"] = PortfolioLifecycleStatus.PUBLISHED
        payload["published_at"] = published_at
        payload["publication_provenance"] = PortfolioPublicationProvenance(
            resolved_at=published_at,
            members=member_provenance,
        )
        # Preserve original member order from the draft (not sorted).
        return PortfolioManifest.model_validate(payload)

    def _try_load_existing(
        self,
        portfolio_id: str,
        version: int,
        *,
        draft: PortfolioManifest,
        dry_run: bool,
        member_provenance: list[MemberPublicationProvenance],
    ):
        """Return existing manifest, ``None``, or a FAILED result on corrupt storage."""
        if not self._repository.exists(portfolio_id, version=version):
            return None
        try:
            return self._load_existing_published(portfolio_id, version)
        except PortfolioRepositoryError as exc:
            return self._failed(
                draft,
                dry_run=dry_run,
                issues=[
                    PortfolioPublicationIssue(
                        code=PortfolioPublicationIssueCode.PUBLICATION_INTEGRITY_FAILED,
                        message=str(exc),
                        context=dict(exc.context),
                    )
                ],
                resolved_members=member_provenance,
            )

    def _load_existing_published(
        self,
        portfolio_id: str,
        version: int,
    ) -> Optional[PortfolioManifest]:
        if not self._repository.exists(portfolio_id, version=version):
            return None
        return self._repository.get_published(portfolio_id, version)

    def _verify_persisted(
        self,
        prepared: PortfolioManifest,
        *,
        expected_published_at: datetime,
    ) -> list[PortfolioPublicationIssue]:
        issues: list[PortfolioPublicationIssue] = []
        portfolio_id = prepared.portfolio_id
        version = prepared.portfolio_version
        try:
            stored = self._repository.get_published(portfolio_id, version)
            integrity = self._repository.verify_integrity(
                portfolio_id,
                version=version,
            )
        except PortfolioRepositoryError as exc:
            issues.append(
                PortfolioPublicationIssue(
                    code=PortfolioPublicationIssueCode.PUBLICATION_INTEGRITY_FAILED,
                    message=str(exc),
                    context=dict(exc.context),
                )
            )
            return issues

        if not integrity.valid:
            issues.append(
                PortfolioPublicationIssue(
                    code=PortfolioPublicationIssueCode.PUBLICATION_INTEGRITY_FAILED,
                    message="published portfolio failed post-write integrity verification",
                    context={"errors": list(integrity.errors)},
                )
            )

        if logical_publication_fingerprint(stored) != logical_publication_fingerprint(
            prepared
        ):
            issues.append(
                PortfolioPublicationIssue(
                    code=PortfolioPublicationIssueCode.PUBLICATION_INTEGRITY_FAILED,
                    message="stored published manifest does not match prepared manifest",
                )
            )

        if stored.published_at != expected_published_at:
            issues.append(
                PortfolioPublicationIssue(
                    code=PortfolioPublicationIssueCode.PUBLICATION_INTEGRITY_FAILED,
                    message="stored published_at does not match prepared timestamp",
                )
            )

        try:
            latest = self._repository.latest(portfolio_id)
            versions = self._repository.list_versions(portfolio_id)
            highest = max(versions) if versions else version
            if version == highest and latest.portfolio_version != version:
                issues.append(
                    PortfolioPublicationIssue(
                        code=PortfolioPublicationIssueCode.PUBLICATION_INTEGRITY_FAILED,
                        message="latest pointer does not resolve to the published version",
                        context={
                            "expected_version": version,
                            "latest_version": latest.portfolio_version,
                        },
                    )
                )
        except PortfolioRepositoryError as exc:
            issues.append(
                PortfolioPublicationIssue(
                    code=PortfolioPublicationIssueCode.PUBLICATION_INTEGRITY_FAILED,
                    message=str(exc),
                    context=dict(exc.context),
                )
            )
        return issues

    def _map_resolution_error(
        self,
        exc: PublishedResearchResolutionError,
        *,
        field_prefix: str,
    ) -> PortfolioPublicationIssue:
        try:
            code = PortfolioPublicationIssueCode(exc.code)
        except ValueError:
            code = PortfolioPublicationIssueCode.SOURCE_RUN_INTEGRITY_FAILED
        context: dict[str, Any] = {}
        if exc.run_id is not None:
            context["source_run_id"] = exc.run_id
        if exc.snapshot_id is not None:
            context["snapshot_id"] = exc.snapshot_id
        field = f"{field_prefix}.source_run_id"
        if exc.snapshot_id is not None:
            field = f"{field_prefix}.selected_snapshot_ids"
        return PortfolioPublicationIssue(
            code=code,
            message=exc.message,
            field=field,
            context=context,
        )

    def _rejected(
        self,
        draft: PortfolioManifest,
        *,
        dry_run: bool,
        issues: list[PortfolioPublicationIssue],
        resolved_members: Optional[list[MemberPublicationProvenance]] = None,
    ) -> PortfolioPublicationResult:
        return self._terminal(
            draft,
            dry_run=dry_run,
            status=PortfolioPublicationStatus.REJECTED,
            issues=issues,
            resolved_members=resolved_members,
        )

    def _conflict(
        self,
        draft: PortfolioManifest,
        *,
        dry_run: bool,
        issues: list[PortfolioPublicationIssue],
        resolved_members: Optional[list[MemberPublicationProvenance]] = None,
    ) -> PortfolioPublicationResult:
        return self._terminal(
            draft,
            dry_run=dry_run,
            status=PortfolioPublicationStatus.CONFLICT,
            issues=issues,
            resolved_members=resolved_members,
        )

    def _failed(
        self,
        draft: PortfolioManifest,
        *,
        dry_run: bool,
        issues: list[PortfolioPublicationIssue],
        resolved_members: Optional[list[MemberPublicationProvenance]] = None,
    ) -> PortfolioPublicationResult:
        return self._terminal(
            draft,
            dry_run=dry_run,
            status=PortfolioPublicationStatus.FAILED,
            issues=issues,
            resolved_members=resolved_members,
        )

    def _terminal(
        self,
        draft: PortfolioManifest,
        *,
        dry_run: bool,
        status: PortfolioPublicationStatus,
        issues: list[PortfolioPublicationIssue],
        resolved_members: Optional[list[MemberPublicationProvenance]] = None,
    ) -> PortfolioPublicationResult:
        return PortfolioPublicationResult(
            ok=False,
            dry_run=dry_run,
            portfolio_id=draft.portfolio_id,
            portfolio_version=draft.portfolio_version,
            status=status,
            idempotent=False,
            published_at=None,
            prepared_manifest=None,
            resolved_members=list(resolved_members or []),
            issues=self._sorted_issues(issues),
            integrity_verified=False,
        )

    @staticmethod
    def _sorted_issues(
        issues: list[PortfolioPublicationIssue],
    ) -> list[PortfolioPublicationIssue]:
        return sorted(
            issues,
            key=lambda item: (
                item.code.value,
                item.field or "",
                item.message,
                str(sorted(item.context.items())),
            ),
        )