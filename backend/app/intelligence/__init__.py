"""Research run, artifact, and snapshot registries for intelligence publishing.

Phase 4.1 — typed run metadata, filesystem persistence, immutable manifests.
Phase 4.2 — append-only checksummed research artifacts under each run.
Phase 4.3 — consumer snapshot contracts + append-only snapshot registration.
Phase 4.3.1 — run-level locking, publish recovery, create-run cleanup.
Phase 4.4 — deterministic artifact-to-snapshot builders.
"""

from app.intelligence.artifact_registry import ResearchArtifactRegistry, serialize_artifact_json
from app.intelligence.errors import (
    ArtifactAlreadyExistsError,
    ArtifactIntegrityError,
    ArtifactNotFoundError,
    IntelligenceStorageError,
    InvalidArtifactError,
    InvalidRunTransitionError,
    InvalidSnapshotError,
    ManifestValidationError,
    RunAlreadyExistsError,
    RunNotFoundError,
    SnapshotAlreadyExistsError,
    SnapshotArtifactPayloadError,
    SnapshotBuildError,
    SnapshotEvidenceError,
    SnapshotIntegrityError,
    SnapshotNotFoundError,
    SnapshotSourceError,
    UnsupportedArtifactContractError,
)
from app.intelligence.run_registry import ResearchRunRegistry
from app.intelligence.schemas import (
    ArtifactReference,
    ArtifactVerificationResult,
    LatestRunPointer,
    ResearchArtifactReference,
    ResearchArtifactType,
    ResearchRunManifest,
    ResearchRunMetadata,
    ResearchRunStatus,
    ResearchRunType,
    ResearchSnapshotReference,
    ResearchSnapshotType,
    SnapshotVerificationResult,
    generate_artifact_id,
    generate_run_id,
    generate_snapshot_id,
)
from app.intelligence.snapshot_builders import (
    RESEARCH_SUMMARY_EVIDENCE_VERSION,
    SIGNAL_EVIDENCE_VERSION,
    ResearchSummarySnapshotBuilder,
    SignalSnapshotBuilder,
)
from app.intelligence.snapshot_contracts import (
    ArtifactSummaryItem,
    ResearchSummarySnapshot,
    SignalDirection,
    SignalRecord,
    SignalSnapshot,
    SnapshotFinding,
    SnapshotLimitation,
    ValidationStatus,
)
from app.intelligence.snapshot_registry import (
    ResearchSnapshotRegistry,
    build_research_summary_snapshot,
    build_signal_snapshot,
)
from app.intelligence.storage import IntelligenceStorage, calculate_sha256

__all__ = [
    "ArtifactAlreadyExistsError",
    "ArtifactIntegrityError",
    "ArtifactNotFoundError",
    "ArtifactReference",
    "ArtifactSummaryItem",
    "ArtifactVerificationResult",
    "IntelligenceStorage",
    "IntelligenceStorageError",
    "InvalidArtifactError",
    "InvalidRunTransitionError",
    "InvalidSnapshotError",
    "LatestRunPointer",
    "ManifestValidationError",
    "RESEARCH_SUMMARY_EVIDENCE_VERSION",
    "ResearchArtifactReference",
    "ResearchArtifactRegistry",
    "ResearchArtifactType",
    "ResearchRunManifest",
    "ResearchRunMetadata",
    "ResearchRunRegistry",
    "ResearchRunStatus",
    "ResearchRunType",
    "ResearchSnapshotReference",
    "ResearchSnapshotRegistry",
    "ResearchSnapshotType",
    "ResearchSummarySnapshot",
    "ResearchSummarySnapshotBuilder",
    "RunAlreadyExistsError",
    "RunNotFoundError",
    "SIGNAL_EVIDENCE_VERSION",
    "SignalDirection",
    "SignalRecord",
    "SignalSnapshot",
    "SignalSnapshotBuilder",
    "SnapshotAlreadyExistsError",
    "SnapshotArtifactPayloadError",
    "SnapshotBuildError",
    "SnapshotEvidenceError",
    "SnapshotFinding",
    "SnapshotIntegrityError",
    "SnapshotLimitation",
    "SnapshotNotFoundError",
    "SnapshotSourceError",
    "SnapshotVerificationResult",
    "UnsupportedArtifactContractError",
    "ValidationStatus",
    "build_research_summary_snapshot",
    "build_signal_snapshot",
    "calculate_sha256",
    "generate_artifact_id",
    "generate_run_id",
    "generate_snapshot_id",
    "serialize_artifact_json",
]
