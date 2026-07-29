"""FastAPI dependency construction for intelligence serving."""

from __future__ import annotations

from functools import lru_cache

from app.intelligence.artifact_registry import ResearchArtifactRegistry
from app.intelligence.run_registry import ResearchRunRegistry
from app.intelligence.snapshot_registry import ResearchSnapshotRegistry
from app.intelligence.storage import IntelligenceStorage
from app.intelligence_serving.service import IntelligenceService


@lru_cache(maxsize=1)
def get_intelligence_service() -> IntelligenceService:
    """Construct registries against the shared IntelligenceStorage root.

    Uses ``INTELLIGENCE_OUTPUT_DIR`` / default ``backend/outputs`` via
    ``IntelligenceStorage()`` — same root as publishing.
    """
    storage = IntelligenceStorage()
    run_registry = ResearchRunRegistry(storage=storage)
    artifact_registry = ResearchArtifactRegistry(run_registry)
    snapshot_registry = ResearchSnapshotRegistry(
        run_registry,
        artifact_registry=artifact_registry,
    )
    return IntelligenceService(run_registry, artifact_registry, snapshot_registry)


def build_intelligence_service(storage: IntelligenceStorage) -> IntelligenceService:
    """Test/helper factory that binds a specific storage root (uncached)."""
    run_registry = ResearchRunRegistry(storage=storage)
    artifact_registry = ResearchArtifactRegistry(run_registry)
    snapshot_registry = ResearchSnapshotRegistry(
        run_registry,
        artifact_registry=artifact_registry,
    )
    return IntelligenceService(run_registry, artifact_registry, snapshot_registry)
