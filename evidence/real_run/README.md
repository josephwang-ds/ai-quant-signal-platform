# Real-run evidence

This directory contains the small, non-sensitive evidence package behind the
README's real-data claims. It was exported from ignored local inputs in
`data/build` with:

```bash
make run
make evidence
```

The raw SEC filing text and market-price panel are not committed.

Files:

- `manifest.json` — cutoff and validation configuration;
- `provenance.json` — data source, sample, and universe limitation;
- `metrics.json` — pooled and matched-session operational metrics;
- `fold_metrics.csv` — chronological out-of-sample stability;
- `oos_importance.csv` — permutation importance on held-out fold rows;
- `audit.csv` — leakage invariants from the honest pipeline;
- `leakage_study.csv` — cumulative correction ladder;
- `integrity.json` — impossible entries and measurement attrition;
- `baseline_intervals.csv` — paired session bootstrap of the model against each
  operational baseline, with the share of draws favouring the baseline;
- `reaction_capture.csv` — how much of each filing's reaction was already in the
  opening print, by materiality and acceptance window;
- `anchoring_study.csv` — the same pipeline scored against a close-anchored and
  an open-anchored label; and
- `hyperparameter_sensitivity.csv` — the headline rescored across a coarse grid
  around the estimator's defaults.

The filings are real, but the 193-issuer convenience universe is a survivor sample.
These results must not be presented as point-in-time index-universe evidence.
