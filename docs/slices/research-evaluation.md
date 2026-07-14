# Research Evaluation (PR-010)

## Purpose

Evaluation is the research governance layer. It answers one question only:

> Do we have enough trustworthy evidence to continue research?

It never answers "should we buy?" Evaluation is not another backtest, not
another validation engine, not AI interpretation, not a confidence score,
and not a profitability ranking or investment recommendation.

Execution (PR-008B) calculates strategy metrics. Validation (PR-009)
calculates evidence across six deterministic stages and **saves its own
output**. **Evaluation summarizes an already-produced `ValidationResult`.**
It performs no market-data reads, no MA-crossover calculation, no OOS split,
no sensitivity grid, and no transaction-cost grid — and, since the
ValidationResultStore refactor, it never triggers a new Validation run
either. It reads exactly one stored payload per request and only extracts
the `stage` / `label` / `status` / `summary` / `blockers` fields that
Validation already produced.

## Architecture

```
app.research_validation.service.ResearchValidationService
  ├── depends on app.research_execution.market_data_port.MarketDataPort
  └── saves its result to app.research_validation.result_store.ValidationResultStore

app.research_evaluation.service.ResearchEvaluationService
  └── depends only on app.research_validation.result_store.ValidationResultStore
```

`ResearchEvaluationService` has **no dependency on `ResearchValidationService`
and no dependency on `MarketDataPort`** — its constructor accepts only a
`ValidationResultStore`. This is enforced by:

- a constructor-signature test
  (`test_evaluation_service_has_no_validation_service_dependency`);
- a source-inspection test that forbids calculation, market-data-adapter,
  and `ResearchValidationService` imports in the evaluation module
  (`test_no_calculation_or_validation_execution_imports_in_evaluation_module`);
- a spy/failing-dependency test that monkeypatches both
  `FixtureMarketDataAdapter.get_daily_ohlcv` and
  `ResearchValidationService.execute` to raise, then proves Evaluation still
  succeeds because it never calls either
  (`test_evaluation_never_touches_market_data_or_validation_service`).

**ValidationResultStore (MVP scope).** A lightweight in-memory store
(`InMemoryValidationResultStore`) keyed by an opaque `validation_run_id`.
Validation calls `store.save(result)` exactly once per successful run and
returns the id to the caller; Evaluation calls `store.get(validation_run_id)`
exactly once and never writes to the store. The Validation API route and the
Evaluation API route resolve the **same process-wide store instance**
(`get_default_validation_result_store()`), so a `validation_run_id` returned
by one request can be loaded by a later request against the other endpoint.
There is no Postgres, no Redis, and no background worker — **saved results
are lost on backend restart.** Persistent `ValidationRun` storage remains
explicitly deferred to a future ADR.

Presentation (`ResearchEvaluationPanel`) renders only backend-provided
fields. It contains no client-side scoring, ranking, or recommendation
logic.

## API

`POST /api/v1/research/evaluation`

Request:

```json
{ "research_id": "ma-crossover-spy", "validation_run_id": "val-3f9c2a1b8e7d4c56" }
```

`validation_run_id` is required and has no default: Evaluation cannot
synthesize one, because doing so would mean triggering a new Validation run.
`research_id` and `validation_run_id` are the only accepted fields; extra
fields are rejected.

- An unsupported `research_id` returns HTTP `400`.
- A missing `validation_run_id` returns HTTP `422` (request-schema
  validation) if omitted entirely, or a `400` with a clear message
  (`"validation_run_id is required..."`) if the service layer receives an
  empty string.
- An unknown `validation_run_id` returns HTTP `404`.
- A `validation_run_id` that belongs to a different `research_id` than the
  one in the request returns HTTP `400`.

Response (`ResearchEvaluationResponse`):

