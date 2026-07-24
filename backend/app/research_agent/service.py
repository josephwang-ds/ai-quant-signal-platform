"""Governance Agent application service — LangGraph orchestration over deterministic tools."""

from __future__ import annotations

import uuid
from typing import Any

from langgraph.checkpoint.memory import MemorySaver

from app.research_agent import GRAPH_VERSION, GraphStepLimitError, MAX_GRAPH_STEPS
from app.research_agent.graph import build_governance_graph
from app.research_agent.prompts import PROMPT_VERSIONS
from app.research_agent.run_store import InMemoryAgentRunStore, get_default_agent_run_store
from app.research_agent.tools.handlers import ToolExecutionContext
from app.research_copilot.llm_config import LlmConfigurationError, resolve_llm_provider_settings
from app.research_copilot.service import resolve_llm_adapter
from app.research_execution.market_data_port import utc_now_iso
from app.research_execution.service import RESEARCH_ID_PATTERN
from app.research_validation.result_store import ValidationResultStore


class ResearchAgentError(Exception):
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class GovernanceAgentService:
    """Controlled research-governance workflow. Does not calculate financial metrics."""

    def __init__(
        self,
        store: ValidationResultStore,
        *,
        llm: Any | None = None,
        llm_available: bool | None = None,
        llm_provider: str | None = None,
        llm_model: str | None = None,
        validation_service: Any | None = None,
        factor_validation_service: Any | None = None,
        execution_service: Any | None = None,
        run_store: InMemoryAgentRunStore | None = None,
        checkpointer: MemorySaver | None = None,
        decision_log: dict[str, list[dict[str, Any]]] | None = None,
    ) -> None:
        self.store = store
        self.run_store = run_store or get_default_agent_run_store()
        self.checkpointer = checkpointer or MemorySaver()
        self.decision_log = decision_log if decision_log is not None else {}
        self.tool_ctx = ToolExecutionContext(
            store=store,
            validation_service=validation_service,
            factor_validation_service=factor_validation_service,
            execution_service=execution_service,
            decision_log=self.decision_log,
        )

        if llm is not None:
            self.llm = llm
            self.llm_available = True if llm_available is None else llm_available
            self.llm_provider = llm_provider or "injected"
            self.llm_model = llm_model or getattr(llm, "model", "injected")
        else:
            try:
                settings = resolve_llm_provider_settings()
                self.llm = resolve_llm_adapter()
                self.llm_available = True
                self.llm_provider = settings.provider
                self.llm_model = settings.model
            except (LlmConfigurationError, Exception):
                self.llm = None
                self.llm_available = False
                self.llm_provider = None
                self.llm_model = None

        self.graph = build_governance_graph(
            llm=self.llm if self.llm_available else None,
            tool_ctx=self.tool_ctx,
            store=store,
            checkpointer=self.checkpointer,
        )

    def create_run(self, request: dict[str, Any]) -> dict[str, Any]:
        research_id = str(request.get("research_id") or "").strip()
        if not RESEARCH_ID_PATTERN.fullmatch(research_id):
            raise ResearchAgentError(
                "research_id must contain 1-128 letters, numbers, dots, underscores, or hyphens."
            )
        intent = request.get("intent")
        if intent not in {
            "review_definition",
            "review_readiness",
            "review_evidence",
            "prepare_decision",
        }:
            raise ResearchAgentError("intent is unsupported.")

        agent_run_id = f"agent-{uuid.uuid4().hex[:16]}"
        started_at = utc_now_iso()
        initial = {
            "agent_run_id": agent_run_id,
            "research_id": research_id,
            "research_type": request.get("research_type") or "trend_following",
            "intent": intent,
            "current_node": "classify_intent",
            "status": "running",
            "research_definition": request.get("research_definition") or {},
            "definition_review": {},
            "knowledge_context": [],
            "requested_tools": [],
            "tool_results": [],
            "evidence_snapshot_id": request.get("evidence_snapshot_id"),
            "evidence_snapshot": {},
            "benchmark_evaluation": {},
            "decision_readiness": {},
            "ai_interpretation": {},
            "missing_evidence": [],
            "recommended_next_steps": [],
            "pending_approval": {},
            "approval_action": None,
            "approval_payload": {},
            "human_decision": {},
            "decision_review": {},
            "completeness": {},
            "llm_available": self.llm_available,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "prompt_versions": dict(PROMPT_VERSIONS),
            "graph_version": GRAPH_VERSION,
            "planning_cycles": 0,
            "step_count": 0,
            "errors": [],
            "trace": [],
            "summary": "Starting governance agent run.",
            "unsupported_request": False,
            "user_question": request.get("user_question"),
        }

        # Seed previous decisions append-only without duplicating the same browser record.
        previous = request.get("previous_decisions") or []
        if previous:
            existing = list(self.decision_log.get(research_id) or [])
            seen = {
                (
                    item.get("decision"),
                    item.get("rationale"),
                    item.get("recorded_at"),
                )
                for item in existing
                if isinstance(item, dict)
            }
            for item in previous:
                if not isinstance(item, dict):
                    continue
                identity = (
                    item.get("decision"),
                    item.get("rationale"),
                    item.get("recorded_at"),
                )
                if identity not in seen:
                    existing.append(item)
                    seen.add(identity)
            self.decision_log[research_id] = existing

        config = {"configurable": {"thread_id": agent_run_id}}
        try:
            result_state = self.graph.invoke(initial, config)
        except Exception as exc:  # Persist an inspectable failure instead of returning HTTP 500.
            step_limited = isinstance(exc, GraphStepLimitError)
            result_state = {
                **initial,
                "status": "failed",
                "current_node": "handle_agent_error",
                "summary": (
                    "Governance Agent stopped at the configured graph-step limit."
                    if step_limited
                    else "Governance Agent stopped safely after an internal workflow error."
                ),
                "errors": [
                    (
                        f"graph_step_limit_exceeded:{MAX_GRAPH_STEPS}"
                        if step_limited
                        else f"agent_workflow_error:{type(exc).__name__}: {exc}"
                    )
                ],
                "step_count": MAX_GRAPH_STEPS if step_limited else 0,
            }
        detail = self._persist(agent_run_id, result_state, started_at=started_at)
        return {
            "agent_run_id": agent_run_id,
            "status": detail["status"],
            "current_node": detail["current_node"],
            "summary": detail["summary"],
        }

    def get_run(self, agent_run_id: str) -> dict[str, Any]:
        stored = self.run_store.get(agent_run_id)
        if stored is None:
            raise ResearchAgentError(f"Unknown agent_run_id '{agent_run_id}'.", status_code=404)
        return stored

    def resume_run(
        self,
        agent_run_id: str,
        action: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        stored = self.get_run(agent_run_id)
        if stored.get("status") == "cancelled":
            raise ResearchAgentError("Agent run is already cancelled.")
        if stored.get("status") == "completed":
            raise ResearchAgentError("Agent run is already completed.")
        if int(stored.get("step_count") or 0) >= MAX_GRAPH_STEPS:
            failed = {
                **stored,
                "status": "failed",
                "current_node": "handle_agent_error",
                "summary": "Governance Agent stopped at the configured graph-step limit.",
                "errors": list(stored.get("errors") or [])
                + [f"graph_step_limit_exceeded:{MAX_GRAPH_STEPS}"],
            }
            return self._persist(
                agent_run_id,
                failed,
                started_at=stored.get("started_at"),
            )

        config = {"configurable": {"thread_id": agent_run_id}}
        self.graph.update_state(
            config,
            {
                "approval_action": action,
                "approval_payload": payload or {},
                "status": "running",
            },
        )
        try:
            result_state = self.graph.invoke(None, config)
        except Exception as exc:
            step_limited = isinstance(exc, GraphStepLimitError)
            failed = {
                **stored,
                "status": "failed",
                "current_node": "handle_agent_error",
                "summary": (
                    "Governance Agent stopped at the configured graph-step limit."
                    if step_limited
                    else "Governance Agent stopped safely after an internal workflow error."
                ),
                "errors": list(stored.get("errors") or [])
                + [
                    (
                        f"graph_step_limit_exceeded:{MAX_GRAPH_STEPS}"
                        if step_limited
                        else f"agent_workflow_error:{type(exc).__name__}: {exc}"
                    )
                ],
                "step_count": (
                    MAX_GRAPH_STEPS
                    if step_limited
                    else int(stored.get("step_count") or 0)
                ),
            }
            return self._persist(
                agent_run_id,
                failed,
                started_at=stored.get("started_at"),
            )
        return self._persist(
            agent_run_id,
            result_state,
            started_at=stored.get("started_at"),
        )

    def cancel_run(self, agent_run_id: str) -> dict[str, Any]:
        stored = self.get_run(agent_run_id)
        if stored.get("status") in {"completed", "cancelled"}:
            return stored
        config = {"configurable": {"thread_id": agent_run_id}}
        self.graph.update_state(
            config,
            {
                "approval_action": "cancel",
                "status": "cancelled",
                "summary": "Agent run cancelled.",
            },
        )
        # Best-effort resume to finalize if interrupted
        try:
            result_state = self.graph.invoke(None, config)
        except Exception:
            result_state = {**stored, "status": "cancelled", "summary": "Agent run cancelled."}
        return self._persist(
            agent_run_id,
            result_state,
            started_at=stored.get("started_at"),
        )

    def _persist(
        self,
        agent_run_id: str,
        state: dict[str, Any],
        *,
        started_at: str | None,
    ) -> dict[str, Any]:
        status = state.get("status") or "running"
        completed_at = None
        if status in {"completed", "failed", "cancelled"}:
            completed_at = utc_now_iso()
        detail = {
            "agent_run_id": agent_run_id,
            "research_id": state.get("research_id"),
            "intent": state.get("intent"),
            "status": status,
            "current_node": state.get("current_node") or "unknown",
            "summary": state.get("summary") or "",
            "research_type": state.get("research_type") or "trend_following",
            "llm_available": bool(state.get("llm_available")),
            "llm_provider": state.get("llm_provider"),
            "llm_model": state.get("llm_model"),
            "prompt_versions": state.get("prompt_versions") or dict(PROMPT_VERSIONS),
            "graph_version": state.get("graph_version") or GRAPH_VERSION,
            "evidence_snapshot_id": state.get("evidence_snapshot_id"),
            "knowledge_context": state.get("knowledge_context") or [],
            "requested_tools": state.get("requested_tools") or [],
            "tool_results": state.get("tool_results") or [],
            "definition_review": state.get("definition_review") or {},
            "completeness": state.get("completeness") or {},
            "ai_interpretation": state.get("ai_interpretation") or {},
            "decision_review": state.get("decision_review") or {},
            "pending_approval": state.get("pending_approval") or {},
            "human_decision": state.get("human_decision") or {},
            "missing_evidence": state.get("missing_evidence") or [],
            "recommended_next_steps": state.get("recommended_next_steps") or [],
            "errors": state.get("errors") or [],
            "trace": state.get("trace") or [],
            "step_count": int(state.get("step_count") or 0),
            "started_at": started_at,
            "completed_at": completed_at,
        }
        self.run_store.save(agent_run_id, detail)
        return detail
