# ADR-0010: Controlled Quant Research Governance Agent

- Status: Accepted
- Date: 2026-07-24

## Context

Research Copilot and the DeepSeek reviewer actions already interpret evidence
through one OpenAI-compatible backend adapter. The product still needed an
explicit multi-step research governance workflow with tool allowlisting, human
approval gates, methodology retrieval, and decision-review drafts — without
becoming a free-form chatbot or a second calculation engine.

## Decision

Introduce a single Quant Research Governance Agent orchestrated by LangGraph:

- Graph state, nodes, conditional edges, interrupt/resume, and step limits
- Approved tool registry that calls existing deterministic services
- Versioned Research Rulebook retrieval (lightweight lexical ranking)
- DeepSeek interpretation only over supplied evidence/knowledge context
- Human approval before expensive validation and before recording decisions
- Process-local checkpointer for this portfolio iteration

Reuse the existing `LlmPort` / `resolve_llm_adapter()` stack. Do not add a second
DeepSeek HTTP client or parallel env-var scheme.

LangGraph is appropriate because the workflow is an explicit state machine with
pause/resume, not a single prompt. One governance agent is preferable to
multi-persona role-play agents. Deterministic services remain authoritative for
metrics. Lightweight rulebook retrieval is sufficient; a vector database is not
required. The Agent cannot trade.

## Consequences

- Copilot `POST /api/v1/research/copilot/query` remains a focused evidence-query
  endpoint with an unchanged contract.
- New routes: `POST/GET /api/v1/research/agent/runs` (+ resume/cancel).
- Agent runs may be lost on process restart until durable checkpointing is added.
- Frontend Overview hosts the Agent panel; lifecycle spine is unchanged.