```json
{
  "research_id": "ma-crossover-spy",
  "evaluation_status": "incomplete",
  "evidence_summary": [
    {
      "stage": "historical_backtest",
      "label": "Historical backtest",
      "status": "completed",
      "summary": "Full-history deterministic MA-crossover evidence was calculated."
    }
  ],
  "evidence_coverage": {
    "implemented_stage_count": 6,
    "completed_stage_count": 5,
    "coverage_percentage": 83.33
  },
  "completed_stages": ["Historical backtest", "Benchmark comparison", "..."],
  "incomplete_stages": ["Out-of-sample validation"],
  "unavailable_stages": [
    "Stress testing",
    "Regime analysis",
    "Walk-forward validation",
    "Monte Carlo simulation"
  ],
  "blockers": ["Insufficient OOS history: need at least 252 valid return rows; got 150."],
  "limitations": ["Evaluation is based on historical evidence only; it performs no new calculations.", "..."],
  "outstanding_evidence": [
    "Stress testing",
    "Regime analysis",
    "Walk-forward validation",
    "Monte Carlo simulation",
    "Paper trading"
  ],
  "provenance": {
    "research_id": "ma-crossover-spy",
    "validation_run_id": "val-3f9c2a1b8e7d4c56",
    "validation_generated_at": "2026-07-14T09:33:15Z",
    "market_data_provenance": { "provider": "yahoo", "source": "Yahoo Finance via yfinance" }
  },
  "generated_at": "2026-07-14T09:33:16Z"
}
```

Evaluation never returns the full validation payload (`stages`, `oos`,
`parameter_sensitivity`, `transaction_cost_sensitivity`, `data_quality` are
absent). `provenance.validation_run_id`, `provenance.validation_generated_at`,
and `provenance.market_data_provenance` are a reference to the stored
validation run that produced the summarized evidence, not a duplicate of it.

HTTP:

- `400` — unsupported `research_id`, missing `validation_run_id` at the
  service layer, or a `validation_run_id`/`research_id` mismatch (all
  request-contract problems, not evidence-availability problems)
- `404` — unknown `validation_run_id` (nothing was ever saved under that id,
  or the in-memory store lost it across a backend restart)
- `200` with `evaluation_status: "blocked"` — the **stored** `ValidationResult`
  itself recorded a fatal stage failure (e.g. a calculation failure baked
  into evidence that was already saved). Evaluation's job is to report
  evidence completeness even when the underlying evidence is degraded, so a
  failed stage is reported as a governance blocker inside a `200` response
  body rather than as an opaque HTTP error. Evaluation never produces this
  status from a live provider failure, because it never calls the provider.

## Status rules

Allowed `evaluation_status` values are **only** `completed`, `incomplete`,
or `blocked`. The following words never appear in an evaluation response:
`passed`, `failed strategy`, `robust`, `good`, `excellent`, `approved`,
`recommend`, or a standalone `buy`/`sell` directive.

- **completed** — every implemented validation stage in the stored result
  completed, and no stage is `failed`.
- **incomplete** — no stage `failed`, but at least one implemented stage is
  `incomplete`.
- **blocked** — at least one implemented stage in the stored result is
  `failed`. Evaluation derives this purely from the stored evidence; it
  never independently detects a "provider unavailable" condition, because
  it never calls a market-data provider.

