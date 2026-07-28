"""Factor family registry for the cross-sectional dataset."""

from __future__ import annotations

import pandas as pd

from app.cross_sectional.constants import DEFAULT_LIQUIDITY_DOLLAR_VOLUME_FLOOR, FACTOR_COLUMNS
from app.cross_sectional.factors.momentum import compute_momentum_factors
from app.cross_sectional.factors.risk import compute_risk_factors
from app.cross_sectional.factors.volume import compute_volume_factors


def compute_all_factors(
    close: pd.Series,
    volume: pd.Series,
    *,
    liquidity_dollar_volume_floor: float = DEFAULT_LIQUIDITY_DOLLAR_VOLUME_FLOOR,
) -> pd.DataFrame:
    """Compute the Phase-1 factor set for one symbol's sorted series."""
    momentum = compute_momentum_factors(close)
    risk = compute_risk_factors(close)
    volume_f = compute_volume_factors(
        close,
        volume,
        liquidity_dollar_volume_floor=liquidity_dollar_volume_floor,
    )
    frame = pd.concat([momentum, risk, volume_f], axis=1)
    missing = [col for col in FACTOR_COLUMNS if col not in frame.columns]
    if missing:
        raise RuntimeError(f"Factor registry missing columns: {missing}")
    return frame.loc[:, list(FACTOR_COLUMNS)]
