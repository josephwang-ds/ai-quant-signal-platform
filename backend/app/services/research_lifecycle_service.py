"""Application service for optional research-lifecycle persistence."""

from __future__ import annotations

import uuid
from typing import Any

from app.db.repositories import research_lifecycle as repo
from app.db.repositories.backtest_runs import DatabaseUnavailableError
from app.research_execution.market_data_port import utc_now_iso
from app.research_reproducibility.manifest import hash_protocol


class ResearchLifecycleService:
    """Coordinates optional durable writes. Never fabricates success offline."""

    def upsert_project(self, payload: dict[str, Any]) -> dict[str, Any]:
        research_id = str(payload.get("id") or "").strip()
        if not research_id:
            raise ValueError("id is required")
        return repo.upsert_research_project(
            {
                "id": research_id,
                "research_type": payload.get("research_type") or "trend_following",
                "name": payload.get("name") or research_id,
                "question": payload.get("question") or "",
                "hypothesis": payload.get("hypothesis"),
                "null_hypothesis": payload.get("null_hypothesis"),
                "mechanism": payload.get("mechanism"),
                "benchmark": payload.get("benchmark"),
                "status": payload.get("status") or "draft",
                "created_at": payload.get("created_at"),
            }
        )

    def publish_protocol_version(self, payload: dict[str, Any]) -> dict[str, Any]:
        research_id = str(payload.get("research_id") or "").strip()
        version = int(payload.get("version") or 0)
        if not research_id or version < 1:
            raise ValueError("research_id and version (>=1) are required")
        parameters = payload.get("parameters") or {}
        if not isinstance(parameters, dict):
            raise ValueError("parameters must be an object")
        existing = repo.get_protocol_version(research_id, version)
        if existing is not None:
            # Protocol versions are immutable once published.
            return {**existing, "immutable": True, "idempotent_replay": True}
        protocol_hash = payload.get("protocol_hash") or hash_protocol(parameters)
        return {
            **repo.insert_protocol_version(
                research_id=research_id,
                version=version,
                parameters=parameters,
                success_criteria=list(payload.get("success_criteria") or []),
                limitations=list(payload.get("limitations") or []),
                protocol_hash=str(protocol_hash),
            ),
            "immutable": True,
            "idempotent_replay": False,
        }

    def save_evidence_snapshot(self, payload: dict[str, Any]) -> dict[str, Any]:
        snapshot_id = str(payload.get("id") or f"snap-{uuid.uuid4().hex[:16]}")
        research_id = str(payload.get("research_id") or "").strip()
        if not research_id:
            raise ValueError("research_id is required")
        evidence = payload.get("evidence")
        if not isinstance(evidence, dict):
            raise ValueError("evidence must be an object")
        evidence_hash = str(
            payload.get("evidence_hash") or hash_protocol(evidence)
        )
        return repo.insert_evidence_snapshot(
            {
                "id": snapshot_id,
                "research_id": research_id,
                "schema_version": str(payload.get("schema_version") or "1"),
                "evidence": evidence,
                "evidence_hash": evidence_hash,
                "reproducibility_manifest": payload.get("reproducibility_manifest")
                or {},
            }
        )

    def save_validation_run(self, payload: dict[str, Any]) -> dict[str, Any]:
        research_id = str(payload.get("research_id") or "").strip()
        if not research_id:
            raise ValueError("research_id is required")
        run_id = str(payload.get("id") or f"val-{uuid.uuid4().hex[:16]}")
        return repo.insert_validation_run(
            {
                "id": run_id,
                "research_id": research_id,
                "protocol_version_id": payload.get("protocol_version_id"),
                "status": payload.get("status") or "completed",
                "evidence_snapshot_id": payload.get("evidence_snapshot_id"),
                "reproducibility_manifest": payload.get("reproducibility_manifest")
                or {},
                "idempotency_key": payload.get("idempotency_key"),
                "created_at": payload.get("created_at"),
                "completed_at": payload.get("completed_at") or utc_now_iso(),
            }
        )

    def save_agent_run(self, payload: dict[str, Any]) -> dict[str, Any]:
        research_id = str(payload.get("research_id") or "").strip()
        agent_run_id = str(payload.get("id") or "").strip()
        if not research_id or not agent_run_id:
            raise ValueError("id and research_id are required")
        saved = repo.insert_agent_run(
            {
                "id": agent_run_id,
                "research_id": research_id,
                "validation_run_id": payload.get("validation_run_id"),
                "status": payload.get("status") or "completed",
                "rulebook_version": payload.get("rulebook_version"),
                "llm_used": bool(payload.get("llm_used")),
                "llm_provider": payload.get("llm_provider"),
                "llm_model": payload.get("llm_model"),
                "deterministic_suggestion": payload.get("deterministic_suggestion"),
                "created_at": payload.get("created_at"),
                "completed_at": payload.get("completed_at"),
            }
        )
        events = payload.get("events") or []
        if isinstance(events, list) and events:
            repo.insert_agent_run_events(agent_run_id, events)
        saved["events"] = repo.list_agent_run_events(agent_run_id)
        return saved

    def save_decision(self, payload: dict[str, Any]) -> dict[str, Any]:
        research_id = str(payload.get("research_id") or "").strip()
        human_outcome = str(payload.get("human_outcome") or "").strip()
        rationale = str(payload.get("rationale") or "").strip()
        if not research_id or not human_outcome or not rationale:
            raise ValueError("research_id, human_outcome, and rationale are required")
        if len(rationale) > 4000:
            raise ValueError("rationale exceeds maximum length")
        return repo.insert_decision_record(
            {
                "research_id": research_id,
                "evidence_snapshot_id": payload.get("evidence_snapshot_id"),
                "agent_run_id": payload.get("agent_run_id"),
                "suggested_outcome": payload.get("suggested_outcome"),
                "human_outcome": human_outcome,
                "override_reason": payload.get("override_reason"),
                "rationale": rationale,
            }
        )

    def list_decisions(self, research_id: str, *, limit: int = 20) -> list[dict[str, Any]]:
        return repo.list_decision_records(research_id, limit=limit)


def map_database_error(exc: Exception) -> tuple[int, str]:
    """Safe HTTP mapping — never leak connection strings or driver traces."""
    if isinstance(exc, DatabaseUnavailableError):
        return 503, "Persistent storage is unavailable in this deployment."
    message = str(exc)
    lowered = message.lower()
    if "supabase_db_url" in lowered or "postgres://" in lowered or "postgresql://" in lowered:
        return 503, "Persistent storage is unavailable in this deployment."
    if "not configured" in lowered:
        return 503, "Persistent storage is not enabled in this deployment."
    return 503, "Persistent storage is temporarily unavailable."
