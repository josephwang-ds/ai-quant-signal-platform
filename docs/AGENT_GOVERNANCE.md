# Quant Research Governance Agent

Status: portfolio / research-demo capability  
Related ADR: `docs/adr/ADR-0010-quant-research-governance-agent.md`

## Responsibilities

The Governance Agent coordinates a **controlled research-review workflow**:

1. Inspect research definitions
2. Retrieve versioned Research Rulebook guidance
3. Build a deterministic, research-type-specific tool plan
4. Pause for human approval before expensive validation
5. Interpret supplied evidence with DeepSeek (when configured)
6. Prepare a decision-review draft
7. Wait for an explicit human decision

Core principle: **Evidence First · AI Second · Human Final**

The model never chooses tools, changes workflow completeness, or produces the
Promote / Hold / Reject suggestion. It receives a read-only normalized snapshot
and may only explain the supplied definition and evidence.

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

Production routes inject the existing Research Execution, Research Validation,
and Factor Validation services. Approved tools therefore run the same
deterministic engines and the same saved run configuration as the workspace.

## Evidence contracts

- Trend research requires execution, aligned benchmark, completed validation,
  OOS, parameter sensitivity, cost sensitivity, and data-quality evidence.
- Factor research requires completed factor validation, its benchmark, and
  calculated RankIC evidence.

Stored validation stages are normalized from the production list envelope.
Failed or incomplete stages never count as available evidence.

## Decision boundary

The deterministic suggestion is derived only from the benchmark verdict,
validation failure state, missing required evidence, and pre-decision workflow
readiness:

- failed validation or failed benchmark → `Reject`
- missing/incomplete evidence → `Hold`
- complete evidence with passing benchmark → `Promote`
- otherwise → `Hold`

AI interpretation is displayed separately and cannot mutate these inputs.

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
| Provider timeout or malformed LLM JSON | Continue deterministically; mark AI interpretation unavailable |
| Graph exceeds 24 nodes | Stop with a persisted terminal failure |
| Process restart | In-memory graph/run state is lost |

## Limitations

- Process-local MemorySaver / agent run store (not durable across Render restarts)
- Curated local rulebook — not a broad financial corpus
- No broker, live trading, portfolio optimization, or external paper search
- DeepSeek interpretation remains advisory and imperfect
- At most one LLM generation occurs in a graph pass; tool planning and decision
  suggestion are deterministic to keep latency and authority bounded
