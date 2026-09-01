"""A time-series foundation model on the volatility task, cached and optional.

Chronos-2 is a pretrained probabilistic forecaster: it takes a numeric series and
returns quantiles for the next h steps, with no fitting on this data at all. That
zero-shot property is what makes it interesting here and also what makes it easy
to misuse, so two things are pinned down before it is allowed near the evidence.

**What it is given, and why that is the whole design.** The input is the issuer's
trailing 20-session realized-volatility series, ending at the session *before*
entry. Forecast twenty steps and the last one is the trailing-20 volatility at
`anchor + 19`, which is realized volatility over the target window exactly. The
question the model is asked is therefore the question being scored -- not a proxy
that has to be converted afterwards, where the conversion is where errors hide.

**Zero-shot does not mean leak-free.** The model's weights were fitted on public
time series before this sample and are frozen, so there is no fold to purge on
the model's side. What still has to hold is that its *input* stops before the
target window, and `VolatilityPanel.trailing_series` is where that is enforced.
A context that ran one session too far would be undetectable in the metrics --
it would simply look like a very good forecaster.

**Optional, and cached like the text model.** Without `torch` and
`chronos-forecasting` this module reports itself unavailable, the evidence export
reports the baselines alone, and nothing else changes. With them, one pass writes
a cache keyed by model, revision, horizon and a digest of the context series;
nothing downstream loads a model again.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from filing_triage.volatility import HORIZON, QUANTILES

# Pinned. "The Chronos forecast" is not a stable description of anything
# without a model id and a revision, and both are part of the cache key.
MODEL_ID = "amazon/chronos-2"
MODEL_REVISION = "main"
BATCH_SIZE = 64
# The model reads at most this much history. Longer contexts cost time without
# adding information at a 20-session horizon.
CONTEXT_LENGTH = 512

# Forecast log volatility and exponentiate, rather than working in levels.
#
# This is not a tweak; it is what makes the comparison fair. Every baseline here
# works in logs, because realized volatility is bounded below by zero and roughly
# log-normal. Handing the foundation model raw levels while the baselines get
# logs would be handicapping the challenger and then reporting that it lost.
#
# Measured both ways on the full sample, logs are also the model's own better
# configuration: pinball 0.0298 against 0.0302, and 80% coverage 75.5% against
# 74.1%. So this is the version the evidence reports -- a negative result is only
# worth stating if the thing that lost was given its best shot.
LOG_SPACE = True


def available() -> bool:
    """Whether the optional stack is installed, without importing it eagerly."""
    from importlib.util import find_spec

    return (find_spec("torch") is not None
            and find_spec("chronos") is not None)


def context_key(context: np.ndarray, horizon: int = HORIZON) -> str:
    """Cache key for one forecast: model, revision, horizon and the series.

    Digesting the series itself rather than the issuer and date means a corrected
    price bar changes the key, so a re-ingest cannot silently reuse a forecast
    made from the old numbers.
    """
    rounded = np.round(np.asarray(context, dtype=float), 8)
    digest = hashlib.sha256(
        f"{MODEL_ID}@{MODEL_REVISION}\x1e{horizon}\x1e{LOG_SPACE}\x1e".encode()
        + rounded.tobytes()
    ).hexdigest()
    return digest[:32]


@dataclass
class ForecastCache:
    """Quantile forecasts on disk, keyed by model and by content.

    One JSON file: five floats per event is small enough that the readability of
    a plain index is worth more than the space a binary format would save.
    """

    path: Path

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self.path.mkdir(parents=True, exist_ok=True)
        self._index_path = self.path / "index.json"
        self.index = (json.loads(self._index_path.read_text())
                      if self._index_path.exists() else self._empty())
        if (self.index.get("model") != MODEL_ID
                or self.index.get("revision") != MODEL_REVISION
                or self.index.get("log_space") != LOG_SPACE
                or self.index.get("quantiles") != list(QUANTILES)):
            # A cache made by another model, or scored at other quantile levels,
            # is not this configuration's cache. Start clean rather than mix.
            self.index = self._empty()

    @staticmethod
    def _empty() -> dict:
        return {"model": MODEL_ID, "revision": MODEL_REVISION,
                "horizon": HORIZON, "log_space": LOG_SPACE,
                "quantiles": list(QUANTILES), "keys": {}}

    def __contains__(self, key: str) -> bool:
        return key in self.index["keys"]

    def get(self, key: str) -> dict[float, float]:
        return dict(zip(QUANTILES, self.index["keys"][key], strict=True))

    def add(self, key: str, quantiles) -> None:
        self.index["keys"][key] = [round(float(v), 6) for v in quantiles]

    def save(self) -> None:
        self._index_path.write_text(json.dumps(self.index, indent=1))

    def fingerprint(self) -> dict:
        return {"model": MODEL_ID, "revision": MODEL_REVISION,
                "horizon": HORIZON, "context_length": CONTEXT_LENGTH,
                "log_space": LOG_SPACE, "forecasts": len(self.index["keys"])}


def _prepare(context: np.ndarray) -> np.ndarray:
    """The last `CONTEXT_LENGTH` observations, in the space the model forecasts in."""
    window = np.asarray(context[-CONTEXT_LENGTH:], dtype=np.float32)
    if not LOG_SPACE:
        return window
    # Guarded rather than assumed positive: a zero-volatility session would make
    # the log infinite, and one infinity poisons the whole batch silently.
    return np.log(np.maximum(window, 1e-8))


def forecast(contexts: list[np.ndarray], cache: ForecastCache, *,
             horizon: int = HORIZON, progress: bool = False) -> None:
    """Fill the cache for any context it does not already hold.

    Loads the model only when there is work, so a rerun over unchanged prices
    never touches torch.
    """
    missing: dict[str, np.ndarray] = {}
    for context in contexts:
        key = context_key(context, horizon)
        if key not in cache and key not in missing and len(context) >= 64:
            missing[key] = context
    if not missing:
        return
    if not available():
        raise RuntimeError(
            "chronos-forecasting and torch are required to build the forecast "
            "cache; install the optional group with `pip install -e '.[ts]'`"
        )

    from chronos import BaseChronosPipeline

    pipeline = BaseChronosPipeline.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
    keys = list(missing)
    for start in range(0, len(keys), BATCH_SIZE):
        batch = keys[start:start + BATCH_SIZE]
        inputs = [_prepare(missing[k]) for k in batch]
        quantiles, _ = pipeline.predict_quantiles(
            inputs, prediction_length=horizon, quantile_levels=list(QUANTILES))
        for key, tensor in zip(batch, quantiles, strict=True):
            # [item, step, quantile]; the last step is the horizon being scored,
            # where the trailing window covers exactly the target sessions.
            values = tensor[0, horizon - 1, :].numpy()
            cache.add(key, np.exp(values) if LOG_SPACE else values)
        if progress:
            print(f"  forecast {min(start + BATCH_SIZE, len(keys)):,}"
                  f" / {len(keys):,}", flush=True)
    cache.save()


def cached_forecast(context: np.ndarray, cache: ForecastCache,
                    horizon: int = HORIZON) -> dict[float, float]:
    """One event's quantiles, or all-NaN when the context was never forecast."""
    key = context_key(context, horizon)
    if key not in cache:
        return dict.fromkeys(QUANTILES, float("nan"))
    return cache.get(key)
