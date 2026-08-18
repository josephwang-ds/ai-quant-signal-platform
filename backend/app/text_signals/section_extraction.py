"""Extract a numbered item section (default: Item 1A, Risk Factors) from a 10-K.

Finding "Item 1A" in a 10-K is not a search problem, it is a disambiguation
problem. Real filings contain the string many times over:

* once in the table of contents,
* several times as mid-sentence cross-references
  ("...as discussed in Part I, Item 1A of this Form 10-K..."),
* and, in filings that use running page headers, once per *page* of the
  section itself. Microsoft's FY2023 10-K contains eighteen occurrences; only
  one of them starts the section.

Two observations separate the real heading from the decoys, and this module
uses both:

1. **Position.** A heading begins a line. Cross-references never do — they sit
   inside a sentence. Requiring line-start eliminates the entire
   cross-reference class without needing to understand the prose.
2. **Span.** Every candidate start is paired with the next item boundary that
   follows it, and the widest span wins. A table-of-contents entry is followed
   within a few characters by the next entry; the body section runs for tens
   of thousands. This also disposes of running headers, whose spans are
   strictly shorter than the true start's.

HTML is parsed with the standard library. ``bs4`` and ``lxml`` happen to be
importable in this environment, but neither is declared in
``requirements.txt`` — they arrive as transitive dependencies of something
else, and building on an undeclared transitive is how a pipeline breaks during
an unrelated upgrade. This mirrors the choice already made in
``factor_validation.inference`` to drop ``statsmodels``.

Extraction never guesses. When no candidate qualifies, the result carries an
``unavailable_reason`` and a ``None`` body rather than the whole document,
matching the platform's standing contract that a missing value stays missing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser

#: Tags whose boundaries imply a line break in the rendered document. Without
#: this, "Item 1A." and "Risk Factors" sitting in adjacent cells would be
#: concatenated into "Item 1A.Risk Factors" and the heading would be missed.
_BLOCK_TAGS = frozenset(
    {
        "address", "article", "aside", "blockquote", "br", "caption", "div",
        "footer", "h1", "h2", "h3", "h4", "h5", "h6", "header", "hr", "li",
        "ol", "p", "section", "table", "tbody", "td", "tfoot", "th", "thead",
        "tr", "ul",
    }
)

_DROPPED_TAGS = frozenset({"script", "style", "head", "title"})

#: Item labels that may terminate Item 1A. 1B is the usual successor, but it is
#: optional for some filers, and 1C (Cybersecurity) only appeared in filings
#: from late 2023. Any of them ends the section; the earliest one wins.
_DEFAULT_TERMINATORS = ("1B", "1C", "2")

#: Below this, a "section" is a table-of-contents artefact or a stub such as
#: "Item 1A. Risk Factors — Not applicable.", not a body of risk disclosure.
#:
#: Calibrated against the corpus rather than guessed: the median extracted
#: Item 1A runs about 67,000 characters, so anything in the low thousands is
#: structurally not a risk-factor body. The earlier 500-char floor admitted
#: ten table-of-contents captures in the 500–1,100 range, and because those
#: compare against a full-length prior year they surfaced as the *largest*
#: apparent rewrites — contaminating precisely the tail the study depends on.
#: Raised before any return was examined; see PREREGISTRATION D4.
MIN_SECTION_CHARS = 2_000


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._suppress = 0

    def handle_starttag(self, tag: str, attrs: object) -> None:  # noqa: ARG002
        if tag in _DROPPED_TAGS:
            self._suppress += 1
        elif tag in _BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _DROPPED_TAGS:
            self._suppress = max(0, self._suppress - 1)
        elif tag in _BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._suppress:
            self._parts.append(data)

    @property
    def text(self) -> str:
        return "".join(self._parts)


def html_to_text(markup: str) -> str:
    """Flatten filing HTML to newline-separated text.

    Normalises the non-breaking spaces that EDGAR HTML is full of; without
    that, ``\\xa0`` survives into the text and every whitespace-tolerant
    regex silently stops matching.
    """
    parser = _TextExtractor()
    parser.feed(markup)
    parser.close()
    text = parser.text.replace("\xa0", " ").replace(" ", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n[ \t]*", "\n", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def _bare_item_pattern(item: str, title: str) -> re.Pattern[str]:
    """Heading match for filers that omit the word "ITEM".

    Citigroup writes ``1A.`` then ``Risk Factors`` on the next line; Morgan
    Stanley and several other large banks do the same. Against those documents
    the string "item 1a" appears **zero** times, so requiring it silently drops
    the filer entirely — and because the convention clusters among large banks,
    the loss is systematic rather than random.

    A bare ``1A`` is far more ambiguous than ``ITEM 1A`` (it matches page
    furniture and list markers), so this pattern is only used as a fallback and
    only when the expected title follows immediately.
    """
    return re.compile(
        rf"^[ \t]*{re.escape(item)}[ \t]*[.:–—-]?[ \t]*\n?[ \t]*{re.escape(title)}",
        re.IGNORECASE | re.MULTILINE,
    )


def _item_pattern(item: str) -> re.Pattern[str]:
    """Heading-position match for an item label.

    Anchored to line start, which is what excludes mid-sentence
    cross-references. The separator class covers the punctuation filers
    actually use: ``Item 1A.``, ``ITEM 1A:``, ``Item 1A —``, or nothing at all.

    The ``ITEM`` prefix is **required**, and that is a deliberate reversal.
    Dropping it recovers a handful of filers who head the section with a bare
    ``1A.`` — but it equally loosens the *terminator* pattern, so a bare
    ``1B`` sitting in a table of contents starts closing sections early.
    Measured on a 150-document sample: one filing recovered, ninety truncated,
    median loss 45,000 characters. A slightly smaller corpus beats a corpus
    that is quietly half-length.
    """
    return re.compile(
        rf"^[ \t]*(?:PART\s+[IVX]+[ \t]*\n[ \t]*)?ITEM[ \t]*"
        rf"{re.escape(item)}[ \t]*[.:–—-]?",
        re.IGNORECASE | re.MULTILINE,
    )


@dataclass(frozen=True)
class SectionExtraction:
    """Result of one extraction attempt. Honest about failure."""

    item: str
    text: str | None
    char_count: int
    start_offset: int | None
    end_offset: int | None
    terminator: str | None
    candidates_considered: int
    unavailable_reason: str | None = None

    @property
    def ok(self) -> bool:
        return self.text is not None


def extract_item_section(
    text: str,
    *,
    item: str = "1A",
    expected_title: str | None = "risk factors",
    terminators: tuple[str, ...] = _DEFAULT_TERMINATORS,
    min_chars: int = MIN_SECTION_CHARS,
) -> SectionExtraction:
    """Extract one item section from already-flattened filing text.

    ``expected_title`` is checked in a short window after the heading and is
    what stops a bare running header ("Item 1A" alone at the top of a page)
    from being treated as a section start. Pass ``None`` to disable the check
    for items whose title varies.
    """
    if not text or not text.strip():
        return SectionExtraction(
            item=item,
            text=None,
            char_count=0,
            start_offset=None,
            end_offset=None,
            terminator=None,
            candidates_considered=0,
            unavailable_reason="empty document text",
        )

    starts = [m for m in _item_pattern(item).finditer(text)]
    if expected_title:
        titled = [
            m
            for m in starts
            if expected_title in text[m.end() : m.end() + 80].lower()
        ]
        # Only tighten if the title filter leaves something; some filers set the
        # heading and its title far enough apart that the window misses.
        starts = titled or starts

    if not starts and expected_title:
        # Fallback for the bare-number heading convention (see above).
        starts = list(_bare_item_pattern(item, expected_title).finditer(text))

    if not starts:
        return SectionExtraction(
            item=item,
            text=None,
            char_count=0,
            start_offset=None,
            end_offset=None,
            terminator=None,
            candidates_considered=0,
            unavailable_reason=f"no heading-position match for Item {item}",
        )

    ends: list[tuple[int, str]] = []
    for terminator in terminators:
        found = list(_item_pattern(terminator).finditer(text))
        if not found:
            # Same convention applies to the closing boundary: a filer that
            # writes "1A." also writes "1B.", and without this the section
            # would run to the end of the document.
            found = list(
                re.finditer(
                    rf"^[ \t]*{re.escape(terminator)}[ \t]*[.:–—-]",
                    text,
                    re.IGNORECASE | re.MULTILINE,
                )
            )
        ends.extend((m.start(), terminator) for m in found)
    ends.sort()

    best: tuple[int, int, int, str | None] | None = None  # (span, start, end, term)
    for match in starts:
        begin = match.start()
        following = [(pos, label) for pos, label in ends if pos > match.end()]
        if following:
            stop, label = following[0]
        else:
            stop, label = len(text), None
        span = stop - begin
        if best is None or span > best[0]:
            best = (span, begin, stop, label)

    assert best is not None
    span, begin, stop, label = best
    body = text[begin:stop].strip()

    if len(body) < min_chars:
        return SectionExtraction(
            item=item,
            text=None,
            char_count=len(body),
            start_offset=begin,
            end_offset=stop,
            terminator=label,
            candidates_considered=len(starts),
            unavailable_reason=(
                f"widest Item {item} span is {len(body)} chars, below the "
                f"{min_chars}-char floor; this is a table-of-contents entry or "
                "a stub such as 'Not applicable', not a disclosure body"
            ),
        )

    return SectionExtraction(
        item=item,
        text=body,
        char_count=len(body),
        start_offset=begin,
        end_offset=stop,
        terminator=label,
        candidates_considered=len(starts),
    )


def extract_risk_factors(markup: str) -> SectionExtraction:
    """Convenience path: filing HTML in, Item 1A (Risk Factors) out.

    Item 1A is the pre-registered section for the filing-change study. See
    ``docs/PREREGISTRATION_TEXT_SIGNALS.md``.
    """
    return extract_item_section(html_to_text(markup), item="1A")
