"""Optional research-lifecycle persistence — repository access only.

Application services own transaction boundaries and idempotency.
Never invent successful writes when the database is unavailable.
"""

from __future__ import annotations

from typing import Any, Optional

from app.db.client import get_db_connection, is_database_configured
from app.db.repositories.backtest_runs import DatabaseUnavailableError


def require_database() -> None:
    if not is_database_configured():
        raise DatabaseUnavailableError("Database is not configured.")


def upsert_research_project(row: dict[str, Any]) -> dict[str, Any]:
    require_database()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into research_projects (
                  id, research_type, name, question, hypothesis, null_hypothesis,
                  mechanism, benchmark, status, created_at, updated_at
                ) values (
                  %(id)s, %(research_type)s, %(name)s, %(question)s, %(hypothesis)s,
                  %(null_hypothesis)s, %(mechanism)s, %(benchmark)s, %(status)s,
                  coalesce(%(created_at)s, now()), now()
                )
                on conflict (id) do update set
                  research_type = excluded.research_type,
                  name = excluded.name,
                  question = excluded.question,
                  hypothesis = excluded.hypothesis,
                  null_hypothesis = excluded.null_hypothesis,
                  mechanism = excluded.mechanism,
                  benchmark = excluded.benchmark,
                  status = excluded.status,
                  updated_at = now()
                returning id, research_type, name, question, status, updated_at
                """,
                row,
            )
            saved = cur.fetchone()
            conn.commit()
    return {
        "id": saved[0],
        "research_type": saved[1],
        "name": saved[2],
        "question": saved[3],
        "status": saved[4],
        "updated_at": saved[5].isoformat() if saved[5] else None,
    }


def get_research_project(research_id: str) -> Optional[dict[str, Any]]:
    require_database()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select id, research_type, name, question, hypothesis, null_hypothesis,
                       mechanism, benchmark, status, created_at, updated_at
                from research_projects
                where id = %s
                """,
                (research_id,),
            )
            row = cur.fetchone()
    if row is None:
        return None
    return {
        "id": row[0],
        "research_type": row[1],
        "name": row[2],
        "question": row[3],
        "hypothesis": row[4],
        "null_hypothesis": row[5],
        "mechanism": row[6],
        "benchmark": row[7],
        "status": row[8],
        "created_at": row[9].isoformat() if row[9] else None,
        "updated_at": row[10].isoformat() if row[10] else None,
    }


def insert_protocol_version(
    *,
    research_id: str,
    version: int,
    parameters: dict[str, Any],
    success_criteria: list[Any],
    limitations: list[Any],
    protocol_hash: str,
) -> dict[str, Any]:
    require_database()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into research_protocol_versions (
                  research_id, version, parameters, success_criteria, limitations, protocol_hash
                ) values (%s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s)
                returning id, research_id, version, protocol_hash, created_at
                """,
                (
                    research_id,
                    version,
                    _json(parameters),
                    _json(success_criteria),
                    _json(limitations),
                    protocol_hash,
                ),
            )
            saved = cur.fetchone()
            conn.commit()
    return {
        "id": str(saved[0]),
        "research_id": saved[1],
        "version": saved[2],
        "protocol_hash": saved[3],
        "created_at": saved[4].isoformat() if saved[4] else None,
    }


def get_protocol_version(research_id: str, version: int) -> Optional[dict[str, Any]]:
    require_database()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select id, research_id, version, parameters, success_criteria, limitations,
                       protocol_hash, created_at
                from research_protocol_versions
                where research_id = %s and version = %s
                """,
                (research_id, version),
            )
            row = cur.fetchone()
    if row is None:
        return None
    return {
        "id": str(row[0]),
        "research_id": row[1],
        "version": row[2],
        "parameters": row[3],
        "success_criteria": row[4],
        "limitations": row[5],
        "protocol_hash": row[6],
        "created_at": row[7].isoformat() if row[7] else None,
    }


