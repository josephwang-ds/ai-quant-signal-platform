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
`FactorValidationService`, `MarketDataPort`, or any financial calculation
module.** It never calls Validation `execute`. For Factor Research runs it
reads the stored Factor Validation payload only and **skips** MA Evaluation
aggregation (factor evidence has no MA `stages`).

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
injection. Production uses `OpenAiCompatibleLlmAdapter` for exactly one
configured OpenAI-compatible provider. There is no runtime environment switch
that can activate a fake provider in a deployed app, and no multi-provider
failover.

Configuration (backend / Render secrets only — never `NEXT_PUBLIC_*`):

| Variable | Role |
|---|---|
| `LLM_PROVIDER` | Allowlisted: `openai` \| `deepseek` |
| `LLM_API_KEY` | Preferred API key |
| `LLM_BASE_URL` | Optional HTTPS base URL (trailing slash normalized) |
| `COPILOT_MODEL` | Model id for the active provider |

Defaults:

- OpenAI → `https://api.openai.com/v1`, `gpt-4o-mini`
- DeepSeek → `https://api.deepseek.com`, `deepseek-v4-flash`

Endpoint construction: `{LLM_BASE_URL}/chat/completions` (no duplicated
`/v1` or `/chat/completions` segments).

`OPENAI_API_KEY` remains a temporary deprecated fallback when `LLM_API_KEY`
is absent. Missing/invalid provider configuration returns HTTP 503.

Structured output: both OpenAI and DeepSeek accept
`response_format: {"type": "json_object"}`. The Copilot keeps that request
and still parses/rejects malformed JSON strictly. Citation and recommendation
safety checks are unchanged. Model availability depends on the provider
account and current API catalog — set `COPILOT_MODEL` explicitly for demos.
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

### Factor Research citations

When `evidence_kind === "factor_validation"` (or template
`cross_sectional_factor`), the assembler builds Factor citations only — it
does **not** fabricate MA validation stages:

| citation_id | Source |
|---|---|
| `factor:rank_ic` | Stored RankIC / IC summary |
| `factor:icir` | Stored ICIR |
| `factor:turnover` | Quantile turnover evidence |
| `factor:long_short` | Long–short cumulative (prefer net of cost) |
| `factor:stability` | Benchmark subperiod stability / rationale |
| `factor:warnings` | Engine / data warnings on the stored run |

Factor replies also return an additive `factor_summary` object on the API
response (strings only; missing metrics are the literal `unavailable`):

```json
{
  "rank_ic": "0.12",
  "icir": "0.8",
  "turnover": "0.42",
  "long_short_return": "0.15",
  "stability": "…from evidence…",
  "warnings": ["…"],
  "citation_ids": ["factor:rank_ic", "…"]
}
```

The server always attaches evidence-built `factor_summary`. If the model
returns different metric strings, they are overridden and warned
(`factor_summary_field_overridden:*`).

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
  "generated_at": "2026-07-15T12:00:00Z",
  "factor_summary": null
}
```

For Factor Research, `factor_summary` is populated from the stored Factor
Validation run. MA clients may ignore the optional field.

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

For Factor Research, the model should also include the factor summary fields
(`rank_ic`, `icir`, `turnover`, `long_short_return`, `stability`, `warnings`)
echoing assembled context only. The service still prefers stored evidence
values over model strings.

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
- `FabricatingFakeLlm`, `FabricatingFactorFakeLlm`, `EmptyCitationFakeLlm`,
  and `UnknownCitationFakeLlm` for safety and citation-resolution tests
- Factor path tests: evidence-only `factor_summary`, MA Evaluation skipped,
  fabricated factor metrics overridden, buy/sell blocked
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
- predicting markets or recommending trades (including Factor Research)
- calculating or inventing RankIC / ICIR / turnover / long–short metrics
