"""Forward-return labels — never used as feature inputs."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.cross_sectional.constants import LABEL_COLUMNS


def _clean_numeric(series: pd.Series) -> pd.Series:
    out = pd.to_numeric(series, errors="coerce")
    return out.replace([np.inf, -np.inf], np.nan)


def compute_forward_labels(close: pd.Series) -> pd.DataFrame:
    """
    Attach forward returns using future prices.

    ``forward_return_Nd[t] = P[t+N] / P[t] - 1``.
    Trailing rows without a complete forward window remain null.
    """
    px = _clean_numeric(close)
    out = pd.DataFrame(index=px.index)
    out["forward_return_5d"] = px.shift(-5) / px - 1.0
    out["forward_return_20d"] = px.shift(-20) / px - 1.0
    out = out.replace([np.inf, -np.inf], np.nan)
    missing = [col for col in LABEL_COLUMNS if col not in out.columns]
    if missing:
        raise RuntimeError(f"Label builder missing columns: {missing}")
    return out.loc[:, list(LABEL_COLUMNS)]
