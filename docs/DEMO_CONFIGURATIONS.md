# Canonical Demo Configurations

Reproducible historical research definitions for interview and portfolio demos.
Metrics are **never** stored here — they are produced by calculation engines at
runtime. If market data is unavailable, the UI shows an honest error state.

## Where defaults live

| Study | Source of truth |
| --- | --- |
| Trend Following | `frontend/lib/canonicalMaCrossover.ts` |
| Cross-Sectional Momentum | `frontend/lib/canonicalCrossSectionalFactor.ts` (`CANONICAL_MOMENTUM_*`) |
| Cross-Sectional Low Volatility | same file (`CANONICAL_LOW_VOL_*`) |
| Catalog projection | `frontend/lib/mockResearchCatalog.ts` |

Update protocol fields in the canonical modules, then re-check
`assertCanonicalCatalog()` and authenticity tests.

## A. Trend Following Study (`ma-crossover-spy`)

| Field | Value |
| --- | --- |
| Symbol | SPY |
| Benchmark | Buy and Hold (same asset) |
| Start | 2018-01-01 |
| End | latest complete trading day from the market-data provider |
| Short / Long MA | 20 / 60 |
| Transaction cost | 0.001 per position change |

Label: reproducible historical demonstration — not a live strategy.

## B. Cross-Sectional Momentum Factor Study (`cross-sectional-factor-sector-etfs`)

| Field | Value |
| --- | --- |
| Universe | `us_sector_etfs` |
| Factor | Momentum (12-1) |
| Rebalance | Monthly |
| Holding period | 1 month |
| Transaction cost | 0.001 × long–short turnover |
| Start | 2018-01-01 |
| End | provider boundary |

## C. Cross-Sectional Low Volatility Factor Study (`cross-sectional-low-vol-sector-etfs`)

Same universe, dates, rebalance, holding, and cost as Momentum.
Factor: Low Volatility (−60d realized vol; higher score = lower vol).

## Decision templates (human-authored only)

Suggested rationales after **calculated** validation exists. Do not pre-seed
metric claims. Examples:

- Momentum Hold: “Historical cross-sectional evidence is directionally positive, but stability and cost sensitivity require further observation.”
- Low Volatility Hold/Reject: “The factor does not demonstrate sufficiently stable cross-sectional evidence across the evaluated period.” (use only if calculated evidence supports that reading)

## Regression fixtures

Deterministic baselines under `backend/tests/fixtures/` protect calculation
behavior. They do **not** guarantee future market performance. See
`docs/KNOWN_LIMITATIONS.md`.
