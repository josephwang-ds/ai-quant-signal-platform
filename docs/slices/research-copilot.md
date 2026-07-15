# Research Copilot (PR-012)

## Purpose

Research Copilot is an evidence-grounded interpretation layer inside the
canonical Research Workspace. It explains existing workspace evidence — it
does not create quantitative truth.

The Copilot may:

- explain backend-generated metrics already present in Validation evidence
- summarize execution evidence attached to a stored Validation run
- explain validation stage status and blockers
- explain evaluation governance status, limitations, and outstanding evidence
- answer methodology questions using approved documentation chunks
- suggest next **research** steps (e.g. run stress testing) based on gaps

The Copilot must not:

- calculate financial metrics
- rerun backtests or trigger Validation
- modify validation or evaluation outcomes
- generate numerical confidence scores
- predict prices or returns
- recommend BUY, SELL, HOLD, or position size
- claim a strategy is robust, approved, or profitable
- invent evidence or use general model knowledge as workspace fact

**Product principle:** Execution produces evidence. Validation verifies
evidence. Evaluation governs evidence. Copilot explains evidence.

## Architecture

```
app.research_copilot.service.ResearchCopilotService
  ├── ValidationResultStore.get(validation_run_id)   # read-only
  ├── ResearchEvaluationService.execute(...)         # read-only aggregation
  ├── ResearchContextAssembler.assemble(...)           # deterministic
  ├── RetrievalIndex.search(...)                       # bounded doc chunks
  └── LlmPort.generate(...)                            # interpretation only
```

`ResearchCopilotService` has **no dependency on `ResearchValidationService`,
`MarketDataPort`, or any financial calculation module.** It never calls
`ResearchValidationService.execute`.

Provider SDKs live only in Infrastructure (`openai_adapter.py` via stdlib
`urllib`). Application and Domain never import provider packages.

### LlmPort

```python
class LlmPort(Protocol):
    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        context: list[ContextItem],
    ) -> LlmResult: ...
```

Offline CI injects `FakeLlmAdapter` explicitly through test dependency
injection. Production uses `OpenAiLlmAdapter` when `OPENAI_API_KEY` is set.
There is no runtime environment switch that can activate a fake provider in a
deployed app. Missing `OPENAI_API_KEY` returns HTTP 503.

Default model: `gpt-4o-mini` (override with `COPILOT_MODEL`).

## Context assembly

`ResearchContextAssembler` builds bounded `ContextItem` records. Each item
carries a stable `citation_id` used for answer-specific citation resolution.

Initial citation IDs:

| citation_id | Source |
|---|---|
| `execution:metrics` | Historical backtest + benchmark comparison summaries |
| `validation:out_of_sample` | OOS validation stage |
| `validation:parameter_sensitivity` | Parameter grid stage |
| `validation:transaction_cost_sensitivity` | Transaction-cost grid stage |
| `validation:data_quality` | Data-quality stage |
| `evaluation:status` | Evaluation status, coverage, blockers |
| `evaluation:outstanding_evidence` | Outstanding evidence list |
| `notebook:hypothesis` | Structured notebook hypothesis entry |
| `notebook:methodology` | Notebook methodology entry |
| `notebook:observation` | Notebook observation entry |
| `documentation:look_ahead_policy` | Execution methodology excerpt |
| `documentation:validation_methodology` | Validation slice excerpt |
| `documentation:evaluation_governance` | Evaluation slice excerpt |
| `documentation:authenticity_policy` | Authenticity policy excerpt |
| `documentation:project_constitution` | Project Bible excerpt |

Requirements enforced in code:

- NaN / Infinity removed
- `equity_curve`, `prices`, `daily_returns`, and raw `series` arrays excluded
- timestamps and provenance preserved where available
- unavailable evidence labeled explicitly

## Retrieval scope (MVP)

In-memory keyword retrieval over safe public documents:

- `docs/slices/research-execution.md`
- `docs/slices/research-validation.md`
- `docs/slices/research-evaluation.md`
- `docs/data/AUTHENTICITY_POLICY.md`
- `docs/PROJECT_BIBLE.md` (bounded excerpts)

No internet search, no live news, no arbitrary repository ingestion, no
external vector database.

## API

`POST /api/v1/research/copilot/query`

Request:

```json
{
  "research_id": "ma-crossover-spy",
  "validation_run_id": "val-…",
  "question": "Why is the evaluation incomplete?",
  "conversation": []
}
```

Response:

```json
{
  "research_id": "ma-crossover-spy",
  "answer": "…",
  "citations": [
    {
      "source_type": "evaluation",
      "source_id": "val-…",
      "label": "Outstanding evidence",
      "excerpt": "Stress testing and regime analysis are unavailable."
    }
  ],
  "warnings": [],
  "grounding_status": "grounded",
  "model": "gpt-4o-mini",
  "generated_at": "2026-07-15T12:00:00Z"
}
```

Errors:

| Status | Meaning |
|--------|---------|
| 400 | Invalid research id, missing question, mismatched validation run |
| 404 | Unknown `validation_run_id` |
| 502 | Provider unavailable |
| 503 | Copilot not configured (no API key) |
| 504 | Provider timeout |

No provider stack traces are returned.

## Citation contract

The provider must return structured JSON:

```json
{
  "answer": "<grounded explanation>",
  "citation_ids": ["evaluation:status", "evaluation:outstanding_evidence"]
}
```

`ResearchCopilotService` then:

1. Parses the structured output safely.
2. Resolves only `citation_ids` present in the assembled context index.
3. Drops or warns on unknown IDs.
4. Returns only the citations selected for that answer.
5. Marks substantive answers with no valid citations as `unavailable` or
   `partially_grounded` — never attaches a fixed generic citation bundle.

Resolved API citations still expose `source_type`, `source_id`, `label`, and
`excerpt` derived from the matching `ContextItem`.

## Grounding and safety

Server-owned `COPILOT_SYSTEM_POLICY` plus post-generation checks:

- block investment recommendation language (`buy`, `sell`, `hold`, etc.)
  except documented `buy-and-hold` benchmark references
- flag unsupported numeric claims vs assembled context
- flag missing citations
- map unsafe output to a safe fallback with `grounding_status=unavailable`

When the LLM is unavailable, the API returns an honest error — **no fake
AI answer** is synthesized.

## Frontend

`Research Copilot` tab inside the canonical Research Workspace:

- sample questions
- question input
- answer + citations + grounding status
- limitations disclaimer
- awaiting-validation and not-configured states

The browser calls only `POST /api/v1/research/copilot/query` via
`researchCopilotApi.ts`. It never calls OpenAI or Anthropic directly.

## Offline testing

- `FakeLlmAdapter` injected explicitly in unit/API tests
- `FabricatingFakeLlm`, `EmptyCitationFakeLlm`, and `UnknownCitationFakeLlm`
  for safety and citation-resolution tests
- `evaluate_answer` unit tests for prohibited language
- repository policy tests: no `NEXT_PUBLIC_*API_KEY`, no frontend SDK imports
- tests proving `COPILOT_ALLOW_FAKE_LLM` cannot enable fake runtime answers

## Explicit non-goals

- autonomous research or trading
- multi-provider routing
- persistent chat history
- external vector infrastructure (Pinecone, Weaviate, etc.)
- strategy generation or automatic backtest execution
- live financial news RAG
