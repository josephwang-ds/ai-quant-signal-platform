# ADR-0009: DeepSeek as a governed research reviewer

- Status: Accepted
- Date: 2026-07-24

## Context

The workspace already had one backend-only OpenAI-compatible language-model
adapter used by Research Copilot. The product also needed help drafting
falsifiable research definitions and interpreting completed evidence, but a
language model must not become a second calculation engine, trading system, or
automatic approval mechanism.

## Decision

Keep one configured provider adapter and expose four focused reviewer actions:

1. Draft Research Definition
2. Review Hypothesis
3. Review Research Evidence
4. Identify Missing Research Steps

All actions use one reviewer system policy and strict Pydantic response
schemas. Structured research context is treated as untrusted input. Reviewer
output is rejected when it is malformed, cites evidence outside the supplied
snapshot, introduces unsupported numerical claims, uses causal/significance
language that the evidence cannot support, or recommends trading/capital
deployment.

The deterministic application services remain authoritative for benchmark
metrics, validation, robustness, data-quality checks, and suggested decision
support. AI-proposed success criteria always have `source = ai_proposed`,
`threshold = null`, and remain inactive until a researcher explicitly reviews
and enables them.

The UI presents reviewer output as an unsaved card with Apply/Edit/Dismiss
controls. It never silently writes research definitions or decision records.
Final decisions remain human-authored and are appended with their evidence
snapshot, benchmark verdict, system suggestion, reviewer, rationale, and
timestamp.

## Configuration and failure mode

The existing environment variables remain authoritative:

- `LLM_PROVIDER=deepseek`
- `LLM_API_KEY`
- `LLM_BASE_URL` (default DeepSeek API URL when the provider is DeepSeek)
- `COPILOT_MODEL`

No provider key is sent to the browser. The application starts and all
deterministic research features continue to work when AI is unconfigured. AI
review endpoints return an honest `503` in that state; they never fall back to
fake content.

## Consequences

- There is no second DeepSeek/OpenAI client to configure or secure.
- Reviewer output is auditable through provider/model/generated-at metadata and
  evidence snapshot timestamps.
- Benchmark and decision behavior is reproducible without the language model.
- The additional schemas and safety checks make model upgrades more deliberate,
  but provider responses cannot silently change the product contract.
