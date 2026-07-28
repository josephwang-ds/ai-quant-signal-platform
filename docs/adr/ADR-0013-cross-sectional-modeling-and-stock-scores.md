# ADR-0013: Cross-Sectional Modeling and Stock Scores (Phase 3)

- **Status:** Accepted
- **Date:** 2026-07-28
- **Deciders:** Research / Validation maintainers

## Context

Phase 1 delivers a point-in-time factor panel. Phase 2 evaluates individual factors (RankIC, quantiles, turnover). Phase 3 asks whether a **multivariate model** improves **cross-sectional ranking** beyond single-factor evidence — without constructing a portfolio.

## Decision

Add an additive package `backend/app/cross_sectional/modeling/` that:

1. Consumes the Phase 1 panel via `CrossSectionalDatasetService.load_panel` (no HTTP panel dump).
2. Applies **model eligibility** separate from Phase 2 factor eligibility (complete-case on the **selected** feature set + label).
3. Uses **expanding walk-forward** chronological splits (no shuffle, no random CV).
4. Applies **label-horizon purging** so a training row’s full forward-return window ends before validation/prediction starts (trading-row semantics aligned with Phase 1 labels).
5. Fits **train-only** preprocessing (clipping + StandardScaler for Ridge; clip-only for LightGBM).
6. Trains exactly two families: **Ridge** (small alpha grid) and **LightGBM** (small fixed grid).
7. Selects hyperparameters with **validation-only** mean daily prediction RankIC (tie-break: median RankIC → positive-IC ratio → lower MAE → simpler model).
8. Emits long-form **out-of-sample** predictions with score/percentile/rank contract.
9. Evaluates OOS prediction RankIC (reusing Phase 2 Spearman primitive, not the Phase 2 service).
10. Compares models with descriptive evidence labels only (not deployment approval).

API: `POST /api/v1/research/cross-sectional/models`.

Artifacts: bounded summaries in process-local `ValidationResultStore` (restart loss). No model binaries over HTTP or in Git.

## Why additive and separate

| Boundary | Rationale |
|---|---|
| Separate from Phase 2 research | Phase 2 answers “does this factor rank?”; Phase 3 answers “does a multivariate model improve ranking?” Training does not belong in factor research services. |
| Separate from portfolio | Scores are evidence, not positions. Top-K, weights, costs, and backtests are Phase 4+. |
| Separate from `backend/app/models` | Existing models package is single-name next-day ML — different unit of analysis and product language. |

## Approved features and labels

Features: Phase 1 continuous factors only (`RESEARCH_FACTOR_COLUMNS`). `liquidity_eligible` may filter rows but is **not** a predictive feature.

Labels: exactly one of `forward_return_5d` or `forward_return_20d` per run.

## Unit of analysis

Row = `as_of_date × symbol`. Ranking and RankIC are computed **within date** (and within model). Dates are never pooled before RankIC.

## Ranking convention

- **Phase 3:** rank `1` = **highest** model score.
- **Phase 2:** quantile `Q1` = **lowest** factor value.

These must not be mixed silently.

## Completeness policy (trade-off)

First implementation uses **complete-case** eligibility for the selected feature set. This reduces sample size versus imputation but avoids inventing values and keeps leakage audits simple. Unselected columns do not affect eligibility. Zero-fill is not the default.

## Leakage controls

1. Chronological date groups never split across train/val/prediction.
2. Purge: `i_max = start_idx - purge_horizon - 1` where purge_horizon = label horizon (+ optional embargo rows).
3. Preprocessing fitted on train (selection) / purged refit history only.
4. Hyperparameters selected on validation only — never on test/OOS metrics.
5. Reported predictions are only fold prediction windows.

## Reproducibility wording

Claim: configuration reproducible; deterministic under recorded environment; best-effort environment capture. No byte-for-byte guarantee unless separately tested.

## Non-goals (Phase 3)

XGBoost/CatBoost/NN/RL, Optuna/AutoML, ranking objectives as product, PCA/SHAP, sector neutralization, ensembles, score calibration, Top-K, portfolio weights/costs/backtest, Sharpe/CAGR/drawdown, frontend modeling pages, LLM/agent training or approval, Promote/Hold/Reject automation.

## Consequences

- Phase 1/2 HTTP contracts unchanged.
- LightGBM remains a declared dependency (`lightgbm>=4.3,<5.0`); missing install fails clearly (no XGBoost substitute).
- Static-universe and survivorship limitations inherited from Phase 1 remain disclosed.
- Scores are **not** guaranteed expected returns; no causal claims.

## References

See `docs/references/REFERENCE-ARCHITECTURE-MAPPING.md` Phase 3 implementation mapping (Qlib score boundary; ML for Trading walk-forward/purge; Vibe-Trading run identity). Concepts reimplemented — no reference source copied into application modules.
