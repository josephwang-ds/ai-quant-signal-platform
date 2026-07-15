# Authenticity Policy — Research Workspace

## Purpose

The public Research Workspace must not imply that fictional research was
performed or that invented market metrics are real results.

This policy governs static demo metadata versus calculated evidence.

## Canonical reference research

**MA Crossover Research** (`ma-crossover-spy`)

| Field | Value |
| --- | --- |
| Symbol | SPY |
| Benchmark | SPY Buy & Hold |
| Strategy | Moving Average Crossover |
| Short window | 20 |
| Long window | 60 |
| Transaction cost | 0.001 per position change |

Source of truth: `frontend/lib/canonicalMaCrossover.ts`

## Allowed static demo metadata

- Research name, question, hypothesis, and objective
- Strategy definition and configured parameters
- Symbol and benchmark labels
- Planned experiment definitions (protocol only)
- Planned validation stage names and pending statuses
- Notebook entries clearly labeled as research design / planning notes
- Product timeline events such as definition created, methodology documented,
  real-data integration planned
- Desk / workspace ownership labels that are not fabricated individual
  researcher biographies

## Must come from real calculations (Research Execution Engine)

- Returns, Sharpe, CAGR, volatility, maximum drawdown
- Win rate, trade count, transaction-cost totals
- Benchmark comparison results
- Out-of-sample outcomes and sensitivity grid numbers
- Validation pass / fail / inconclusive outcomes
- Evaluation / Research Confidence scores and recommendations
- Any claim that a backtest or validation “completed” with numeric evidence

Until those exist: fields are **null**, **Not Calculated**, **Not Started**,
**Awaiting Data**, or **Not Available** — never fabricated.

## Why fabricated financial metrics are prohibited

Invented Sharpes and confidence scores create false trust. This product is a
research operating system oriented toward evidence and reproducibility. Fake
performance undermines governance and demos a credibility failure.

## Unavailable-data behavior

- Explain **why** a field is unavailable
- State **what** will populate it (Research Execution Engine / real history)
- Preserve the label: `Research Definition — Calculated results pending` until
  execution succeeds
- Never fall back to demo numbers when a provider is unavailable
- Provider-unavailable UI must remain non-fabricating

## PR-008B real-data boundary

PR-008B attaches runtime market data and calculated MA20/60 evidence to the same
canonical research id via `POST /api/v1/research/execution`.

Rules that remain in force:

- Domain / Application own calculations; Infrastructure owns providers
- Presentation never calls Yahoo Finance and never invents fallback metrics
- Under PR-008B alone, only Historical Backtest and Benchmark Comparison may
  become Completed; PR-009 extends this only through backend validation evidence
- Evaluation / Research Confidence stay unavailable without OOS, sensitivity,
  cost, stress, and data-quality evidence
- See `docs/slices/research-execution.md` for contracts, conventions, and cache

## PR-009 validation-evidence boundary

PR-009 may mark Historical Backtest, Same-Asset Benchmark Comparison,
Chronological OOS, bounded Parameter Sensitivity, Transaction-Cost
Sensitivity, and Data-Quality Review according to deterministic backend stage
results.

This evidence does not establish a final Validation Pass or robustness
conclusion. Stress testing, regime analysis, full robustness evaluation,
Evaluation, Research Confidence, and readiness recommendations remain
unavailable. See `docs/slices/research-validation.md`.

## PR-010 evaluation-governance boundary

PR-010 adds `POST /api/v1/research/evaluation`, which **summarizes** PR-009
validation evidence (evidence coverage, completed/incomplete/unavailable
stages, blockers, limitations, outstanding evidence). It performs no
calculations of its own and introduces no new numeric evidence.

Rules that remain in force:

- Allowed `evaluation_status` values are only `completed`, `incomplete`, or
  `blocked` — never a quality, robustness, or investment judgement.
- No Research Confidence score, star rating, quality grade, or buy/sell
  recommendation is shown anywhere in the Evaluation view.
- Evidence coverage is implementation completeness only, never confidence.
- Stress testing, regime analysis, walk-forward validation, Monte Carlo
  simulation, Publish Strategy, and Paper Trading remain unavailable and
  are listed as outstanding evidence, not as pending scores.
- See `docs/slices/research-evaluation.md`.

## PR-011A remediation — public preview modules

An internal audit (`docs/reviews/RC-1-REPOSITORY-AUDIT.md`) found that six
"adjacent" public preview routes rendered fabricated evidence from
`frontend/lib/mockQuantData.ts` — a hardcoded Sharpe ratio (1.12), max
drawdown (-8.6%), hit rate (0.58), a "Strategy Health Score" of 76/100 with
fabricated pillar scores, simulated governance verdicts ("Approved with
caution", "Approved — size capped", "Downgraded to WATCH"), and `BUY`/`SELL`
signal strings with no real backend evidence behind them. This directly
violated the rule above ("fabricated financial metrics are prohibited") even
though it sat outside the canonical `ma-crossover-spy` research path.

Remediated modules — each now renders an honest `WorkspacePlaceholder`
("Planned Capability" state) instead of any simulated metric or verdict:

- Strategy Health Score (`/strategy-health-score`)
- Return Quality Lens (`/return-quality-lens`)
- Risk Gate Review (`/risk-gate-review`)
- Scenario Shock Test (`/scenario-shock-test`)
- Decision Ledger (`/decision-ledger`)
- Decision Room (`/decision-room`)

`frontend/lib/mockQuantData.ts` and the two dead-code components that only
it fed (`ExecutiveCockpitGrid`, `ExecutiveCockpitSnapshot`, both already
unreachable from any route) were deleted outright, along with the
translation-dictionary entries in `frontend/lib/i18n.ts` that only existed
to translate that fabricated copy. No replacement numbers were invented —
these modules show **no score, no signal, and no verdict** until they are
backed by real Research Execution / Validation / Evaluation evidence. See
`frontend/lib/publicPreviewAuthenticity.test.ts` for the regression tests
that keep this true.

The `/overview` route's title and description previously said "Executive
Cockpit" / described a "risk governance, return quality, and audit trail"
view, even though the page itself only ever rendered the honest workspace
module directory (`WORKSPACE_MODULES`). That mismatched branding was
corrected to "Workspace Overview" to describe what the page actually shows.

## Research Copilot (PR-012)

The Research Copilot is an **interpretation layer only**. It may explain
evidence already produced by Execution, Validation, and Evaluation, plus
approved documentation chunks and structured notebook context.

The Copilot must not:

- calculate new financial metrics
- invent Sharpe, CAGR, drawdown, win rate, trade count, or validation status
- recommend BUY, SELL, HOLD, position size, or allocation
- claim a strategy is approved, robust, safe, or profitable
- present a mock or canned answer as if it were model-generated when the
  provider is unavailable

Provider API keys remain backend-only (`OPENAI_API_KEY`, `COPILOT_MODEL`).
Never expose keys through `NEXT_PUBLIC_*` variables or call OpenAI/Anthropic
from the frontend. Offline tests use `FakeLlmAdapter`; production without a
key returns HTTP 503 and the UI shows "Research Copilot is not configured
for this deployment."