This mirrors `ResearchValidationService`'s own `failed > incomplete >
completed` precedence, renamed to the governance vocabulary
(`failed` → `blocked`).

## Evidence coverage definition

Coverage is **implementation completeness, not confidence, not quality,
and not robustness**.

```
implemented_stage_count = 6   (fixed: the six PR-009 stages)
completed_stage_count   = count of those six with status "completed"
coverage_percentage     = round(completed_stage_count / implemented_stage_count * 100, 2)
```

Example: 5 of 6 implemented stages completed → `83.33%` coverage. A future
stage (Stress, Regime, Walk-forward, Monte Carlo) is never counted in the
denominator, because coverage measures what has been *built*, not what
would be ideal.

## Blockers

Blockers are a deterministic, deduplicated union of the `blockers` field
already computed by each of the six stages **in the stored `ValidationResult`**
(e.g. "Insufficient OOS history: need at least 252 valid return rows; got
150.", or a data-quality fatal-check summary). No blocker is invented and no
blocker is derived from a live call: Evaluation only reads what
`ResearchValidationService` already wrote to the store at Validation time.

A provider failure (HTTP `502`) or an insufficient-full-history failure
(HTTP `400`) can only happen **during Validation**, before anything is
saved — so a `validation_run_id` never exists for that failed attempt, and
Evaluation can never be called with it. The frontend enforces this by only
sending a `validation_run_id` once Validation has actually produced a
result (see Frontend, below).

## Limitations

A fixed, informational list, independent of this run's results:

- Evaluation is based on historical evidence only; it performs no new
  calculations.
- Independent benchmark comparison is unavailable; benchmark evidence uses
  same-asset buy-and-hold only.
- Stress testing is not implemented.
- Regime analysis is not implemented.
- Walk-forward validation is not implemented.
- Monte Carlo simulation is not implemented.
- Research has not been published.
- Paper trading is unavailable.

## Outstanding evidence

The unavailable validation capabilities plus paper trading — evidence a
reviewer would need before further governance decisions, never phrased as
strategy advice:

- Stress testing
- Regime analysis
- Walk-forward validation
- Monte Carlo simulation
- Paper trading

## Frontend

The workspace never lets Evaluation trigger its own Validation run. It
reuses the `validation_run_id` from the Validation result already loaded by
the workspace (`useResearchValidation`) and passes it into
`useResearchEvaluation(researchId, enabled, validationRunId)`:

- If Validation has not produced a `validation_run_id` yet (e.g. the user
  opens the Evaluation tab first), the hook reports status
  `awaiting_validation` and performs **no request**. The panel shows "Run
  or load Validation evidence before Evaluation can be generated." with a
  link to the Validation tab — it never silently runs Validation and never
  falls back to mock evidence.
- Once Validation completes and a `validation_run_id` becomes available,
  the hook automatically transitions to `loading` and calls
  `POST /api/v1/research/evaluation` with that id.

`ResearchEvaluationPanel` itself renders an enterprise governance dashboard,
not a trading UI:

- Evaluation status badge (`completed` / `incomplete` / `blocked`)
- Evidence coverage (implemented / completed / percentage, with an explicit
  "not a confidence score" disclaimer)
- Evidence summary table (one row per implemented stage: label, status,
  backend summary text)
- Completed evidence / incomplete evidence / outstanding evidence /
  limitations / blockers lists
- Generated time and provenance source
- The existing `ResearchTimeline` component, reused (not duplicated) to
  show research lifecycle events alongside evaluation evidence

The panel never renders a numeric score, star rating, confidence badge, or
buy/sell recommendation. This is enforced by a frontend test.

## Out of scope

No AI/LLM summarization, no strategy ranking, no portfolio integration, no
Publish Strategy, no Paper Trading execution, no stress testing, no regime
analysis, no walk-forward optimization, no Monte Carlo simulation. These
remain future validation stages (Epic C/D) or future bounded contexts
(Portfolio, Governance) per `ROADMAP.md`.

## Local verification

```bash
cd backend
PYTHONPATH=. python3 -m pytest tests/test_research_evaluation.py -v

cd ../frontend
npm test -- --run
npm run build
```

The backend fixture suite is offline and uses
`backend/tests/fixtures/spy_daily_sample.csv` via the same
`ResearchValidationService` fixture adapter PR-009 already tests against —
seeding a `ValidationResultStore` directly rather than going through the
HTTP layer.

## Future work

- Replace the in-memory `ValidationResultStore` with a durable store
  (e.g. Postgres-backed `ValidationRun` table) so evidence survives a
  backend restart. Deferred pending an ADR; out of scope for this slice.
- Stress testing, regime analysis, walk-forward validation, and Monte
  Carlo simulation remain unimplemented validation stages; they will change
  `IMPLEMENTED_STAGE_LABELS` and the coverage denominator when added.
