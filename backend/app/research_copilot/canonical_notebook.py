"""Static canonical notebook context mirrored from the MA Crossover definition."""

from __future__ import annotations

CANONICAL_RESEARCH_ID = "ma-crossover-spy"

CANONICAL_DEFINITION = {
    "research_id": CANONICAL_RESEARCH_ID,
    "name": "MA Crossover Research",
    "research_question": (
        "Does a simple MA20/MA60 crossover outperform SPY buy-and-hold after "
        "transaction costs over a long historical period?"
    ),
    "hypothesis": (
        "A medium-term moving-average crossover may reduce large drawdowns, "
        "but its performance advantage may weaken after transaction costs and "
        "during sideways markets."
    ),
    "symbol": "SPY",
    "benchmark": "SPY Buy & Hold",
    "strategy": "Moving Average Crossover",
    "parameters": {
        "short_window": 20,
        "long_window": 60,
        "transaction_cost": 0.001,
        "position_lag_days": 1,
        "start_date": "2018-01-01",
    },
}

NOTEBOOK_ENTRIES: tuple[dict[str, str], ...] = (
    {
        "id": "nb-ma-001",
        "entry_type": "Observation",
        "title": "Research question framed",
        "body": (
            "Define whether MA20/MA60 on SPY can outperform SPY buy-and-hold "
            "after a 0.001 cost on each position change. Scope only — no "
            "performance calculated in this entry."
        ),
    },
    {
        "id": "nb-ma-002",
        "entry_type": "Hypothesis",
        "title": "Primary hypothesis (design)",
        "body": (
            "A medium-term moving-average crossover may reduce large drawdowns, "
            "but its advantage may weaken after transaction costs and during "
            "sideways markets."
        ),
    },
    {
        "id": "nb-ma-003",
        "entry_type": "Methodology",
        "title": "Look-ahead and position-lag protocol",
        "body": (
            "Signals use completed bars only. Positions apply with a one-day lag "
            "so same-day closes cannot be traded. Transaction costs apply only "
            "when position changes."
        ),
    },
)