def insert_evidence_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    require_database()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into evidence_snapshots (
                  id, research_id, schema_version, evidence, evidence_hash, reproducibility_manifest
                ) values (
                  %(id)s, %(research_id)s, %(schema_version)s, %(evidence)s::jsonb,
                  %(evidence_hash)s, %(reproducibility_manifest)s::jsonb
                )
                on conflict (id) do nothing
                returning id, evidence_hash, created_at
                """,
                {
                    **row,
                    "evidence": _json(row["evidence"]),
                    "reproducibility_manifest": _json(
                        row.get("reproducibility_manifest") or {}
                    ),
                },
            )
            saved = cur.fetchone()
            replay = False
            if saved is None:
                cur.execute(
                    "select id, evidence_hash, created_at from evidence_snapshots where id = %s",
                    (row["id"],),
                )
                saved = cur.fetchone()
                replay = True
            conn.commit()
    return {
        "id": saved[0],
        "evidence_hash": saved[1],
        "created_at": saved[2].isoformat() if saved[2] else None,
        "idempotent_replay": replay,
    }


def get_evidence_snapshot(snapshot_id: str) -> Optional[dict[str, Any]]:
    require_database()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select id, research_id, schema_version, evidence, evidence_hash,
                       reproducibility_manifest, created_at
                from evidence_snapshots
                where id = %s
                """,
                (snapshot_id,),
            )
            row = cur.fetchone()
    if row is None:
        return None
    return {
        "id": row[0],
        "research_id": row[1],
        "schema_version": row[2],
        "evidence": row[3],
        "evidence_hash": row[4],
        "reproducibility_manifest": row[5],
        "created_at": row[6].isoformat() if row[6] else None,
    }


def insert_validation_run(row: dict[str, Any]) -> dict[str, Any]:
    """Insert a validation run; honor idempotency_key when present."""
    require_database()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            idem = row.get("idempotency_key")
            if idem:
                cur.execute(
                    """
                    select id, research_id, status, evidence_snapshot_id, created_at, completed_at
                    from validation_runs
                    where research_id = %s and idempotency_key = %s
                    """,
                    (row["research_id"], idem),
                )
                existing = cur.fetchone()
                if existing is not None:
                    conn.commit()
                    return {
                        "id": existing[0],
                        "research_id": existing[1],
                        "status": existing[2],
                        "evidence_snapshot_id": existing[3],
                        "created_at": existing[4].isoformat() if existing[4] else None,
                        "completed_at": existing[5].isoformat() if existing[5] else None,
                        "idempotent_replay": True,
                    }
            cur.execute(
                """
                insert into validation_runs (
                  id, research_id, protocol_version_id, status, evidence_snapshot_id,
                  reproducibility_manifest, idempotency_key, created_at, completed_at
                ) values (
                  %(id)s, %(research_id)s, %(protocol_version_id)s, %(status)s,
                  %(evidence_snapshot_id)s, %(reproducibility_manifest)s::jsonb,
                  %(idempotency_key)s, coalesce(%(created_at)s, now()), %(completed_at)s
                )
                returning id, research_id, status, evidence_snapshot_id, created_at, completed_at
                """,
                {
                    **row,
                    "reproducibility_manifest": _json(
                        row.get("reproducibility_manifest") or {}
                    ),
                },
            )
            saved = cur.fetchone()
            conn.commit()
    return {
        "id": saved[0],
        "research_id": saved[1],
        "status": saved[2],
        "evidence_snapshot_id": saved[3],
        "created_at": saved[4].isoformat() if saved[4] else None,
        "completed_at": saved[5].isoformat() if saved[5] else None,
        "idempotent_replay": False,
    }


