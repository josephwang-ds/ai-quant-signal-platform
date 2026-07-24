# Quant Research Governance Agent

Status: portfolio / research-demo capability  
Related ADR: `docs/adr/ADR-0010-quant-research-governance-agent.md`

## Responsibilities

The Governance Agent coordinates a **controlled research-review workflow**:

1. Inspect research definitions
2. Retrieve versioned Research Rulebook guidance
3. Select approved deterministic tools
4. Pause for human approval before expensive validation
5. Interpret supplied evidence with DeepSeek (when configured)
6. Prepare a decision-review draft
7. Wait for an explicit human decision

Core principle: **Evidence First · AI Second · Human Final**

## Prohibited behavior

The Agent must not:

- calculate financial metrics
- invent missing evidence or treat unavailable as zero
- predict prices or recommend securities
- generate or execute trades
- approve live deployment
- silently activate numeric success thresholds
- overwrite prior human decisions
- run unbounded autonomous loops
- execute arbitrary code or HTTP tools
- expose raw chain-of-thought

## Node graph

`classify_intent` → `load_research_context` → `review_research_definition` →
`retrieve_methodology` → `inspect_available_evidence` → `plan_tool_calls` →
(`request_tool_approval`) → `execute_approved_tools` → `refresh_evidence_snapshot` →
`review_evidence` → `assess_research_completeness` → (`prepare_decision_review` →
`await_human_decision`) → `finalize_agent_run`

Intent-specific shortcuts apply (for example definition review skips expensive tools).

## Tool registry

Read-only tools may run without approval. Deterministic execution tools and
write-sensitive actions require approval / confirmation.

See `backend/app/research_agent/tools/__init__.py`.

## Citations

- **Knowledge citation**: Research Rulebook section (`knowledge_id`, version, excerpt)
- **Evidence citation**: calculated result IDs from the current evidence snapshot

These are visually and structurally distinct in the Agent panel.

## Prompt versions

Tracked in `backend/app/research_agent/prompts.py` (`PROMPT_VERSIONS`).

## Run trace

Each run returns concise workflow events (node, event, detail). No raw CoT.

## Failure modes

| Condition | Behavior |
|-----------|----------|
| No LLM key | Deterministic nodes still run; AI interpretation marked unavailable |
| Unsupported trading/prediction ask | Fail safely |
| Unknown tool / bad args | Rejected by registry |
| Mixed/stale snapshot | Stop review as inconclusive/failed |
| Process restart | In-memory graph/run state is lost |

## Limitations

- Process-local MemorySaver / agent run store (not durable across Render restarts)
- Curated local rulebook — not a broad financial corpus
- No broker, live trading, portfolio optimization, or external paper search
- DeepSeek interpretation remains advisory and imperfect
