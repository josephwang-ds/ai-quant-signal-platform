# Research Evaluation (PR-010)

## Purpose

Evaluation is the research governance layer. It answers one question only:

> Do we have enough trustworthy evidence to continue research?

It never answers "should we buy?" Evaluation is not another backtest, not
another validation engine, not AI interpretation, not a confidence score,
and not a profitability ranking or investment recommendation.

Execution (PR-008B) calculates strategy metrics. Validation (PR-009)
calculates evidence across six deterministic stages. **Evaluation summarizes
that evidence.** It performs no market-data reads, no MA-crossover
calculation, no OOS split, no sensitivity grid, and no transaction-cost
grid. It calls `ResearchValidationService.execute(...)` exactly once and
only reads the `stage` / `label` / `status` / `summary` / `blockers` fields
that service already produced.

## Architecture

```
app.research_evaluation.service.ResearchEvaluationService
  └── depends on app.research_validation.service.ResearchValidationService
        └── depends on app.research_execution.market_data_port.MarketDataPort
```

`ResearchEvaluationService` holds no calculation logic and imports no
calculation function (`run_ma_crossover_research`,
`summarize_return_segment`) or market-data type. This is enforced by a
dedicated backend test that inspects the module source
(`test_no_calculation_functions_are_imported_by_evaluation`).

Presentation (`ResearchEvaluationPanel`) renders only backend-provided
fields. It contains no client-side scoring, ranking, or recommendation
logic.

## API

`POST /api/v1/research/evaluation`

Request:

```json
{ "research_id": "ma-crossover-spy" }
```

`research_id` is the only accepted field; extra fields are rejected. An
unsupported `research_id` returns HTTP `400`.

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
    "validation_generated_at": "2026-07-14T09:33:15Z",
    "market_data_provenance": { "provider": "yahoo", "source": "Yahoo Finance via yfinance" }
  },
  "generated_at": "2026-07-14T09:33:16Z"
}
```

Evaluation never returns the full validation payload (`stages`, `oos`,
`parameter_sensitivity`, `transaction_cost_sensitivity`, `data_quality` are
absent). `provenance.validation_generated_at` and
`provenance.market_data_provenance` are a reference to the validation run
that produced the summarized evidence, not a duplicate of it.

HTTP:

- `400` — unsupported `research_id` (a request-contract problem, not an
  evidence-availability problem)
- `200` with `evaluation_status: "blocked"` — provider failure, missing
  market data, or a fatal validation-stage failure. Evaluation's job is to
  report evidence completeness even when the underlying data is
  unavailable, so these conditions are reported as governance blockers
  inside the response body rather than as an opaque HTTP error.

## Status rules

Allowed `evaluation_status` values are **only** `completed`, `incomplete`,
or `blocked`. The following words never appear in an evaluation response:
`passed`, `failed strategy`, `robust`, `good`, `excellent`, `approved`,
`recommend`, or a standalone `buy`/`sell` directive.

- **completed** — every implemented validation stage completed, and no
  stage is `failed`.
- **incomplete** — no stage `failed`, but at least one implemented stage is
  `incomplete`.
- **blocked** — a fatal validation failure: either at least one implemented
  stage is `failed`, or the underlying validation call itself could not
  produce evidence (provider unavailable / historical execution failed).

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
already computed by each of the six validation stages (e.g. "Insufficient
OOS history: need at least 252 valid return rows; got 150.", or a
data-quality fatal-check summary), plus — only when the underlying
validation call itself raised — one additional top-level message:

- `Provider unavailable: {message}` when the validation call failed with
  HTTP 502 (market-data provider failure).
- `Historical execution failed: {message}` for any other validation
  failure (e.g. insufficient full-history sample).

No blocker is invented; every string is either produced by
`ResearchValidationService` or is a fixed, literal wrapper around its
error message.

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

`ResearchEvaluationPanel` renders an enterprise governance dashboard, not a
trading UI:

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
`ResearchValidationService` fixture adapter PR-009 already tests against.
