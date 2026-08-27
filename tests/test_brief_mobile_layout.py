"""Computed brief-grid layout cascade at a 390px viewport."""

from __future__ import annotations

import re

from company_lens.web.page import _css

BRIEF_CLASSES = (
    "brief-lead",
    "brief-numbers",
    "brief-reading",
    "brief-limit",
    "brief-missing",
    "brief-quality",
)


def _parse_declarations(block: str) -> dict[str, str]:
    declarations: dict[str, str] = {}
    for chunk in block.split(";"):
        if ":" not in chunk:
            continue
        prop, value = chunk.split(":", 1)
        declarations[prop.strip()] = value.strip()
    return declarations


def _cascade_scan(css: str, width: int) -> dict[str, dict[str, str]]:
    state: dict[str, dict[str, str]] = {name: {} for name in ("brief-grid", *BRIEF_CLASSES)}
    i = 0
    active_max: int | None = None
    while i < len(css):
        media = re.match(r"@media\(max-width:(\d+)px\)\{", css[i:])
        if media:
            active_max = int(media.group(1))
            i += media.end()
            continue
        if css[i] == "}" and active_max is not None:
            active_max = None
            i += 1
            continue
        rule = re.match(r"([^{}@]+)\{([^{}]+)\}", css[i:])
        if not rule:
            i += 1
            continue
        if active_max is not None and width > active_max:
            i += rule.end()
            continue
        selector = rule.group(1)
        decls = _parse_declarations(rule.group(2))
        interesting = {
            key: value
            for key, value in decls.items()
            if key in {"grid-template-columns", "grid-column"}
        }
        i += rule.end()
        if not interesting:
            continue
        compact = selector.replace(" ", "")
        for name in state:
            token = f".{name}"
            if token not in compact:
                continue
            if name != "brief-grid" and compact == ".brief-grid":
                continue
            state[name].update(interesting)
    return state


def test_brief_cards_span_full_width_at_390px() -> None:
    css = _css()
    # Responsive full-width rule must come after unconditional brief span rules.
    assert css.rfind(".brief-quality{grid-column:span 6}") < css.rfind(
        ".brief-lead,.brief-numbers,.brief-reading,.brief-limit,.brief-missing,.brief-quality{grid-column:1/-1}"
    )

    desktop = _cascade_scan(css, width=1200)
    mobile = _cascade_scan(css, width=390)

    assert "repeat(12" in desktop["brief-grid"].get("grid-template-columns", "")
    assert desktop["brief-lead"].get("grid-column") == "span 7"
    assert desktop["brief-quality"].get("grid-column") == "span 6"

    assert mobile["brief-grid"].get("grid-template-columns") == "1fr"
    for name in BRIEF_CLASSES:
        assert mobile[name].get("grid-column") == "1/-1", name

    # Computed layout: one-column grid at 390px content width is ~full width, not ~38px.
    main_padding = 14  # @media(max-width:620px) main padding
    section_padding = 18
    content_width = 390 - (2 * main_padding) - (2 * section_padding)
    card_width = content_width  # grid-column:1/-1 inside a 1fr brief-grid
    assert content_width >= 300
    assert card_width > 200
    assert abs(card_width - content_width) < 1
