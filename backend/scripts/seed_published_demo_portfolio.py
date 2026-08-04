#!/usr/bin/env python3
"""Compatibility wrapper for Portfolio publication seed.

Preferred invocation:

    python -m app.portfolio.seed_published_portfolio --manifest path.json --dry-run
"""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.portfolio.seed_published_portfolio import main


if __name__ == "__main__":
    raise SystemExit(main())
