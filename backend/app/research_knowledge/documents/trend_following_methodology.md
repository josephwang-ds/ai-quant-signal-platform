# Trend Following Methodology
knowledge_id: kb.trend_following.v1
topic: methodology
research_type: trend_following

Trend following MA research uses completed bars only with a one-day position lag. Buy-and-Hold is the primary benchmark. Validation includes OOS chronological split, fixed-parameter chronological walk-forward, parameter sensitivity, transaction-cost sensitivity, and data-quality checks. Do not treat in-sample Sharpe as proof of robustness. Walk-forward uses fixed MA20/MA60 parameters and is not per-fold retuning.
