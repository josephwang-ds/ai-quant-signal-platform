"""Phase 5.1B — Portfolio filesystem registry tests."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from app.portfolio.errors import (
    PortfolioDraftNotFoundError,
    PortfolioIntegrityError,
    PortfolioInvalidStateError,
    PortfolioLockError,
    PortfolioPublicationConflictError,
    PortfolioStorageError,
    PortfolioVersionNotFoundError,
)
from app.portfolio.repository import FilesystemPortfolioRepository
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
from app.portfolio.serialization import serialize_portfolio_manifest
from app.portfolio.storage import (
    INTEGRITY_FILENAME,
    MANIFEST_FILENAME,
    PortfolioStorage,
    sha256_bytes,
    version_dirname,
)

AWARE = datetime(2026, 7, 29, 15, 0, 0, tzinfo=timezone.utc)
PID_A = "portfolio_20260729T150000Z_aaaaaaaa"
PID_B = "portfolio_20260729T150000Z_bbbbbbbb"
RUN_A = "run_20260728T041530Z_aaaaaaaa"
RUN_B = "run_20260728T041530Z_bbbbbbbb"


def _mandate() -> PortfolioMandate:
    return PortfolioMandate(
        name="Registry Test Portfolio",
        objective="Persist published research run membership for review",
        rebalance_frequency=RebalanceFrequency.MONTHLY,
        base_currency="USD",
    )


def _constraints(**overrides) -> PortfolioConstraintSet:
    payload = {
        "long_only": True,
        "fully_invested": True,
        "allow_cash": False,
        "weight_sum_tolerance": Decimal("0.000001"),
    }
    payload.update(overrides)
    return PortfolioConstraintSet(**payload)


def _member(run_id: str, order: int, weight: Decimal | None = None) -> PortfolioMember:
    return PortfolioMember(
        source_run_id=run_id,
        member_order=order,
        analytical_weight=None if weight is None else AnalyticalWeight(value=weight),
    )


def _draft_manifest(portfolio_id: str = PID_A, version: int = 1) -> PortfolioManifest:
    return PortfolioManifest(
        schema_version=PORTFOLIO_MANIFEST_SCHEMA_VERSION,
        portfolio_id=portfolio_id,
        portfolio_version=version,
        lifecycle_status=PortfolioLifecycleStatus.DRAFT,
        mandate=_mandate(),
        members=[_member(RUN_A, 0), _member(RUN_B, 1)],
        constraints=_constraints(),
        weight_method=WeightMethod.EQUAL,
        created_at=AWARE,
        published_at=None,
    )


def _published_manifest(
    portfolio_id: str = PID_A,
    version: int = 1,
    *,
    weight_a: Decimal = Decimal("0.5"),
    weight_b: Decimal = Decimal("0.5"),
) -> PortfolioManifest:
    return PortfolioManifest(
        schema_version=PORTFOLIO_MANIFEST_SCHEMA_VERSION,
        portfolio_id=portfolio_id,
        portfolio_version=version,
        lifecycle_status=PortfolioLifecycleStatus.PUBLISHED,
        mandate=_mandate(),
        members=[
            _member(RUN_A, 0, weight_a),
            _member(RUN_B, 1, weight_b),
        ],
        constraints=_constraints(),
        weight_method=WeightMethod.OPERATOR_SPECIFIED,
        created_at=AWARE,
        published_at=AWARE,
    )


@pytest.fixture
def repo(tmp_path: Path) -> FilesystemPortfolioRepository:
    return FilesystemPortfolioRepository(root=tmp_path)


# --- Layout ---


def test_draft_and_published_layout(repo: FilesystemPortfolioRepository, tmp_path: Path):
    repo.save_draft(_draft_manifest())
    repo.publish(_published_manifest())

    draft_manifest = tmp_path / PID_A / "draft" / MANIFEST_FILENAME
    published_manifest = tmp_path / PID_A / "published" / "v0001" / MANIFEST_FILENAME
    latest = tmp_path / PID_A / "latest.json"
    assert draft_manifest.is_file()
    assert published_manifest.is_file()
    assert (tmp_path / PID_A / "draft" / INTEGRITY_FILENAME).is_file()
    assert (tmp_path / PID_A / "published" / "v0001" / INTEGRITY_FILENAME).is_file()
    assert latest.is_file()
    assert version_dirname(1) == "v0001"
    assert version_dirname(12) == "v0012"


def test_temporary_files_excluded_from_lists(
    repo: FilesystemPortfolioRepository, tmp_path: Path
):
    repo.publish(_published_manifest())
    published = tmp_path / PID_A / "published"
    junk = published / ".manifest.json.tmp"
    junk.write_text("partial", encoding="utf-8")
    assert repo.list_versions(PID_A) == [1]
    assert junk.is_file()


# --- Drafts ---


def test_draft_save_and_read(repo: FilesystemPortfolioRepository):
    saved = repo.save_draft(_draft_manifest())
    loaded = repo.get_draft(PID_A)
    assert loaded.portfolio_id == PID_A
    assert loaded.lifecycle_status is PortfolioLifecycleStatus.DRAFT
    assert saved.model_dump(mode="json") == loaded.model_dump(mode="json")


def test_draft_atomic_replacement(repo: FilesystemPortfolioRepository):
    repo.save_draft(_draft_manifest(version=1))
    updated = _draft_manifest(version=2)
    repo.save_draft(updated)
    loaded = repo.get_draft(PID_A)
    assert loaded.portfolio_version == 2


def test_published_manifest_rejected_by_draft_save(repo: FilesystemPortfolioRepository):
    with pytest.raises(PortfolioInvalidStateError):
        repo.save_draft(_published_manifest())


def test_draft_not_in_published_version_list(repo: FilesystemPortfolioRepository):
    repo.save_draft(_draft_manifest())
    assert repo.list_versions(PID_A) == []
    assert repo.exists(PID_A, draft=True)
    assert not repo.exists(PID_A, version=1)


def test_draft_replacement_does_not_affect_published(repo: FilesystemPortfolioRepository):
    published = repo.publish(_published_manifest(version=1))
    repo.save_draft(_draft_manifest(version=2))
    again = repo.get_published(PID_A, 1)
    assert again.model_dump(mode="json") == published.model_dump(mode="json")


# --- Publication ---


def test_publish_version_one_and_later(repo: FilesystemPortfolioRepository):
    first = repo.publish(_published_manifest(version=1))
    second = repo.publish(_published_manifest(version=2, weight_a=Decimal("0.6"), weight_b=Decimal("0.4")))
    assert repo.list_versions(PID_A) == [1, 2]
    assert repo.latest(PID_A).portfolio_version == 2
    assert first.portfolio_version == 1
    assert second.portfolio_version == 2


def test_same_content_same_version_idempotent(repo: FilesystemPortfolioRepository, tmp_path: Path):
    manifest = _published_manifest(version=1)
    first = repo.publish(manifest)
    path = tmp_path / PID_A / "published" / "v0001" / MANIFEST_FILENAME
    mtime_before = path.stat().st_mtime_ns
    second = repo.publish(manifest)
    mtime_after = path.stat().st_mtime_ns
    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    assert mtime_before == mtime_after


def test_different_content_same_version_conflict(repo: FilesystemPortfolioRepository):
    repo.publish(_published_manifest(version=1, weight_a=Decimal("0.5"), weight_b=Decimal("0.5")))
    with pytest.raises(PortfolioPublicationConflictError):
        repo.publish(
            _published_manifest(version=1, weight_a=Decimal("0.6"), weight_b=Decimal("0.4"))
        )


def test_draft_rejected_by_publish(repo: FilesystemPortfolioRepository):
    with pytest.raises(PortfolioInvalidStateError):
        repo.publish(_draft_manifest())


def test_latest_resolves_highest_version(repo: FilesystemPortfolioRepository):
    repo.publish(_published_manifest(version=1))
    repo.publish(_published_manifest(version=3, weight_a=Decimal("0.7"), weight_b=Decimal("0.3")))
    # Publish v2 after v3 — latest must remain 3
    repo.publish(_published_manifest(version=2, weight_a=Decimal("0.55"), weight_b=Decimal("0.45")))
    assert repo.latest(PID_A).portfolio_version == 3
    assert repo.list_versions(PID_A) == [1, 2, 3]


# --- Integrity ---


def test_checksum_generated_and_verified(repo: FilesystemPortfolioRepository, tmp_path: Path):
    manifest = _published_manifest()
    repo.publish(manifest)
    expected = sha256_bytes(serialize_portfolio_manifest(manifest))
    integrity = json.loads(
        (tmp_path / PID_A / "published" / "v0001" / INTEGRITY_FILENAME).read_text(
            encoding="utf-8"
        )
    )
    assert integrity["algorithm"] == "sha256"
    assert integrity["content_checksum"] == expected
    result = repo.verify_integrity(PID_A, version=1)
    assert result.valid
    assert result.checksum_matches


def test_manifest_tampering_detected(repo: FilesystemPortfolioRepository, tmp_path: Path):
    repo.publish(_published_manifest())
    path = tmp_path / PID_A / "published" / "v0001" / MANIFEST_FILENAME
    path.write_text(path.read_text(encoding="utf-8").replace("0.5", "0.6"), encoding="utf-8")
    with pytest.raises(PortfolioIntegrityError):
        repo.get_published(PID_A, 1)
    result = repo.verify_integrity(PID_A, version=1)
    assert not result.valid
    assert not result.checksum_matches


def test_integrity_metadata_tampering_detected(
    repo: FilesystemPortfolioRepository, tmp_path: Path
):
    repo.publish(_published_manifest())
    path = tmp_path / PID_A / "published" / "v0001" / INTEGRITY_FILENAME
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["content_checksum"] = "0" * 64
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(PortfolioIntegrityError):
        repo.get_published(PID_A, 1)


def test_missing_integrity_record_detected(repo: FilesystemPortfolioRepository, tmp_path: Path):
    repo.publish(_published_manifest())
    (tmp_path / PID_A / "published" / "v0001" / INTEGRITY_FILENAME).unlink()
    with pytest.raises(PortfolioIntegrityError):
        repo.get_published(PID_A, 1)
    result = repo.verify_integrity(PID_A, version=1)
    assert not result.valid
    assert not result.integrity_exists


def test_unsupported_algorithm_rejected(repo: FilesystemPortfolioRepository, tmp_path: Path):
    repo.publish(_published_manifest())
    path = tmp_path / PID_A / "published" / "v0001" / INTEGRITY_FILENAME
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["algorithm"] = "md5"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(PortfolioIntegrityError):
        repo.get_published(PID_A, 1)


def test_corrupt_json_rejected(repo: FilesystemPortfolioRepository, tmp_path: Path):
    repo.publish(_published_manifest())
    path = tmp_path / PID_A / "published" / "v0001" / MANIFEST_FILENAME
    # Keep checksum matching by also rewriting integrity after corruption — expect parse fail
    path.write_text("{not-json", encoding="utf-8")
    integrity = tmp_path / PID_A / "published" / "v0001" / INTEGRITY_FILENAME
    payload = json.loads(integrity.read_text(encoding="utf-8"))
    payload["content_checksum"] = sha256_bytes(b"{not-json")
    integrity.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(Exception):
        repo.get_published(PID_A, 1)


def test_stored_identity_mismatch_detected(repo: FilesystemPortfolioRepository, tmp_path: Path):
    repo.publish(_published_manifest())
    path = tmp_path / PID_A / "published" / "v0001" / MANIFEST_FILENAME
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["portfolio_id"] = PID_B
    raw = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.write_bytes(raw)
    integrity = tmp_path / PID_A / "published" / "v0001" / INTEGRITY_FILENAME
    record = json.loads(integrity.read_text(encoding="utf-8"))
    record["content_checksum"] = sha256_bytes(raw)
    integrity.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(PortfolioIntegrityError):
        repo.get_published(PID_A, 1)


# --- Concurrency ---


def test_concurrent_same_version_publication_one_stable_result(
    repo: FilesystemPortfolioRepository,
):
    manifest = _published_manifest(version=1)
    errors: list[BaseException] = []
    results: list[PortfolioManifest] = []
    barrier = threading.Barrier(2)

    def worker() -> None:
        try:
            barrier.wait(timeout=5)
            results.append(repo.publish(manifest))
        except BaseException as exc:  # noqa: BLE001 — collect for assertion
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    assert not errors
    assert len(results) == 2
    assert results[0].model_dump(mode="json") == results[1].model_dump(mode="json")
    assert repo.list_versions(PID_A) == [1]


def test_different_portfolio_ids_write_independently(
    repo: FilesystemPortfolioRepository,
):
    barrier = threading.Barrier(2)
    errors: list[BaseException] = []

    def worker(pid: str) -> None:
        try:
            barrier.wait(timeout=5)
            repo.publish(_published_manifest(portfolio_id=pid, version=1))
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [
        threading.Thread(target=worker, args=(PID_A,)),
        threading.Thread(target=worker, args=(PID_B,)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    assert not errors
    assert sorted(repo.list_portfolios()) == sorted([PID_A, PID_B])


# --- Atomicity / fault injection ---


def test_publish_failure_before_replace_leaves_no_visible_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    storage = PortfolioStorage(root=tmp_path)
    repo = FilesystemPortfolioRepository(storage=storage)
    calls = {"n": 0}
    original = storage.write_bytes_atomic

    def fail_first(path: Path, payload: bytes, *, overwrite: bool = False):
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("simulated disk failure")
        return original(path, payload, overwrite=overwrite)

    monkeypatch.setattr(storage, "write_bytes_atomic", fail_first)
    with pytest.raises(OSError):
        repo.publish(_published_manifest())
    assert repo.list_portfolios(include_draft_only=False) == []
    assert not (tmp_path / PID_A / "published" / "v0001" / MANIFEST_FILENAME).is_file()


def test_draft_replace_failure_preserves_prior_draft(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    storage = PortfolioStorage(root=tmp_path)
    repo = FilesystemPortfolioRepository(storage=storage)
    repo.save_draft(_draft_manifest(version=1))
    original = storage.write_bytes_atomic

    def fail_next(path: Path, payload: bytes, *, overwrite: bool = False):
        if path.name == MANIFEST_FILENAME:
            raise OSError("simulated draft failure")
        return original(path, payload, overwrite=overwrite)

    monkeypatch.setattr(storage, "write_bytes_atomic", fail_next)
    with pytest.raises(OSError):
        repo.save_draft(_draft_manifest(version=2))
    loaded = FilesystemPortfolioRepository(storage=PortfolioStorage(root=tmp_path)).get_draft(
        PID_A
    )
    assert loaded.portfolio_version == 1


def test_orphan_temp_does_not_affect_reads(repo: FilesystemPortfolioRepository, tmp_path: Path):
    repo.publish(_published_manifest())
    orphan = tmp_path / PID_A / "published" / "v0001" / ".manifest.json.extra.tmp"
    orphan.write_text("orphan", encoding="utf-8")
    loaded = repo.get_published(PID_A, 1)
    assert loaded.portfolio_version == 1
    assert repo.list_versions(PID_A) == [1]


def test_lock_timeout_surfaces_explicitly(tmp_path: Path):
    storage = PortfolioStorage(root=tmp_path)
    storage.ensure_root()
    held = threading.Event()
    release = threading.Event()
    errors: list[BaseException] = []

    def holder() -> None:
        try:
            with storage.acquire_write_lock(PID_A, timeout_seconds=5.0):
                held.set()
                release.wait(timeout=5.0)
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    thread = threading.Thread(target=holder)
    thread.start()
    assert held.wait(timeout=5.0)
    with pytest.raises(PortfolioLockError):
        with storage.acquire_write_lock(PID_A, timeout_seconds=0.2):
            pass
    release.set()
    thread.join(timeout=5.0)
    assert not errors


# --- Paths / listing ---


def test_invalid_portfolio_id_rejected(repo: FilesystemPortfolioRepository):
    with pytest.raises(Exception):
        repo.get_draft("../evil")


def test_symlink_escape_rejected(tmp_path: Path):
    root = tmp_path / "registry"
    outside = tmp_path / "outside"
    outside.mkdir()
    root.mkdir()
    storage = PortfolioStorage(root=root)
    storage.ensure_root()
    link = root / PID_A
    link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(PortfolioStorageError):
        storage.write_bytes_atomic(link / "manifest.json", b"{}", overwrite=True)
    assert not (outside / "manifest.json").exists()


def test_list_portfolios_sorted_and_draft_only_policy(repo: FilesystemPortfolioRepository):
    assert repo.list_portfolios() == []
    repo.save_draft(_draft_manifest(PID_B))
    repo.publish(_published_manifest(PID_A))
    assert repo.list_portfolios(include_draft_only=True) == sorted([PID_A, PID_B])
    assert repo.list_portfolios(include_draft_only=False) == [PID_A]


def test_corrupt_unrelated_portfolio_does_not_erase_valid_listing(
    repo: FilesystemPortfolioRepository, tmp_path: Path
):
    repo.publish(_published_manifest(PID_A))
    bad = tmp_path / "not-a-portfolio-id"
    bad.mkdir()
    (bad / "draft").mkdir()
    assert repo.list_portfolios() == [PID_A]


def test_decimal_and_timestamp_serialization_stable(repo: FilesystemPortfolioRepository):
    manifest = _published_manifest(weight_a=Decimal("0.25"), weight_b=Decimal("0.75"))
    first = serialize_portfolio_manifest(manifest)
    second = serialize_portfolio_manifest(manifest)
    assert first == second
    assert b'"0.25"' in first
    repo.publish(manifest)
    loaded = repo.get_published(PID_A, 1)
    assert loaded.members[0].analytical_weight is not None
    assert loaded.members[0].analytical_weight.value == Decimal("0.25")
    assert loaded.published_at is not None
    assert loaded.published_at.tzinfo is not None


def test_get_draft_missing(repo: FilesystemPortfolioRepository):
    with pytest.raises(PortfolioDraftNotFoundError):
        repo.get_draft(PID_A)


def test_get_published_missing(repo: FilesystemPortfolioRepository):
    with pytest.raises(PortfolioVersionNotFoundError):
        repo.get_published(PID_A, 1)
