# AI Grounding and Demo Audit

**Date:** 2026-07-15 · **Baseline:** `main` @ `a897c13` (PR #13 merged) · **Scope:** PR-012 Research Copilot — read-only audit, no code changes

## Executive Summary

PR #13 (Research Copilot) is merged to `main`. The Copilot is **evidence-grounded** for portfolio/demo use: answer-specific `citation_ids`, no runtime fake-provider switch, deterministic safety checks, and honest HTTP 503 when `OPENAI_API_KEY` is absent.

**CI on `main` is green** (run `29394976761`). Live provider smoke was **not run** — no API key in the audit environment (non-blocking).

**Verdict: Portfolio v1.1 Ready** with stated limitations: Copilot live answers require backend provider configuration; legacy backtest tests may fail locally under sandbox network limits while CI passes.

---

## Merged Baseline

| Item | Value |
|---|---|
| Commit | `a897c13` |
| Merged PR | [#13 — Research Copilot](https://github.com/josephwang-ds/ai-quant-signal-platform/pull/13) |
| CI | [29394976761](https://github.com/josephwang-ds/ai-quant-signal-platform/actions/runs/29394976761) — all jobs success |
| Vercel Production | Deployed after merge |

**Confirmed on `main`:**
- `POST /api/v1/research/copilot/query`
- Structured output `{"answer","citation_ids"}` with context-bound resolution
- No `COPILOT_ALLOW_FAKE_LLM` runtime switch
- `FakeLlmAdapter` injected in tests only

---

## Architecture (key boundaries)

| Claim | Result | Evidence |
|---|---|---|
| Frontend calls backend only | Pass | `researchCopilotApi.ts` |
| No OpenAI/Anthropic SDK in frontend | Pass | `researchCopilotPolicy.test.ts` |
| No `MarketDataPort` / validation re-execution | Pass | `service.py`, inspection tests |
| Reads stored `ValidationResult` only | Pass | `ValidationResultStore.get()` |
| Missing key → 503 | Pass | `resolve_llm_adapter()`, API test |
| Provider timeout/unavailable → 504/502 | Pass | `service.py` error mapping |

---

## Citation Grounding

Each `ContextItem` carries a stable `citation_id` (e.g. `validation:out_of_sample`, `evaluation:status`, `documentation:look_ahead_policy`). The provider returns `citation_ids`; the service resolves only IDs present in the assembled context, warns on unknown IDs, and does not attach a fixed generic bundle.

| Question type | Cites (observed with test adapter) |
|---|---|
| OOS | `validation:out_of_sample`, `documentation:validation_methodology` |
| Transaction cost | `validation:transaction_cost_sensitivity` |
| Evaluation governance | `evaluation:status`, `evaluation:outstanding_evidence` |
| Look-ahead / methodology | `notebook:methodology`, `documentation:look_ahead_policy` |

Substantive answers with zero valid citations → `grounding_status=unavailable`.

---

## Safety

Deterministic checks block BUY/SELL/HOLD/position-size/guaranteed/approved/robust language. Fabricated numerics flagged as `partially_grounded`. No fake answer when provider is missing. Warnings returned in API and shown in UI.

---

## Context Bounds

Typical assembly: ~15 context items, ~21 KB payload. Excludes API keys, home paths, raw source code, full equity curves, and price/return arrays. Question max 1,000 chars; conversation bounded.

---

## Test Results

| Suite | Result | Notes |
|---|---|---|
| `test_research_copilot.py` | 22 passed | |
| Focused research suites | 103 passed | |
| Backend full offline (local) | 145 passed, 13 failed | Legacy yfinance; **CI passes** |
| Frontend tests | 128 passed | |
| Frontend build | Pass | CI typecheck passes |

---

## Demo Notes

**Canonical flow:** Execution → Validation → Evaluation → Copilot.

**Friction:** (1) provider key needed for live Copilot answers; (2) nine workspace tabs — stay on evidence spine; (3) grounding status labels need a brief verbal explanation.

**60-second pitch:** Execution computes, Validation verifies, Evaluation governs, Copilot explains — deterministic systems stay authoritative; the LLM is interpretation only.

---

## Final Verdict

**Portfolio v1.1 Ready** — citations are answer-specific, unsafe recommendations are blocked, no runtime fake provider, missing provider state is honest.
