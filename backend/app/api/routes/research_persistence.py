"""Optional research-lifecycle persistence API.

Frontend never talks to Supabase directly. When the database is unavailable,
these endpoints return 503 with safe messages — they do not invent success.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from app.db.repositories.backtest_runs import DatabaseUnavailableError
from app.db.repositories.research_lifecycle import (
    get_evidence_snapshot,
    get_research_project,
    list_agent_run_events,
    persistence_mode,
)
from app.services.research_lifecycle_service import (
    ResearchLifecycleService,
    map_database_error,
)

router = APIRouter(prefix="/api/v1/research/persistence", tags=["research-persistence"])
_service = ResearchLifecycleService()


class ProjectUpsertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=128)
    research_type: str = "trend_following"
    name: str = Field(min_length=1, max_length=256)
    question: str = Field(min_length=1, max_length=4000)
    hypothesis: Optional[str] = Field(default=None, max_length=4000)
    null_hypothesis: Optional[str] = Field(default=None, max_length=4000)
    mechanism: Optional[str] = Field(default=None, max_length=4000)
    benchmark: Optional[str] = Field(default=None, max_length=256)
    status: str = "draft"


class ProtocolVersionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_id: str = Field(min_length=1, max_length=128)
    version: int = Field(ge=1, le=10_000)
    parameters: dict[str, Any] = Field(default_factory=dict)
    success_criteria: list[Any] = Field(default_factory=list)
    limitations: list[Any] = Field(default_factory=list)
    protocol_hash: Optional[str] = Field(default=None, max_length=128)


class EvidenceSnapshotRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Optional[str] = Field(default=None, max_length=128)
    research_id: str = Field(min_length=1, max_length=128)
    schema_version: str = "1"
    evidence: dict[str, Any]
    evidence_hash: Optional[str] = Field(default=None, max_length=128)
    reproducibility_manifest: dict[str, Any] = Field(default_factory=dict)


class ValidationRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Optional[str] = Field(default=None, max_length=128)
    research_id: str = Field(min_length=1, max_length=128)
    protocol_version_id: Optional[str] = None
    status: str = "completed"
    evidence_snapshot_id: Optional[str] = None
    reproducibility_manifest: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: Optional[str] = Field(default=None, max_length=256)


class AgentRunPersistRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=128)
    research_id: str = Field(min_length=1, max_length=128)
    validation_run_id: Optional[str] = None
    status: str = "completed"
    rulebook_version: Optional[str] = None
    llm_used: bool = False
    llm_provider: Optional[str] = Field(default=None, max_length=64)
    llm_model: Optional[str] = Field(default=None, max_length=128)
    deterministic_suggestion: Optional[str] = Field(default=None, max_length=64)
    events: list[dict[str, Any]] = Field(default_factory=list)
    completed_at: Optional[str] = None


class DecisionRecordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_id: str = Field(min_length=1, max_length=128)
    evidence_snapshot_id: Optional[str] = None
    agent_run_id: Optional[str] = None
    suggested_outcome: Optional[str] = Field(default=None, max_length=64)
    human_outcome: str = Field(min_length=1, max_length=64)
    override_reason: Optional[str] = Field(default=None, max_length=2000)
    rationale: str = Field(min_length=1, max_length=4000)


def _handle(exc: Exception) -> HTTPException:
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail=str(exc))
    status, detail = map_database_error(exc)
    return HTTPException(status_code=status, detail=detail)


@router.get("/mode")
def get_persistence_mode() -> dict[str, str]:
    return {"persistence_mode": persistence_mode()}


@router.put("/projects")
def upsert_project(body: ProjectUpsertRequest) -> dict[str, Any]:
    try:
        return _service.upsert_project(body.model_dump())
    except Exception as exc:  # noqa: BLE001 — mapped to safe HTTP
        raise _handle(exc) from exc


@router.get("/projects/{research_id}")
def read_project(research_id: str) -> dict[str, Any]:
    try:
        row = get_research_project(research_id)
    except DatabaseUnavailableError as exc:
        raise _handle(exc) from exc
    if row is None:
        raise HTTPException(status_code=404, detail="Research project not found.")
    return row


@router.post("/protocol-versions")
def publish_protocol(body: ProtocolVersionRequest) -> dict[str, Any]:
    try:
        return _service.publish_protocol_version(body.model_dump())
    except Exception as exc:  # noqa: BLE001
        raise _handle(exc) from exc


@router.post("/evidence-snapshots")
def save_snapshot(body: EvidenceSnapshotRequest) -> dict[str, Any]:
    try:
        return _service.save_evidence_snapshot(body.model_dump())
    except Exception as exc:  # noqa: BLE001
        raise _handle(exc) from exc


@router.get("/evidence-snapshots/{snapshot_id}")
def read_snapshot(snapshot_id: str) -> dict[str, Any]:
    try:
        row = get_evidence_snapshot(snapshot_id)
    except DatabaseUnavailableError as exc:
        raise _handle(exc) from exc
    if row is None:
        raise HTTPException(status_code=404, detail="Evidence snapshot not found.")
    return row


@router.post("/validation-runs")
def save_validation_run(body: ValidationRunRequest) -> dict[str, Any]:
    try:
        return _service.save_validation_run(body.model_dump())
    except Exception as exc:  # noqa: BLE001
        raise _handle(exc) from exc


@router.post("/agent-runs")
def save_agent_run(body: AgentRunPersistRequest) -> dict[str, Any]:
    try:
        return _service.save_agent_run(body.model_dump())
    except Exception as exc:  # noqa: BLE001
        raise _handle(exc) from exc


@router.get("/agent-runs/{agent_run_id}/events")
def read_agent_events(agent_run_id: str) -> dict[str, Any]:
    try:
        events = list_agent_run_events(agent_run_id)
    except DatabaseUnavailableError as exc:
        raise _handle(exc) from exc
    return {"agent_run_id": agent_run_id, "events": events}


@router.post("/decision-records")
def save_decision(body: DecisionRecordRequest) -> dict[str, Any]:
    try:
        return _service.save_decision(body.model_dump())
    except Exception as exc:  # noqa: BLE001
        raise _handle(exc) from exc


@router.get("/decision-records")
def list_decisions(
    research_id: str = Query(min_length=1, max_length=128),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    try:
        items = _service.list_decisions(research_id, limit=limit)
    except Exception as exc:  # noqa: BLE001
        raise _handle(exc) from exc
    return {"research_id": research_id, "items": items}
