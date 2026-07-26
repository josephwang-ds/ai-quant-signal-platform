# Walk-Forward Methodology
knowledge_id: kb.walk_forward.v1
topic: robustness
research_type: trend_following

Canonical trend walk-forward evaluates fixed MA20/MA60 parameters on chronological OOS folds. Expanding and rolling history windows are supported. Time series are never shuffled. Parameters are not reselected inside each fold.

Default protocol uses 3–5 OOS folds (default 4). Each fold records warm-up, train start/end, OOS start/end, strategy return, benchmark return, Sharpe, max drawdown, and trades. Aggregates report completed fold count, positive-return fold ratio, benchmark-outperformance fold ratio, median OOS return, median OOS Sharpe, and worst OOS drawdown.

Failed folds remain in evidence and are not silently dropped. Insufficient history returns unavailable/insufficient_data. Thresholds live in versioned methodology config `wf.trend_ma_crossover.v1`.

Walk-forward reduces but does not eliminate overfitting risk. It does not represent future returns. Fixed-parameter walk-forward is not the same as per-fold parameter tuning. Compare Models walk-forward is a separate ML evaluation path and must not be substituted for this canonical trend robustness evidence.
