"""Factor validation package — pure calculation engines (no I/O)."""

from app.factor_validation.rank_ic import (
    ROLLING_IC_WINDOW,
    compute_rank_ic_series,
    rolling_ic,
    summarize_ic,
)
from app.factor_validation.quantile_portfolios import (
    QUANTILE_COUNT,
    compute_quantile_portfolios,
)

__all__ = [
    "ROLLING_IC_WINDOW",
    "QUANTILE_COUNT",
    "compute_rank_ic_series",
    "summarize_ic",
    "rolling_ic",
    "compute_quantile_portfolios",
]
