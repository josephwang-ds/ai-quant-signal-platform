"""Phase 5.1C — Portfolio publication pipeline tests."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Optional, Sequence

import pytest

from app.portfolio.ports import PublishedRunReference, PublishedSnapshotReference
from app.portfolio.publication import (
    PortfolioPublicationCommand,
    PortfolioPublicationIssueCode,
    PortfolioPublicationService,
    PortfolioPublicationStatus,
)
from app.portfolio.repository import FilesystemPortfolioRepository
from app.portfolio.research_adapter import PublishedResearchResolutionError
from app.portfolio.schemas import (
    PORTFOLIO_MANIFEST_SCHEMA_VERSION,
    AnalyticalWeight,
    PortfolioConstraintSet,
    PortfolioLifecycleStatus,
    PortfolioMandate,
    PortfolioManifest,
    PortfolioMember,
    RebalanceFrequency,
    WeightMethod,
)
from app.portfolio.storage import INTEGRITY_FILENAME, MANIFEST_FILENAME

AWARE = datetime(2026, 7, 29, 16, 0, 0, tzinfo=timezone.utc)
CLOCK = datetime(2026, 7, 29, 17, 30, 0, tzinfo=timezone.utc)
PID = "portfolio_20260729T160000Z_cccccccc"
RUN_A = "run_20260728T041530Z_aaaaaaaa"
RUN_B = "run_20260728T041530Z_bbbbbbbb"
SNAP_A = "snapshot_aaaabbbb"
SNAP_B = "snapshot_ccccdddd"
SNAP_OTHER = "snapshot_eeeeffff"
CHECK_A = "a" * 64
CHECK_B = "b" * 64


def _snapshot(
    snapshot_id: str,
    *,
    checksum: str,
    snapshot_type: str = "research_summary",
) -> PublishedSnapshotReference:
    return PublishedSnapshotReference(
        snapshot_id=snapshot_id,
        name=f"name-{snapshot_id}",
        snapshot_type=snapshot_type,
        schema_version="research-summary-snapshot/v1",
        checksum_algorithm="sha256",
        checksum=checksum,
        size_bytes=12,
        created_at=AWARE,
        integrity_verified=False,
    )


def _run(
    run_id: str,
    *,
    snapshots: list[PublishedSnapshotReference],
    validation_ok: bool = True,
    status: str = "PUBLISHED",
    published_at: Optional[datetime] = AWARE,
    integrity: str = "ok",
    methodology_version: str = "demo-model-v1",
) -> PublishedRunReference:
    return PublishedRunReference(
        run_id=run_id,
        publication_status=status,
        validation_ok=validation_ok,
        published_at=published_at,
        strategy_or_research_name="Demo Research",
        snapshot_references=snapshots,
        source_integrity_status=integrity,
        methodology_version=methodology_version,
    )


class FakeResearchQuery:
    def __init__(
        self,
        runs: dict[str, PublishedRunReference],
        *,
        missing: Optional[set[str]] = None,
        unpublished: Optional[set[str]] = None,
        integrity_failed: Optional[set[str]] = None,
        verify_errors: Optional[dict[str, PublishedResearchResolutionError]] = None,
        identity_swap: Optional[dict[str, str]] = None,
    ) -> None:
        self.runs = runs
        self.missing = missing or set()
        self.unpublished = unpublished or set()
        self.integrity_failed = integrity_failed or set()
        self.verify_errors = verify_errors or {}
        self.identity_swap = identity_swap or {}
        self.get_calls: list[str] = []
        self.verify_calls: list[tuple[str, str]] = []

    def get_published_run(self, run_id: str) -> PublishedRunReference:
        self.get_calls.append(run_id)
        if run_id in self.missing:
            raise PublishedResearchResolutionError(
                "SOURCE_RUN_NOT_FOUND",
                "missing",
                run_id=run_id,
            )
        if run_id in self.unpublished:
            raise PublishedResearchResolutionError(
                "SOURCE_RUN_NOT_PUBLISHED",
                "not published",
                run_id=run_id,
            )
        if run_id in self.integrity_failed:
            raise PublishedResearchResolutionError(
                "SOURCE_RUN_INTEGRITY_FAILED",
                "corrupt",
                run_id=run_id,
            )
        run = self.runs[run_id]
        if run_id in self.identity_swap:
            return run.model_copy(update={"run_id": self.identity_swap[run_id]})
        return run

    def list_snapshot_references(
        self,
        run_id: str,
    ) -> Sequence[PublishedSnapshotReference]:
        return list(self.get_published_run(run_id).snapshot_references)

    def verify_snapshot(
        self,
        run_id: str,
        snapshot_id: str,
    ) -> PublishedSnapshotReference:
        self.verify_calls.append((run_id, snapshot_id))
        key = f"{run_id}:{snapshot_id}"
        if key in self.verify_errors:
            raise self.verify_errors[key]
        run = self.get_published_run(run_id)
        for item in run.snapshot_references:
            if item.snapshot_id == snapshot_id:
                return item.model_copy(update={"integrity_verified": True})
        raise PublishedResearchResolutionError(
            "SOURCE_SNAPSHOT_NOT_FOUND",
            "snapshot missing",
            run_id=run_id,
            snapshot_id=snapshot_id,
        )


def _mandate() -> PortfolioMandate:
    return PortfolioMandate(
        name="Publication Test Portfolio",
        objective="Admit two published research runs with verified snapshots",
        rebalance_frequency=RebalanceFrequency.MONTHLY,
        base_currency="USD",
    )


def _constraints() -> PortfolioConstraintSet:
    return PortfolioConstraintSet(
        long_only=True,
        fully_invested=True,
        allow_cash=False,
        weight_sum_tolerance=Decimal("0.000001"),
    )


def _draft(
    *,
    members: Optional[list[PortfolioMember]] = None,
    version: int = 1,
    weight_method: WeightMethod = WeightMethod.EQUAL,
) -> PortfolioManifest:
    if members is None:
        members = [
            PortfolioMember(
                source_run_id=RUN_A,
                member_order=0,
                selected_snapshot_ids=[SNAP_A],
            ),
            PortfolioMember(
                source_run_id=RUN_B,
                member_order=1,
                selected_snapshot_ids=[SNAP_B],
            ),
        ]
    return PortfolioManifest(
        schema_version=PORTFOLIO_MANIFEST_SCHEMA_VERSION,
        portfolio_id=PID,
        portfolio_version=version,
        lifecycle_status=PortfolioLifecycleStatus.DRAFT,
        mandate=_mandate(),
        members=members,
        constraints=_constraints(),
        weight_method=weight_method,
        created_at=AWARE,
        published_at=None,
    )


def _default_research() -> FakeResearchQuery:
    return FakeResearchQuery(
        {
            RUN_A: _run(RUN_A, snapshots=[_snapshot(SNAP_A, checksum=CHECK_A)]),
            RUN_B: _run(
                RUN_B,
                snapshots=[_snapshot(SNAP_B, checksum=CHECK_B, snapshot_type="signal")],
            ),
        }
    )


@pytest.fixture
def repo(tmp_path: Path) -> FilesystemPortfolioRepository:
    return FilesystemPortfolioRepository(root=tmp_path)


@pytest.fixture
def service(repo: FilesystemPortfolioRepository) -> PortfolioPublicationService:
    return PortfolioPublicationService(
        repo,
        _default_research(),
        now_fn=lambda: CLOCK,
    )


def test_valid_draft_publishes(service: PortfolioPublicationService, repo):
    draft = _draft()
    original = draft.model_dump(mode="json")
    result = service.publish(PortfolioPublicationCommand(manifest=draft))
    assert result.ok
    assert result.status is PortfolioPublicationStatus.PUBLISHED
    assert result.published_at == CLOCK
    assert result.integrity_verified
    assert draft.model_dump(mode="json") == original
    assert draft.lifecycle_status is PortfolioLifecycleStatus.DRAFT
    stored = repo.get_published(PID, 1)
    assert stored.lifecycle_status is PortfolioLifecycleStatus.PUBLISHED
    assert stored.published_at == CLOCK
    assert stored.members[0].member_order == 0
    assert stored.members[1].selected_snapshot_ids == [SNAP_B]
    assert stored.publication_provenance is not None
    assert len(stored.publication_provenance.members) == 2
    assert (
        stored.publication_provenance.members[0].selected_snapshot_checksums[0].checksum
        == CHECK_A
    )
    assert stored.publication_provenance.members[0].selected_snapshot_types == [
        "research_summary"
    ]
    assert stored.publication_provenance.members[1].selected_snapshot_types == ["signal"]


def test_weights_preserved_operator_specified(repo: FilesystemPortfolioRepository):
    research = _default_research()
    service = PortfolioPublicationService(repo, research, now_fn=lambda: CLOCK)
    draft = _draft(
        weight_method=WeightMethod.OPERATOR_SPECIFIED,
        members=[
            PortfolioMember(
                source_run_id=RUN_A,
                member_order=0,
                analytical_weight=AnalyticalWeight(value=Decimal("0.4")),
                selected_snapshot_ids=[SNAP_A],
            ),
            PortfolioMember(
                source_run_id=RUN_B,
                member_order=1,
                analytical_weight=AnalyticalWeight(value=Decimal("0.6")),
                selected_snapshot_ids=[SNAP_B],
            ),
        ],
    )
    result = service.publish(PortfolioPublicationCommand(manifest=draft))
    assert result.ok
    stored = repo.get_published(PID, 1)
    assert stored.members[0].analytical_weight is not None
    assert stored.members[0].analytical_weight.value == Decimal("0.4")
    assert stored.members[1].analytical_weight.value == Decimal("0.6")


def test_missing_run_rejected(repo: FilesystemPortfolioRepository):
    research = FakeResearchQuery({}, missing={RUN_A, RUN_B})
    service = PortfolioPublicationService(repo, research, now_fn=lambda: CLOCK)
    result = service.publish(PortfolioPublicationCommand(manifest=_draft()))
    assert not result.ok
    assert result.status is PortfolioPublicationStatus.REJECTED
    assert any(
        i.code is PortfolioPublicationIssueCode.SOURCE_RUN_NOT_FOUND
        for i in result.issues
    )
    assert repo.list_portfolios(include_draft_only=True) == []


def test_unpublished_run_rejected(repo: FilesystemPortfolioRepository):
    research = FakeResearchQuery(
        {
            RUN_A: _run(RUN_A, snapshots=[_snapshot(SNAP_A, checksum=CHECK_A)]),
            RUN_B: _run(RUN_B, snapshots=[_snapshot(SNAP_B, checksum=CHECK_B)]),
        },
        unpublished={RUN_B},
    )
    service = PortfolioPublicationService(repo, research, now_fn=lambda: CLOCK)
    result = service.publish(PortfolioPublicationCommand(manifest=_draft()))
    assert any(
        i.code is PortfolioPublicationIssueCode.SOURCE_RUN_NOT_PUBLISHED
        for i in result.issues
    )


def test_validation_failure_rejected(repo: FilesystemPortfolioRepository):
    research = FakeResearchQuery(
        {
            RUN_A: _run(RUN_A, snapshots=[_snapshot(SNAP_A, checksum=CHECK_A)]),
            RUN_B: _run(
                RUN_B,
                snapshots=[_snapshot(SNAP_B, checksum=CHECK_B)],
                validation_ok=False,
            ),
        }
    )
    service = PortfolioPublicationService(repo, research, now_fn=lambda: CLOCK)
    result = service.publish(PortfolioPublicationCommand(manifest=_draft()))
    assert any(
        i.code is PortfolioPublicationIssueCode.SOURCE_RUN_VALIDATION_FAILED
        for i in result.issues
    )


def test_integrity_failure_rejected(repo: FilesystemPortfolioRepository):
    research = FakeResearchQuery(
        {
            RUN_A: _run(RUN_A, snapshots=[_snapshot(SNAP_A, checksum=CHECK_A)]),
            RUN_B: _run(RUN_B, snapshots=[_snapshot(SNAP_B, checksum=CHECK_B)]),
        },
        integrity_failed={RUN_B},
    )
    service = PortfolioPublicationService(repo, research, now_fn=lambda: CLOCK)
    result = service.publish(PortfolioPublicationCommand(manifest=_draft()))
    assert any(
        i.code is PortfolioPublicationIssueCode.SOURCE_RUN_INTEGRITY_FAILED
        for i in result.issues
    )


def test_identity_mismatch_rejected(repo: FilesystemPortfolioRepository):
    research = FakeResearchQuery(
        {
            RUN_A: _run(RUN_A, snapshots=[_snapshot(SNAP_A, checksum=CHECK_A)]),
            RUN_B: _run(RUN_B, snapshots=[_snapshot(SNAP_B, checksum=CHECK_B)]),
        },
        identity_swap={RUN_A: RUN_B},
    )
    service = PortfolioPublicationService(repo, research, now_fn=lambda: CLOCK)
    result = service.publish(PortfolioPublicationCommand(manifest=_draft()))
    assert any(
        i.code is PortfolioPublicationIssueCode.SOURCE_IDENTITY_MISMATCH
        for i in result.issues
    )


def test_missing_selected_snapshot_rejected(repo: FilesystemPortfolioRepository):
    research = FakeResearchQuery(
        {
            RUN_A: _run(RUN_A, snapshots=[_snapshot(SNAP_A, checksum=CHECK_A)]),
            RUN_B: _run(RUN_B, snapshots=[_snapshot(SNAP_B, checksum=CHECK_B)]),
        }
    )
    draft = _draft(
        members=[
            PortfolioMember(
                source_run_id=RUN_A,
                member_order=0,
                selected_snapshot_ids=[SNAP_OTHER],
            ),
            PortfolioMember(
                source_run_id=RUN_B,
                member_order=1,
                selected_snapshot_ids=[SNAP_B],
            ),
        ]
    )
    service = PortfolioPublicationService(repo, research, now_fn=lambda: CLOCK)
    result = service.publish(PortfolioPublicationCommand(manifest=draft))
    assert any(
        i.code is PortfolioPublicationIssueCode.SOURCE_SNAPSHOT_NOT_FOUND
        for i in result.issues
    )


def test_empty_selected_snapshots_rejected(repo: FilesystemPortfolioRepository):
    service = PortfolioPublicationService(
        repo, _default_research(), now_fn=lambda: CLOCK
    )
    draft = _draft(
        members=[
            PortfolioMember(
                source_run_id=RUN_A, member_order=0, selected_snapshot_ids=[]
            ),
            PortfolioMember(
                source_run_id=RUN_B,
                member_order=1,
                selected_snapshot_ids=[SNAP_B],
            ),
        ]
    )
    result = service.publish(PortfolioPublicationCommand(manifest=draft))
    assert any(
        i.code is PortfolioPublicationIssueCode.SOURCE_SNAPSHOT_SELECTION_REQUIRED
        for i in result.issues
    )


def test_unsupported_snapshot_type_rejected(repo: FilesystemPortfolioRepository):
    research = FakeResearchQuery(
        {
            RUN_A: _run(
                RUN_A,
                snapshots=[
                    _snapshot(SNAP_A, checksum=CHECK_A, snapshot_type="factor_exposure")
                ],
            ),
            RUN_B: _run(RUN_B, snapshots=[_snapshot(SNAP_B, checksum=CHECK_B)]),
        }
    )
    service = PortfolioPublicationService(repo, research, now_fn=lambda: CLOCK)
    result = service.publish(PortfolioPublicationCommand(manifest=_draft()))
    assert any(
        i.code is PortfolioPublicationIssueCode.SOURCE_SNAPSHOT_UNSUPPORTED_TYPE
        for i in result.issues
    )


def test_snapshot_verify_failure_rejected(repo: FilesystemPortfolioRepository):
    research = FakeResearchQuery(
        {
            RUN_A: _run(RUN_A, snapshots=[_snapshot(SNAP_A, checksum=CHECK_A)]),
            RUN_B: _run(RUN_B, snapshots=[_snapshot(SNAP_B, checksum=CHECK_B)]),
        },
        verify_errors={
            f"{RUN_A}:{SNAP_A}": PublishedResearchResolutionError(
                "SOURCE_SNAPSHOT_INVALID",
                "checksum failed",
                run_id=RUN_A,
                snapshot_id=SNAP_A,
            )
        },
    )
    service = PortfolioPublicationService(repo, research, now_fn=lambda: CLOCK)
    result = service.publish(PortfolioPublicationCommand(manifest=_draft()))
    assert any(
        i.code is PortfolioPublicationIssueCode.SOURCE_SNAPSHOT_INVALID
        for i in result.issues
    )
    assert not repo.exists(PID, version=1)


def test_one_invalid_member_rejects_whole_portfolio(repo: FilesystemPortfolioRepository):
    research = FakeResearchQuery(
        {
            RUN_A: _run(RUN_A, snapshots=[_snapshot(SNAP_A, checksum=CHECK_A)]),
        },
        missing={RUN_B},
    )
    service = PortfolioPublicationService(repo, research, now_fn=lambda: CLOCK)
    result = service.publish(PortfolioPublicationCommand(manifest=_draft()))
    assert not result.ok
    assert not repo.exists(PID, version=1)


def test_idempotent_retry_preserves_timestamp_and_files(
    service: PortfolioPublicationService,
    repo: FilesystemPortfolioRepository,
    tmp_path: Path,
):
    draft = _draft()
    first = service.publish(PortfolioPublicationCommand(manifest=draft))
    path = tmp_path / PID / "published" / "v0001" / MANIFEST_FILENAME
    mtime_before = path.stat().st_mtime_ns
    service2 = PortfolioPublicationService(
        repo,
        _default_research(),
        now_fn=lambda: datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc),
    )
    second = service2.publish(PortfolioPublicationCommand(manifest=draft))
    assert second.status is PortfolioPublicationStatus.ALREADY_PUBLISHED
    assert second.idempotent
    assert second.published_at == first.published_at == CLOCK
    assert path.stat().st_mtime_ns == mtime_before


def test_changed_weight_same_version_conflicts(repo: FilesystemPortfolioRepository):
    research = _default_research()
    service = PortfolioPublicationService(repo, research, now_fn=lambda: CLOCK)
    first = _draft(
        weight_method=WeightMethod.OPERATOR_SPECIFIED,
        members=[
            PortfolioMember(
                source_run_id=RUN_A,
                member_order=0,
                analytical_weight=AnalyticalWeight(value=Decimal("0.5")),
                selected_snapshot_ids=[SNAP_A],
            ),
            PortfolioMember(
                source_run_id=RUN_B,
                member_order=1,
                analytical_weight=AnalyticalWeight(value=Decimal("0.5")),
                selected_snapshot_ids=[SNAP_B],
            ),
        ],
    )
    assert service.publish(PortfolioPublicationCommand(manifest=first)).ok
    changed = _draft(
        weight_method=WeightMethod.OPERATOR_SPECIFIED,
        members=[
            PortfolioMember(
                source_run_id=RUN_A,
                member_order=0,
                analytical_weight=AnalyticalWeight(value=Decimal("0.6")),
                selected_snapshot_ids=[SNAP_A],
            ),
            PortfolioMember(
                source_run_id=RUN_B,
                member_order=1,
                analytical_weight=AnalyticalWeight(value=Decimal("0.4")),
                selected_snapshot_ids=[SNAP_B],
            ),
        ],
    )
    result = service.publish(PortfolioPublicationCommand(manifest=changed))
    assert not result.ok
    assert result.status is PortfolioPublicationStatus.CONFLICT
    assert any(
        i.code is PortfolioPublicationIssueCode.PUBLICATION_VERSION_CONFLICT
        for i in result.issues
    )


def test_changed_membership_conflicts(repo: FilesystemPortfolioRepository):
    research = FakeResearchQuery(
        {
            RUN_A: _run(RUN_A, snapshots=[_snapshot(SNAP_A, checksum=CHECK_A)]),
            RUN_B: _run(RUN_B, snapshots=[_snapshot(SNAP_B, checksum=CHECK_B)]),
            "run_20260728T041530Z_cccccccc": _run(
                "run_20260728T041530Z_cccccccc",
                snapshots=[_snapshot(SNAP_OTHER, checksum="c" * 64)],
            ),
        }
    )
    service = PortfolioPublicationService(repo, research, now_fn=lambda: CLOCK)
    assert service.publish(PortfolioPublicationCommand(manifest=_draft())).ok
    changed = _draft(
        members=[
            PortfolioMember(
                source_run_id=RUN_A,
                member_order=0,
                selected_snapshot_ids=[SNAP_A],
            ),
            PortfolioMember(
                source_run_id="run_20260728T041530Z_cccccccc",
                member_order=1,
                selected_snapshot_ids=[SNAP_OTHER],
            ),
        ]
    )
    result = service.publish(PortfolioPublicationCommand(manifest=changed))
    assert result.status is PortfolioPublicationStatus.CONFLICT
    assert any(
        i.code is PortfolioPublicationIssueCode.PUBLICATION_VERSION_CONFLICT
        for i in result.issues
    )


def test_changed_selected_snapshot_conflicts(repo: FilesystemPortfolioRepository):
    snap_extra = "snapshot_ffffaaaa"
    research = FakeResearchQuery(
        {
            RUN_A: _run(
                RUN_A,
                snapshots=[
                    _snapshot(SNAP_A, checksum=CHECK_A),
                    _snapshot(snap_extra, checksum="d" * 64),
                ],
            ),
            RUN_B: _run(RUN_B, snapshots=[_snapshot(SNAP_B, checksum=CHECK_B)]),
        }
    )
    service = PortfolioPublicationService(repo, research, now_fn=lambda: CLOCK)
    assert service.publish(PortfolioPublicationCommand(manifest=_draft())).ok
    changed = _draft(
        members=[
            PortfolioMember(
                source_run_id=RUN_A,
                member_order=0,
                selected_snapshot_ids=[snap_extra],
            ),
            PortfolioMember(
                source_run_id=RUN_B,
                member_order=1,
                selected_snapshot_ids=[SNAP_B],
            ),
        ]
    )
    result = service.publish(PortfolioPublicationCommand(manifest=changed))
    assert result.status is PortfolioPublicationStatus.CONFLICT
    assert any(
        i.code is PortfolioPublicationIssueCode.PUBLICATION_VERSION_CONFLICT
        for i in result.issues
    )


def test_changed_source_provenance_conflicts(repo: FilesystemPortfolioRepository):
    research = _default_research()
    service = PortfolioPublicationService(repo, research, now_fn=lambda: CLOCK)
    assert service.publish(PortfolioPublicationCommand(manifest=_draft())).ok
    research2 = FakeResearchQuery(
        {
            RUN_A: _run(
                RUN_A,
                snapshots=[_snapshot(SNAP_A, checksum=CHECK_A)],
                published_at=datetime(2026, 7, 30, 1, 0, 0, tzinfo=timezone.utc),
                methodology_version="changed-model",
            ),
            RUN_B: _run(RUN_B, snapshots=[_snapshot(SNAP_B, checksum=CHECK_B)]),
        }
    )
    service2 = PortfolioPublicationService(repo, research2, now_fn=lambda: CLOCK)
    result = service2.publish(PortfolioPublicationCommand(manifest=_draft()))
    assert result.status is PortfolioPublicationStatus.CONFLICT
    assert any(
        i.code is PortfolioPublicationIssueCode.PUBLICATION_VERSION_CONFLICT
        for i in result.issues
    )


def test_dry_run_validated_no_writes(
    service: PortfolioPublicationService,
    repo: FilesystemPortfolioRepository,
    tmp_path: Path,
):
    result = service.publish(
        PortfolioPublicationCommand(manifest=_draft(), dry_run=True)
    )
    assert result.ok
    assert result.status is PortfolioPublicationStatus.VALIDATED
    assert result.prepared_manifest is not None
    assert result.resolved_members
    assert list(tmp_path.iterdir()) == []
    assert repo.list_portfolios(include_draft_only=True) == []


def test_dry_run_rejected_still_queries(repo: FilesystemPortfolioRepository):
    research = FakeResearchQuery({}, missing={RUN_A, RUN_B})
    service = PortfolioPublicationService(repo, research, now_fn=lambda: CLOCK)
    result = service.publish(
        PortfolioPublicationCommand(manifest=_draft(), dry_run=True)
    )
    assert not result.ok
    assert result.status is PortfolioPublicationStatus.REJECTED
    assert research.get_calls


def test_lower_version_does_not_move_latest_backward(
    repo: FilesystemPortfolioRepository,
):
    service = PortfolioPublicationService(
        repo, _default_research(), now_fn=lambda: CLOCK
    )
    assert service.publish(
        PortfolioPublicationCommand(manifest=_draft(version=2))
    ).ok
    assert service.publish(
        PortfolioPublicationCommand(manifest=_draft(version=1))
    ).ok
    assert repo.latest(PID).portfolio_version == 2
    assert repo.list_versions(PID) == [1, 2]


def test_post_write_integrity_failure_prevents_success(
    repo: FilesystemPortfolioRepository,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    service = PortfolioPublicationService(
        repo, _default_research(), now_fn=lambda: CLOCK
    )
    original_publish = repo.publish

    def publish_then_corrupt(manifest):
        stored = original_publish(manifest)
        path = tmp_path / PID / "published" / "v0001" / MANIFEST_FILENAME
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace(PID, PID[:-1] + "d"), encoding="utf-8")
        return stored

    monkeypatch.setattr(repo, "publish", publish_then_corrupt)
    result = service.publish(PortfolioPublicationCommand(manifest=_draft()))
    assert not result.ok
    assert result.status is PortfolioPublicationStatus.FAILED
    assert any(
        i.code is PortfolioPublicationIssueCode.PUBLICATION_INTEGRITY_FAILED
        for i in result.issues
    )


def test_missing_integrity_after_write_detected(
    repo: FilesystemPortfolioRepository,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    service = PortfolioPublicationService(
        repo, _default_research(), now_fn=lambda: CLOCK
    )
    original_publish = repo.publish

    def publish_then_drop_integrity(manifest):
        stored = original_publish(manifest)
        (tmp_path / PID / "published" / "v0001" / INTEGRITY_FILENAME).unlink()
        return stored

    monkeypatch.setattr(repo, "publish", publish_then_drop_integrity)
    result = service.publish(PortfolioPublicationCommand(manifest=_draft()))
    assert not result.ok
    assert result.status is PortfolioPublicationStatus.FAILED
    assert any(
        i.code is PortfolioPublicationIssueCode.PUBLICATION_INTEGRITY_FAILED
        for i in result.issues
    )


def test_domain_invalid_skips_source_resolution(repo: FilesystemPortfolioRepository):
    research = _default_research()
    service = PortfolioPublicationService(repo, research, now_fn=lambda: CLOCK)
    bad = _draft(
        members=[
            PortfolioMember(
                source_run_id=RUN_A, member_order=0, selected_snapshot_ids=[SNAP_A]
            ),
        ]
    )
    result = service.publish(PortfolioPublicationCommand(manifest=bad))
    assert not result.ok
    assert any(
        i.code is PortfolioPublicationIssueCode.PORTFOLIO_DOMAIN_INVALID
        for i in result.issues
    )
    assert research.get_calls == []


def test_snapshot_ownership_mismatch_rejected(repo: FilesystemPortfolioRepository):
    research = FakeResearchQuery(
        {
            RUN_A: _run(RUN_A, snapshots=[_snapshot(SNAP_A, checksum=CHECK_A)]),
            RUN_B: _run(RUN_B, snapshots=[_snapshot(SNAP_B, checksum=CHECK_B)]),
        }
    )
    original_verify = research.verify_snapshot

    def swapped_verify(run_id: str, snapshot_id: str):
        verified = original_verify(run_id, snapshot_id)
        return verified.model_copy(update={"snapshot_id": SNAP_OTHER})

    research.verify_snapshot = swapped_verify  # type: ignore[method-assign]
    service = PortfolioPublicationService(repo, research, now_fn=lambda: CLOCK)
    result = service.publish(PortfolioPublicationCommand(manifest=_draft()))
    assert any(
        i.code is PortfolioPublicationIssueCode.SOURCE_SNAPSHOT_OWNERSHIP_MISMATCH
        for i in result.issues
    )
    assert not repo.exists(PID, version=1)


def test_corrupt_latest_pointer_rejects_success(
    repo: FilesystemPortfolioRepository, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    service = PortfolioPublicationService(
        repo, _default_research(), now_fn=lambda: CLOCK
    )
    original_publish = repo.publish

    def publish_then_corrupt_latest(manifest):
        stored = original_publish(manifest)
        latest = tmp_path / PID / "latest.json"
        latest.write_text("{not-json", encoding="utf-8")
        return stored

    monkeypatch.setattr(repo, "publish", publish_then_corrupt_latest)
    result = service.publish(PortfolioPublicationCommand(manifest=_draft()))
    assert result.status is PortfolioPublicationStatus.FAILED
    assert any(
        i.code is PortfolioPublicationIssueCode.PUBLICATION_INTEGRITY_FAILED
        for i in result.issues
    )


def test_seed_command_rejects_missing_sources_without_writes(tmp_path: Path):
    repo_root = tmp_path / "portfolios"
    manifest_path = tmp_path / "draft.json"
    manifest_path.write_text(
        json.dumps(_draft().model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.portfolio.seed_published_portfolio",
            "--manifest",
            str(manifest_path),
            "--dry-run",
            "--registry-root",
            str(repo_root),
            "--intelligence-root",
            str(tmp_path / "intel"),
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(Path(__file__).resolve().parents[1]),
    )
    assert proc.returncode == 1
    payload = json.loads(proc.stdout)
    assert payload["status"] == "REJECTED"
    assert not any(repo_root.rglob("manifest.json")) if repo_root.exists() else True


def test_seed_invalid_manifest_exit_code(tmp_path: Path):
    missing = tmp_path / "missing.json"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.portfolio.seed_published_portfolio",
            "--manifest",
            str(missing),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(Path(__file__).resolve().parents[1]),
    )
    assert proc.returncode == 1
    payload = json.loads(proc.stdout)
    assert payload["ok"] is False


def test_seed_module_idempotent_with_fake_service(
    repo: FilesystemPortfolioRepository, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    from app.portfolio import seed_published_portfolio as seed_mod

    service = PortfolioPublicationService(
        repo, _default_research(), now_fn=lambda: CLOCK
    )

    def _publish_portfolio_from_manifest(**kwargs):
        return service.publish(
            PortfolioPublicationCommand(
                manifest=kwargs["manifest"],
                dry_run=kwargs["dry_run"],
            )
        )

    monkeypatch.setattr(
        seed_mod,
        "publish_portfolio_from_manifest",
        _publish_portfolio_from_manifest,
    )
    manifest_path = tmp_path / "draft.json"
    manifest_path.write_text(
        json.dumps(_draft().model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )
    first = seed_mod.main(
        ["--manifest", str(manifest_path), "--registry-root", str(tmp_path / "unused")]
    )
    second = seed_mod.main(
        ["--manifest", str(manifest_path), "--registry-root", str(tmp_path / "unused")]
    )
    assert first == 0
    assert second == 0
    assert repo.list_versions(PID) == [1]


def test_dry_run_conflict_when_version_exists(repo: FilesystemPortfolioRepository):
    service = PortfolioPublicationService(
        repo, _default_research(), now_fn=lambda: CLOCK
    )
    assert service.publish(PortfolioPublicationCommand(manifest=_draft())).ok
    changed = _draft(
        weight_method=WeightMethod.OPERATOR_SPECIFIED,
        members=[
            PortfolioMember(
                source_run_id=RUN_A,
                member_order=0,
                analytical_weight=AnalyticalWeight(value=Decimal("0.7")),
                selected_snapshot_ids=[SNAP_A],
            ),
            PortfolioMember(
                source_run_id=RUN_B,
                member_order=1,
                analytical_weight=AnalyticalWeight(value=Decimal("0.3")),
                selected_snapshot_ids=[SNAP_B],
            ),
        ],
    )
    result = service.publish(
        PortfolioPublicationCommand(manifest=changed, dry_run=True)
    )
    assert result.status is PortfolioPublicationStatus.CONFLICT
    assert result.dry_run is True
