# ADR-0008: Factor Validation Engine and Cross-Sectional Factor Study

**Status:** Accepted  
**Date:** 2026-07-24  
**Deciders:** Research platform team  

## Context

The Research Workspace ships one executable template: Trend Following Study
(MA crossover). Product needs a second template — **Cross-Sectional Equity
Factor Study** — as a factor **validation** workflow (not a trading strategy,
not portfolio optimization, not a broker).

Validation evidence for factors is conventionally RankIC / ICIR and
equal-weight quantile portfolios (Q1–Q5) with long–short, turnover, and
stated transaction costs. These must be deterministic pure calculations,
never LLM-invented metrics.

## Decision

1. Add a Validation-context package `backend/app/factor_validation/` with
   pure-calc modules (`rank_ic`, `quantile_portfolios`) that take Universe,
   monthly factor panels, and forward returns — **no** market-data or FastAPI
   imports inside the engines.
2. Add additive route `POST /api/v1/research/factor-validation`. Do **not**
   change existing MA `/api/v1/research/validation` contracts.
3. Introduce research template id `cross_sectional_factor` alongside
   `trend_following`. Shared lifecycle spine
   (Research → Experiment → Validation → Robustness → Decision) stays;
   evidence panels fork by template.
4. v1 universe preset: `us_sector_etfs` (sector ETFs via existing MarketDataRouter).
5. Executable factors: **Momentum** (12-1), **Low Volatility** (−60d vol).
   **Value** is Coming Soon (API reject / UI disabled).
6. Quantile convention: five equal-count buckets; high factor → Q5; ties broken
   by stable symbol sort. Long–short = Q5 − Q1 period returns (gross). Turnover for LS
   book: `0.5 × Σ|w_t − w_{t−}|` with first rebalance treated as full build
   (`0.5 × Σ|w_t|`). Cost = turnover × cost_rate (default 0.001). Net LS subtracts
   that cost from each period return before compounding — never a fixed fictional
   deduction.
7. RankIC: Spearman; ICIR = mean(IC)/std(IC, ddof=1); rolling IC = 12-month
   trailing mean. Insufficient sample → skip period or null summary fields —
   never invent. AI / Copilot never computes RankIC or quantile evidence.
8. Persist factor-validation payloads through `ValidationResultStore` and
   return `validation_run_id`. Factor run IDs must not be fed into the MA
   Evaluation / Copilot path (different evidence shape).
9. No optimization, risk model, borrow model, or broker connectivity.
10. **Feature Interpretation** (Compare Models diagnostic): coefficient /
    permutation / optional SHAP after fit; does not change predictions or
    backtest metrics. SHAP remains optional (`shap` package). Importance is
    not causality.

## Consequences

### Positive

- Second research template without breaking MA authenticity path.
- Reusable, unit-testable IC and quantile engines.
- Clear separation: calculation vs interpretation (Copilot).

### Negative

- Sector-ETF universe is a demo cross-section, not a production equity universe.
- Value and richer universes deferred.

## Alternatives considered

- **Extend MA validation stages with factor metrics** — rejected; different
  evidence shape and would couple templates.
- **LLM-computed IC summaries as product truth** — rejected; authenticity policy.
- **Optimized / risk-model portfolios** — rejected; out of scope.

## Related

- `docs/data/AUTHENTICITY_POLICY.md`
- ADR-0007 Market data router
- Research Copilot slice (evidence-only interpretation)