def insert_agent_run(row: dict[str, Any]) -> dict[str, Any]:
    require_database()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into agent_runs (
                  id, research_id, validation_run_id, status, rulebook_version,
                  llm_used, llm_provider, llm_model, deterministic_suggestion,
                  created_at, completed_at
                ) values (
                  %(id)s, %(research_id)s, %(validation_run_id)s, %(status)s,
                  %(rulebook_version)s, %(llm_used)s, %(llm_provider)s, %(llm_model)s,
                  %(deterministic_suggestion)s, coalesce(%(created_at)s, now()),
                  %(completed_at)s
                )
                on conflict (id) do nothing
                returning id, research_id, status, llm_used, deterministic_suggestion, created_at
                """,
                row,
            )
            saved = cur.fetchone()
            if saved is None:
                cur.execute(
                    """
                    select id, research_id, status, llm_used, deterministic_suggestion, created_at
                    from agent_runs where id = %s
                    """,
                    (row["id"],),
                )
                saved = cur.fetchone()
            conn.commit()
    return {
        "id": saved[0],
        "research_id": saved[1],
        "status": saved[2],
        "llm_used": saved[3],
        "deterministic_suggestion": saved[4],
        "created_at": saved[5].isoformat() if saved[5] else None,
    }


def insert_agent_run_events(agent_run_id: str, events: list[dict[str, Any]]) -> int:
    require_database()
    if not events:
        return 0
    inserted = 0
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            for event in events:
                cur.execute(
                    """
                    insert into agent_run_events (
                      agent_run_id, sequence, authority, node, status, summary,
                      evidence_ids, methodology_citations
                    ) values (
                      %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb
                    )
                    on conflict (agent_run_id, sequence) do nothing
                    """,
                    (
                        agent_run_id,
                        int(event["sequence"]),
                        str(event.get("authority") or "system"),
                        str(event.get("node") or "unknown"),
                        str(event.get("status") or "completed"),
                        str(event.get("summary") or "")[:500],
                        _json(event.get("evidence_ids") or []),
                        _json(event.get("methodology_citations") or []),
                    ),
                )
                inserted += cur.rowcount
            conn.commit()
    return inserted


def list_agent_run_events(agent_run_id: str) -> list[dict[str, Any]]:
    require_database()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select sequence, authority, node, status, summary,
                       evidence_ids, methodology_citations, created_at
                from agent_run_events
                where agent_run_id = %s
                order by sequence asc
                """,
                (agent_run_id,),
            )
            rows = cur.fetchall()
    return [
        {
            "sequence": row[0],
            "authority": row[1],
            "node": row[2],
            "status": row[3],
            "summary": row[4],
            "evidence_ids": row[5] or [],
            "methodology_citations": row[6] or [],
            "created_at": row[7].isoformat() if row[7] else None,
        }
        for row in rows
    ]


def insert_decision_record(row: dict[str, Any]) -> dict[str, Any]:
    require_database()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into decision_records (
                  research_id, evidence_snapshot_id, agent_run_id,
                  suggested_outcome, human_outcome, override_reason, rationale
                ) values (
                  %(research_id)s, %(evidence_snapshot_id)s, %(agent_run_id)s,
                  %(suggested_outcome)s, %(human_outcome)s, %(override_reason)s, %(rationale)s
                )
                returning id, research_id, human_outcome, created_at
                """,
                row,
            )
            saved = cur.fetchone()
            conn.commit()
    return {
        "id": str(saved[0]),
        "research_id": saved[1],
        "human_outcome": saved[2],
        "created_at": saved[3].isoformat() if saved[3] else None,
    }


def list_decision_records(research_id: str, *, limit: int = 20) -> list[dict[str, Any]]:
    require_database()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select id, research_id, evidence_snapshot_id, agent_run_id,
                       suggested_outcome, human_outcome, override_reason, rationale, created_at
                from decision_records
                where research_id = %s
                order by created_at desc
                limit %s
                """,
                (research_id, max(1, min(limit, 100))),
            )
            rows = cur.fetchall()
    return [
        {
            "id": str(row[0]),
            "research_id": row[1],
            "evidence_snapshot_id": row[2],
            "agent_run_id": row[3],
            "suggested_outcome": row[4],
            "human_outcome": row[5],
            "override_reason": row[6],
            "rationale": row[7],
            "created_at": row[8].isoformat() if row[8] else None,
        }
        for row in rows
    ]


def persistence_mode() -> str:
    """Product-facing mode label for UI — never exposes connection details."""
    if not is_database_configured():
        return "browser-local"
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("select 1")
                cur.fetchone()
        return "persisted"
    except Exception:
        return "persistence-unavailable"


def _json(value: Any) -> str:
    import json

    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
