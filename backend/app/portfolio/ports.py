"""Published Research query port for Portfolio publication (Phase 5.1C)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Protocol, Sequence

from pydantic import BaseModel, ConfigDict, Field


class PublishedSnapshotReference(BaseModel):
    """Portfolio-side projection of a published research snapshot reference."""

    model_config = ConfigDict(extra="forbid")

    snapshot_id: str
    name: str
    snapshot_type: str
    schema_version: str
    checksum_algorithm: str
    checksum: str
    size_bytes: int
    created_at: datetime
    integrity_verified: bool = False


class PublishedRunReference(BaseModel):
    """Portfolio-side provenance projection of a Published Research Run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    publication_status: str
    validation_ok: bool
    published_at: Optional[datetime] = None
    strategy_or_research_name: Optional[str] = None
    snapshot_references: list[PublishedSnapshotReference] = Field(default_factory=list)
    source_integrity_status: str = "ok"
    methodology_version: Optional[str] = None
    universe: Optional[str] = None
    notes: Optional[str] = None


class PublishedResearchQueryPort(Protocol):
    """Narrow read port over Phase 4 Published Research evidence."""

    def get_published_run(self, run_id: str) -> PublishedRunReference:
        """Return a published run reference or raise a typed resolution error."""

    def list_snapshot_references(
        self,
        run_id: str,
    ) -> Sequence[PublishedSnapshotReference]:
        """Return snapshot references for a published run."""

    def verify_snapshot(
        self,
        run_id: str,
        snapshot_id: str,
    ) -> PublishedSnapshotReference:
        """Verify snapshot ownership/integrity and return the reference."""
