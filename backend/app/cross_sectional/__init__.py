"""Cross-sectional factor dataset package (Phase 1).

Additive Research/Market Intelligence utilities. Does not replace
``factor_validation`` (ADR-0008) or Trend Following execution.
"""

from app.cross_sectional.constants import (
    FACTOR_COLUMNS,
    FACTOR_VERSION,
    LABEL_COLUMNS,
    UNIVERSE_ID_LIQUID_31,
    UNIVERSE_ID_LIQUID_50,
)
from app.cross_sectional.universe import resolve_universe

__all__ = [
    "FACTOR_COLUMNS",
    "FACTOR_VERSION",
    "LABEL_COLUMNS",
    "UNIVERSE_ID_LIQUID_31",
    "UNIVERSE_ID_LIQUID_50",
    "resolve_universe",
]
