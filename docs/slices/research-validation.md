# Research Validation (PR-009)

## Outcome

`POST /api/v1/research/validation` produces deterministic validation evidence
for the canonical `ma-crossover-spy` research. It reuses PR-008B's
`MarketDataPort`, normalized OHLCV series, provenance, cache behavior, and
MA-crossover calculations. One normalized price download feeds every stage.

This slice reports evidence completeness; it does not create a final Validation
Pass, Robustness conclusion, Evaluation, Research Confidence, or readiness
recommendation.

## Request

```json
{
  "research_id": "ma-crossover-spy",
  "symbol": "SPY",
  "benchmark": "SPY",
  "start_date": "2018-01-01",
  "end_date": null,
  "short_window": 20,
  "long_window": 60,
  "transaction_cost": 0.001,
  "risk_free_rate": 0,
  "in_sample_ratio": 0.7
}
```

PR-009 retains the PR-008B same-asset benchmark rule: `benchmark` must equal
`symbol`. Independent benchmark downloads remain deferred.

## Response

The response contains:

- strategy configuration and source provenance;
- `validation_status` (`completed`, `incomplete`, or `failed`);
- `evidence_complete` (true only when every implemented stage completed);
- six ordered `stages`, each with status, summary, evidence, deterministic
  rules, warnings, blockers, generation time, and provenance;
- structured OOS, parameter-sensitivity, cost-sensitivity, and data-quality
  results.

No response value may be NaN or Infinity. A mathematically undefined metric is
`null` with a warning.

## Chronological OOS methodology

1. Sort and validate the normalized daily series.
2. Compute the split index as `floor(observation_count * in_sample_ratio)`.
3. Use the first raw observation at that index as the OOS boundary.
4. Run MA20/60 once on the full series, preserving all pre-OOS observations for
   moving-average warm-up.
5. Evaluate in-sample return rows with date before the boundary and OOS return
   rows on or after it.

There is no shuffle and no OOS optimization. Fixed MA parameters are unchanged.
The minimum valid OOS sample is `max(60, long_window)` rows. A smaller sample
produces `incomplete`, not fabricated metrics.

### Split-boundary position and cost

The first OOS position is the prior trading day's signal from the full-series
run. Its turnover compares that position with the final in-sample position.
Therefore a genuine entry or exit at the boundary incurs the configured cost.
Segment cumulative returns are rebased to 1.0 for segment-only metrics, while
the underlying position and turnover state are not reset.

## Parameter sensitivity

The bounded, deterministically ordered grid is:

- short windows: `10, 20, 30`;
- long windows: `50, 60, 100`;
- combinations where `short < long` only.

Every combination uses the same normalized series and configured transaction
cost. MA20/60 is marked canonical. The descriptive summary reports valid and
profitable counts, positive-Sharpe count, medians, ranges, and the canonical
Sharpe percentile. It neither selects a best strategy nor recommends a
parameter set.

## Transaction-cost sensitivity

Canonical MA20/60 is evaluated at `0`, `0.001`, `0.002`, and `0.005` per unit
turnover. Results include return and Sharpe degradation relative to the
zero-cost case, plus the canonical-cost result. No profitability-only pass/fail
rule is applied.

## Data-quality review

Fatal contract checks:

- empty data;
- missing required columns;
- duplicate or invalid dates;
- non-positive prices;
- insufficient full history;
- insufficient valid rows after warm-up.

Non-fatal limitations include filled volume, stale cache, short coverage,
adjusted-close fallback, provider limitations, and approximate missing weekday
intervals. Interval detection does not claim exchange-calendar knowledge.

Informational evidence includes provider, source, symbol, requested/actual
range, observation count, cache state, and retrieval timestamp.

Provider warnings do not become failures automatically. Non-fatal limitations
make the data-quality stage `incomplete`; fatal contract violations make it
`failed` or prevent execution at the API boundary.

## Stage status rules

- Historical backtest: completed after successful baseline calculation.
- Benchmark comparison: completed when same-asset benchmark metrics exist.
- OOS: completed with sufficient valid OOS rows; incomplete when insufficient;
  failed only on calculation failure.
- Parameter sensitivity: completed when all valid combinations execute;
  incomplete when only some execute; failed when none execute.
- Cost sensitivity: completed when all levels execute; incomplete when only
  some execute; failed when none execute.
- Data quality: completed without limitations; incomplete for non-fatal
  limitations; failed for fatal issues.

Overall status is `failed` if any stage failed, `incomplete` if any stage is
incomplete or unavailable, otherwise `completed`.

## Limitations

Yahoo Finance remains research/demo grade, not exchange grade. This slice does
not implement stress testing, regime analysis, walk-forward optimization,
parameter selection, independent benchmarks, full robustness evaluation,
Evaluation, Research Confidence, Publish Strategy, or portfolio eligibility.
Positive returns or Sharpe do not establish robustness or future performance.

## Local verification

```bash
cd backend
PYTHONPATH=. python3 -m pytest tests/test_research_validation.py -v

cd ../frontend
npm test -- --run
npm run build
```

The backend fixture suite is offline and uses
`backend/tests/fixtures/spy_daily_sample.csv`.

Measured locally on 2026-07-14, one default fixture validation (one data read,
one baseline, nine parameter runs, and four cost runs) completed in
`0.050433` seconds. This is a development measurement, not an SLO.
