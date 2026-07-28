"""Domain exceptions for the intelligence publishing layer."""

from __future__ import annotations


class IntelligenceStorageError(Exception):
    """Filesystem or configuration failure in intelligence storage."""


class RunNotFoundError(IntelligenceStorageError):
    """Requested research run does not exist."""


class RunAlreadyExistsError(IntelligenceStorageError):
    """A run directory or manifest already exists for the given run_id."""


class InvalidRunTransitionError(ValueError):
    """Status transition is not allowed by the research-run lifecycle."""


class ManifestValidationError(ValueError):
    """Research run manifest failed consistency validation."""


class ArtifactNotFoundError(IntelligenceStorageError):
    """Requested research artifact is not registered."""


class ArtifactAlreadyExistsError(IntelligenceStorageError):
    """Artifact name, id, or destination file already exists for the run."""


class ArtifactIntegrityError(IntelligenceStorageError):
    """Registered artifact bytes do not match recorded checksum or size."""


class InvalidArtifactError(ValueError):
    """Artifact payload, path, or metadata is invalid for registration."""


class SnapshotNotFoundError(IntelligenceStorageError):
    """Requested intelligence snapshot is not registered."""


class SnapshotAlreadyExistsError(IntelligenceStorageError):
    """Snapshot name, id, or destination file already exists for the run."""


class SnapshotIntegrityError(IntelligenceStorageError):
    """Registered snapshot bytes do not match recorded checksum or size."""


class InvalidSnapshotError(ValueError):
    """Snapshot payload, provenance, or metadata is invalid."""


class SnapshotSourceError(InvalidSnapshotError):
    """Source artifact references are missing, cross-run, or failed verification."""


class SnapshotBuildError(InvalidSnapshotError):
    """Deterministic snapshot builder failed to map registered evidence."""


class UnsupportedArtifactContractError(SnapshotBuildError):
    """Registered artifact payload is not a supported builder contract."""


class SnapshotArtifactPayloadError(SnapshotBuildError):
    """Registered artifact payload is malformed for the supported contract."""


class SnapshotEvidenceError(SnapshotBuildError):
    """Builder evidence/provenance rules were violated."""
