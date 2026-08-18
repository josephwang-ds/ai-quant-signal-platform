"""Year-over-year textual similarity for a single company's filings.

The signal is *change*: a firm that rewrites its risk disclosure has done
something a firm that copy-pastes has not. Similarity is the measurement,
``1 - similarity`` is the signal.

Three constraints are enforced structurally here rather than left to callers.

**Same company only.** A cosine between two different firms' filings measures
industry vocabulary, not change — pharmaceutical filings resemble other
pharmaceutical filings whatever either of them said last year. Comparing across
symbols is refused rather than warned about.

**Point-in-time IDF.** TF-IDF needs a document collection to weight terms, and
the obvious implementation — fit the vectoriser on every filing in the sample —
leaks. A term's rarity computed over documents that had not yet been filed is
information from the future, and it changes the weights applied to the past.
:func:`select_point_in_time_corpus` exists so that the corpus is filtered by
availability before the vectoriser ever sees it.

**A zero vector is not zero similarity.** If a document shares no vocabulary
with the fitted corpus its vector is all zeros, and the cosine is undefined
rather than 0.0. Returning 0.0 would report maximal change — the strongest
possible signal — from a document that simply failed to vectorise. That case
returns an ``unavailable_reason`` instead.

Vectorisation uses ``scikit-learn``, which is a declared dependency already
carrying the Ridge and LightGBM models. The corpus discipline above is this
module's own; only the term weighting is delegated.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

#: Alphabetic tokens of two or more characters. Pure numbers are deliberately
#: excluded: dollar amounts and dates change every year for reasons that have
#: nothing to do with a firm revising what it discloses, and counting them as
#: textual change would manufacture signal in the most mechanical way possible.
#: Pre-registered — see docs/PREREGISTRATION_TEXT_SIGNALS.md (D5).
TOKEN_PATTERN = r"(?u)\b[A-Za-z][A-Za-z]+\b"

#: Below this many tokens a section is too short for a cosine to mean anything.
MIN_TOKENS = 100


@dataclass(frozen=True)
class TimedDocument:
    """A filing's extracted section text, with the instant it became usable.

    ``available_at`` is ``TextRecord.information_available_time`` from the
    timestamp module — not publish time, and not filing date.
    """

    doc_id: str
    symbol: str
    text: str
    available_at: datetime
    fiscal_year: int | None = None


@dataclass(frozen=True)
class SimilarityResult:
    symbol: str
    current_doc_id: str
    prior_doc_id: str
    cosine_similarity: float | None
    #: ``1 - cosine``. The quantity the study is actually about.
    change_score: float | None
    idf_corpus_size: int
    unavailable_reason: str | None = None

    @property
    def ok(self) -> bool:
        return self.cosine_similarity is not None


class CrossCompanyComparisonError(ValueError):
    """Raised when two filings from different issuers would be compared."""


def select_point_in_time_corpus(
    documents: Sequence[TimedDocument],
    as_of: datetime,
) -> list[TimedDocument]:
    """Documents legitimately usable for fitting IDF at ``as_of``.

    Equality is admissible: a document available exactly at the computation
    instant exists at that instant. This mirrors ``assert_no_lookahead`` in the
    timestamp module rather than inventing a second convention.
    """
    if as_of.tzinfo is None:
        raise ValueError("naive datetime rejected; supply an aware datetime")
    return [
        doc
        for doc in documents
        if doc.available_at.tzinfo is not None and doc.available_at <= as_of
    ]


def _token_count(vectorizer: TfidfVectorizer, text: str) -> int:
    return len(vectorizer.build_analyzer()(text))


def fit_idf(corpus: Sequence[TimedDocument]) -> TfidfVectorizer | None:
    """Fit one vectoriser on an already point-in-time-filtered corpus.

    Exists so that a batch of pairs sharing the same information cutoff can be
    scored against a single fit. Refitting per pair is not more correct — the
    corpus is identical for every pair at the same instant — it is only
    slower, by roughly the number of pairs.
    """
    texts = [doc.text for doc in corpus if doc.text.strip()]
    if not texts:
        return None
    vectorizer = TfidfVectorizer(
        token_pattern=TOKEN_PATTERN, lowercase=True, norm="l2"
    )
    try:
        vectorizer.fit(texts)
    except ValueError:
        return None
    return vectorizer


def year_over_year_similarity(
    current: TimedDocument,
    prior: TimedDocument,
    *,
    idf_corpus: Sequence[TimedDocument],
    min_tokens: int = MIN_TOKENS,
    vectorizer: TfidfVectorizer | None = None,
) -> SimilarityResult:
    """Cosine similarity between one firm's filing and its own prior filing.

    ``idf_corpus`` must already be point-in-time filtered; this function does
    not filter it, because it cannot know the caller's computation instant.
    Pass the output of :func:`select_point_in_time_corpus`.

    ``vectorizer`` optionally supplies a fit produced by :func:`fit_idf` over
    that same corpus, so a batch sharing one cutoff pays for a single fit.
    """
    if current.symbol != prior.symbol:
        raise CrossCompanyComparisonError(
            f"refusing to compare {current.symbol} with {prior.symbol}: a "
            "cross-company cosine measures industry vocabulary, not change"
        )
    if current.doc_id == prior.doc_id:
        raise ValueError(
            f"{current.doc_id}: cannot compare a filing with itself"
        )

    def unavailable(reason: str) -> SimilarityResult:
        return SimilarityResult(
            symbol=current.symbol,
            current_doc_id=current.doc_id,
            prior_doc_id=prior.doc_id,
            cosine_similarity=None,
            change_score=None,
            idf_corpus_size=len(idf_corpus),
            unavailable_reason=reason,
        )

    if not current.text.strip() or not prior.text.strip():
        return unavailable("one or both documents are empty")

    corpus_texts = [doc.text for doc in idf_corpus if doc.text.strip()]
    if not corpus_texts:
        return unavailable("point-in-time IDF corpus is empty")

    if vectorizer is None:
        vectorizer = TfidfVectorizer(
            token_pattern=TOKEN_PATTERN,
            lowercase=True,
            norm="l2",
        )
        try:
            vectorizer.fit(corpus_texts)
        except ValueError as exc:  # e.g. corpus is entirely stop words
            return unavailable(f"IDF corpus could not be vectorised: {exc}")

    n_current = _token_count(vectorizer, current.text)
    n_prior = _token_count(vectorizer, prior.text)
    if n_current < min_tokens or n_prior < min_tokens:
        return unavailable(
            f"document too short to compare: {n_current} and {n_prior} tokens "
            f"against a {min_tokens}-token floor"
        )

    matrix = vectorizer.transform([current.text, prior.text])
    norms = np.asarray(np.sqrt(matrix.multiply(matrix).sum(axis=1))).ravel()
    if float(norms[0]) == 0.0 or float(norms[1]) == 0.0:
        return unavailable(
            "a document shares no vocabulary with the point-in-time IDF "
            "corpus, so its vector is all zeros and the cosine is undefined; "
            "reporting this rather than 0.0, which would claim maximal change"
        )

    # TfidfVectorizer already L2-normalises, so the dot product is the cosine.
    cosine = float(matrix[0].multiply(matrix[1]).sum())
    cosine = min(1.0, max(0.0, cosine))

    return SimilarityResult(
        symbol=current.symbol,
        current_doc_id=current.doc_id,
        prior_doc_id=prior.doc_id,
        cosine_similarity=cosine,
        change_score=1.0 - cosine,
        idf_corpus_size=len(corpus_texts),
    )


def pair_consecutive_filings(
    documents: Sequence[TimedDocument],
) -> list[tuple[TimedDocument, TimedDocument]]:
    """Pair each filing with the same company's immediately preceding one.

    Ordering is by availability, not fiscal year: a late or amended filing
    becomes usable when it becomes usable, and pairing on fiscal year would
    silently compare documents the pipeline could not yet have read.
    """
    by_symbol: dict[str, list[TimedDocument]] = {}
    for doc in documents:
        by_symbol.setdefault(doc.symbol, []).append(doc)

    pairs: list[tuple[TimedDocument, TimedDocument]] = []
    for symbol_docs in by_symbol.values():
        ordered = sorted(symbol_docs, key=lambda d: (d.available_at, d.doc_id))
        for prior, current in zip(ordered, ordered[1:]):
            pairs.append((current, prior))
    return pairs
