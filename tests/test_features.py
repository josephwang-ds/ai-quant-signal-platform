from __future__ import annotations

from datetime import date

import pandas as pd

from filing_triage.config import PipelineConfig
from filing_triage.features import _issuer_state_features, _novelty_features


def test_future_documents_cannot_change_earlier_novelty() -> None:
    first_two = pd.DataFrame({
        "ticker": ["ABC", "ABC"],
        "text": ["quarterly earnings revenue", "quarterly earnings revenue increased"],
    })
    with_future = pd.concat([
        first_two,
        pd.DataFrame({
            "ticker": ["ABC"] * 10,
            "text": [f"future document unrelated topic {index}" for index in range(10)],
        }),
    ], ignore_index=True)

    before = _novelty_features(first_two)
    after = _novelty_features(with_future).iloc[:2]

    pd.testing.assert_frame_equal(before, after)
    assert before.iloc[0]["novelty"] == 0.5
    assert before.iloc[0]["first_filing"] == 1


def test_missing_trailing_state_is_preserved_for_native_model_handling() -> None:
    dates = pd.bdate_range("2024-01-02", periods=4)
    returns = pd.DataFrame({
        "ticker": ["ABC"] * 4,
        "date": [value.date() for value in dates],
        "ret": [0.01, -0.01, 0.02, 0.01],
        "close": [100.0, 99.0, 101.0, 102.0],
        "volume": [1000.0, 1100.0, 900.0, 1200.0],
        "volume_median_60": [float("nan")] * 4,
    })
    events = pd.DataFrame({
        "ticker": ["ABC"],
        "entry_session": [date(2024, 1, 5)],
    })

    features = _issuer_state_features(events, returns, PipelineConfig())

    assert features.isna().all(axis=None)
