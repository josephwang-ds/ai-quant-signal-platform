"""Train-only preprocessing for Ridge (and optional transforms)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from app.cross_sectional.modeling.constants import PREPROCESSING_VERSION


@dataclass
class PreprocessArtifacts:
    feature_order: list[str]
    clip_lower: dict[str, float] | None
    clip_upper: dict[str, float] | None
    scaler_mean: list[float] | None
    scaler_scale: list[float] | None
    fit_cutoff: str
    preprocessing_version: str
    zero_variance_features: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "feature_order": self.feature_order,
            "clip_lower": self.clip_lower,
            "clip_upper": self.clip_upper,
            "scaler_mean": self.scaler_mean,
            "scaler_scale": self.scaler_scale,
            "fit_cutoff": self.fit_cutoff,
            "preprocessing_version": self.preprocessing_version,
            "zero_variance_features": self.zero_variance_features,
        }


class TrainOnlyPreprocessor:
    """
    Fit clipping bounds + StandardScaler on training rows only.

    Uses verified raw continuous factors (no same-date CS z-score in v1).
    """

    def __init__(
        self,
        features: list[str],
        *,
        clip_q_low: float = 0.01,
        clip_q_high: float = 0.99,
        scale: bool = True,
    ) -> None:
        self.features = list(features)
        self.clip_q_low = clip_q_low
        self.clip_q_high = clip_q_high
        self.scale = scale
        self._lower: dict[str, float] = {}
        self._upper: dict[str, float] = {}
        self._scaler: StandardScaler | None = None
        self._zero_var: list[str] = []
        self._fit_cutoff = ""

    def fit(self, train: pd.DataFrame, *, fit_cutoff: str) -> "TrainOnlyPreprocessor":
        self._fit_cutoff = fit_cutoff
        self._lower = {}
        self._upper = {}
        self._zero_var = []
        for col in self.features:
            series = pd.to_numeric(train[col], errors="coerce").dropna()
            if series.empty:
                self._lower[col] = 0.0
                self._upper[col] = 0.0
                self._zero_var.append(col)
                continue
            self._lower[col] = float(series.quantile(self.clip_q_low))
            self._upper[col] = float(series.quantile(self.clip_q_high))
            if float(series.std(ddof=0)) == 0.0:
                self._zero_var.append(col)
        clipped = self._clip_frame(train)
        if self.scale:
            self._scaler = StandardScaler()
            self._scaler.fit(clipped[self.features].to_numpy(dtype=float))
        return self

    def transform(self, frame: pd.DataFrame) -> np.ndarray:
        clipped = self._clip_frame(frame)
        arr = clipped[self.features].to_numpy(dtype=float)
        if self.scale and self._scaler is not None:
            return self._scaler.transform(arr)
        return arr

    def _clip_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        out = frame.copy()
        for col in self.features:
            out[col] = pd.to_numeric(out[col], errors="coerce").clip(
                lower=self._lower[col], upper=self._upper[col]
            )
        return out

    def artifacts(self) -> PreprocessArtifacts:
        mean = None
        scale = None
        if self._scaler is not None:
            mean = [float(x) for x in self._scaler.mean_]
            scale = [float(x) for x in self._scaler.scale_]
        return PreprocessArtifacts(
            feature_order=list(self.features),
            clip_lower=dict(self._lower),
            clip_upper=dict(self._upper),
            scaler_mean=mean,
            scaler_scale=scale,
            fit_cutoff=self._fit_cutoff,
            preprocessing_version=PREPROCESSING_VERSION,
            zero_variance_features=list(self._zero_var),
        )
