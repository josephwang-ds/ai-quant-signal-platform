from __future__ import annotations

import pytest

from filing_triage.synth import generate


@pytest.fixture(scope="session")
def world():
    """One small synthetic world, shared by every end-to-end test."""
    return generate(n_issuers=60, seed=11)
