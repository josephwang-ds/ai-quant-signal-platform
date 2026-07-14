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
