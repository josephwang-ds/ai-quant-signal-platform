from __future__ import annotations

from pathlib import Path


def test_scheduled_refresh_updates_fundamentals_before_building_pages() -> None:
    script = Path("scripts/run_scheduled_refresh.sh").read_text(encoding="utf-8")

    fundamentals = script.index("scripts/refresh_fundamentals.py")
    page_build = script.index("scripts/build_company_pages.py")
    assert fundamentals < page_build
    assert "COMPANY_LENS_FUNDAMENTALS_TICKERS:-AAPL" in script
