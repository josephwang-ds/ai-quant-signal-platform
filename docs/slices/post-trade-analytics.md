# Post-Trade Analytics

> **Status:** Implemented demo slice  
> **Route:** `/post-trade`  
> **Boundary:** deterministic analytics only; no OMS, broker, exchange feed, or execution

## Purpose

This slice demonstrates two analytical workflows used to understand trading
performance and infrastructure health:

1. **Performance Attribution** — explain notional-weighted active PnL through
   gross edge versus benchmark, fees, and realized slippage.
2. **Anomaly Detection** — identify metric degradation using a past-only robust
   baseline.

The public page uses a deterministic synthetic fixture. The data is visibly and
structurally labeled `synthetic_demo`; it must never be described as live trading
activity.

## Interface research

The July 30, 2026 design review used active, high-adoption open-source projects
as references:

- [QuantStats](https://github.com/ranaroussi/quantstats) and
  [pyfolio](https://github.com/quantopian/pyfolio) organize performance work as
  tear sheets: a small KPI summary, benchmark-aware plots, drawdown or return
  views, and detailed tables.
- [Grafana](https://github.com/grafana/grafana) treats operational diagnosis as
  a time-series problem: observed values, thresholds, incident markers,
  annotations, and a state or event log.
- [VisualHFT](https://github.com/visualHFT/VisualHFT) reinforces the value of a
  dense execution-quality console for market-microstructure work rather than a
  promotional dashboard.
- [PyOD](https://github.com/yzhao062/pyod),
  [Kats](https://github.com/facebookresearch/Kats), and
  [ruptures](https://github.com/deepcharles/ruptures) provide a method ladder
  beyond a robust baseline: isolation-based detectors, time-series anomaly
  methods, and change-point detection.

The implemented page combines a tear-sheet attribution section with an
operations-style latency monitor. It deliberately avoids gradients, oversized
marketing copy, chatbot language, generated recommendations, and unexplained
scores. The result keeps the evidence visible: formula, grouping, baseline,
threshold, score, and exception rows.

The detector roadmap is intentionally conservative:

1. rolling median/MAD with past-only observations (implemented);
2. CUSUM or PELT for persistent regime changes, benchmarked against the robust
   baseline;
3. a multivariate detector only when labeled incidents and stable evaluation
   data justify the additional complexity.

## Performance Attribution

For observation \(i\), the service converts basis points to USD with the
observation notional:

```text
gross_edge_i = notional_i × (gross_pnl_bps_i - benchmark_pnl_bps_i) / 10,000
fee_drag_i   = notional_i × fees_bps_i / 10,000
slippage_i   = notional_i × slippage_bps_i / 10,000
net_active_i = gross_edge_i - fee_drag_i - slippage_i
```

Portfolio-level basis-point values are derived from summed USD contributions
divided by summed notional. They are not simple averages. The output includes a
reconciliation error and venue or strategy grouping.

## Anomaly Detection

Observations are isolated by `(metric, entity)` and ordered by timestamp. Each
score uses only the preceding `baseline_window` observations:

```text
center = median(history)
scale  = 1.4826 × median(abs(history - center))
score  = (current - center) / scale
```

Standard deviation is used only when MAD is zero. A constant baseline followed
by a different value receives a bounded sentinel score. The configured
direction may be `high`, `low`, or `two_sided`.

This is a transparent detector, not a claim that one threshold fits every
exchange, protocol, latency distribution, or operational regime.

## API

```text
POST /api/v1/post-trade/attribution
POST /api/v1/post-trade/anomalies
```

Contracts: `backend/app/post_trade/schemas.py`  
Services: `backend/app/post_trade/service.py`  
Routes: `backend/app/api/routes/post_trade_analytics.py`

## Verification

```bash
cd backend
PYTHONPATH=. python -m pytest tests/test_post_trade_analytics.py -q

cd frontend
npm test -- --run \
  lib/postTradeAnalytics.test.ts \
  components/features/post-trade/PostTradeAnalyticsPage.test.tsx
```
