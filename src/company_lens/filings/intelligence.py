"""A small, inspectable NLP baseline for 8-K filings."""

from __future__ import annotations

import html
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from difflib import SequenceMatcher

import pandas as pd
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from company_lens.contracts import (
    Citation,
    FilingBrief,
    FilingChange,
    FilingComparison,
    FilingEntity,
    FilingReaction,
    FilingTimelinePoint,
)
from filing_triage.ingest.edgar import ITEM_LABELS

NUMBER_PATTERN = re.compile(
    r"(?<!\w)(?:\$\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:thousand|million|billion))?"
    r"|\d[\d,]*(?:\.\d+)?\s?(?:%|percent|million|billion))(?!\w)",
    re.IGNORECASE,
)
SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")
DATE_PATTERN = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+\d{1,2},\s+\d{4}\b|\b\d{4}-\d{2}-\d{2}\b",
    re.IGNORECASE,
)


def build_filing_briefs(
    events: pd.DataFrame,
    ticker: str,
    limit: int = 5,
    *,
    reactions: dict[str, FilingReaction] | None = None,
) -> list[FilingBrief]:
    """Read the latest filings with stable citations and issuer-relative novelty."""
    required = {
        "ticker",
        "cik",
        "accession",
        "primary_document",
        "form",
        "items",
        "acceptance_time",
        "text",
    }
    missing = required - set(events.columns)
    if missing:
        raise ValueError(f"event panel missing columns: {sorted(missing)}")
    issuer = events[events["ticker"].str.upper() == ticker.upper()].copy()
    if issuer.empty:
        return []
    issuer = issuer.sort_values("acceptance_time")
    novelty = _causal_novelty(issuer["text"].fillna("").tolist())
    issuer["novelty"] = novelty
    comparisons = _causal_comparisons(issuer)

    briefs = []
    reactions = reactions or {}
    for row in issuer.tail(limit).sort_values("acceptance_time", ascending=False).itertuples():
        source_url = _sec_url(int(row.cik), row.accession, row.primary_document)
        passages = _rank_passages(str(row.text), row.accession, source_url)
        entities = _extract_entities(passages)
        items = [
            {"code": code, "label": ITEM_LABELS.get(code, "Other disclosure")}
            for code in _item_codes(str(row.items))
        ]
        briefs.append(
            FilingBrief(
                accession=row.accession,
                form=row.form,
                accepted_at=pd.Timestamp(row.acceptance_time).isoformat(),
                items=items,
                source_url=source_url,
                novelty=float(row.novelty) if pd.notna(row.novelty) else None,
                key_numbers=_legacy_key_numbers(entities),
                entities=entities,
                passages=passages,
                comparison=comparisons.get(row.accession),
                reaction=reactions.get(str(row.accession)),
            )
        )
    return briefs


def build_filing_timeline(
    events: pd.DataFrame,
    ticker: str,
    *,
    reactions: dict[str, FilingReaction] | None = None,
    limit: int = 8,
) -> list[FilingTimelinePoint]:
    """Build a compact chronological filing history without rerunning passage NLP."""
    required = {
        "ticker",
        "cik",
        "accession",
        "primary_document",
        "items",
        "acceptance_time",
    }
    missing = required - set(events.columns)
    if missing:
        raise ValueError(f"event panel missing columns: {sorted(missing)}")
    issuer = events[
        events["ticker"].astype(str).str.upper() == ticker.upper()
    ].sort_values(["acceptance_time", "accession"])
    reactions = reactions or {}
    points = []
    for row in issuer.tail(limit).itertuples():
        codes = _item_codes(str(row.items))
        item_code = codes[0] if codes else "—"
        points.append(
            FilingTimelinePoint(
                accession=str(row.accession),
                accepted_at=pd.Timestamp(row.acceptance_time).isoformat(),
                item_code=item_code,
                item_label=ITEM_LABELS.get(item_code, "Corporate update"),
                source_url=_sec_url(int(row.cik), row.accession, row.primary_document),
                reaction=reactions.get(str(row.accession)),
            )
        )
    return points


def compare_filing_texts(
    current_text: str,
    prior_text: str,
    *,
    current_accession: str,
    prior_accession: str,
    current_source_url: str,
    prior_source_url: str,
    limit_per_kind: int = 3,
) -> tuple[list[FilingChange], dict[str, int]]:
    """Compare meaningful sentences while preserving current and prior source anchors."""
    current = _meaningful_sentences(current_text)
    prior = _meaningful_sentences(prior_text)
    prior_exact = {_normalize_sentence(sentence) for _, sentence in prior}
    current_exact = {_normalize_sentence(sentence) for _, sentence in current}
    current_open = [item for item in current if _normalize_sentence(item[1]) not in prior_exact]
    prior_open = [item for item in prior if _normalize_sentence(item[1]) not in current_exact]

    pair_candidates = _candidate_sentence_pairs(current_open, prior_open)

    used_current: set[int] = set()
    used_prior: set[int] = set()
    changed = []
    for similarity, current_position, current_sentence, prior_position, prior_sentence in sorted(
        pair_candidates, reverse=True
    ):
        if current_position in used_current or prior_position in used_prior:
            continue
        used_current.add(current_position)
        used_prior.add(prior_position)
        if _is_routine_period_update(current_sentence, prior_sentence):
            continue
        changed.append(
            FilingChange(
                kind="changed",
                current=_citation(
                    current_sentence,
                    current_position,
                    current_accession,
                    current_source_url,
                ),
                prior=_citation(
                    prior_sentence,
                    prior_position,
                    prior_accession,
                    prior_source_url,
                ),
                similarity=similarity,
            )
        )

    added = [
        FilingChange(
            kind="added",
            current=_citation(sentence, position, current_accession, current_source_url),
            prior=None,
        )
        for position, sentence in current_open
        if position not in used_current
    ]
    removed = [
        FilingChange(
            kind="removed",
            current=None,
            prior=_citation(sentence, position, prior_accession, prior_source_url),
        )
        for position, sentence in prior_open
        if position not in used_prior
    ]
    counts = {"changed": len(changed), "added": len(added), "removed": len(removed)}
    selected = (
        _rank_changes(changed, limit_per_kind)
        + _rank_changes(added, limit_per_kind)
        + _rank_changes(removed, limit_per_kind)
    )
    return selected, counts


def _candidate_sentence_pairs(
    current: list[tuple[int, str]],
    prior: list[tuple[int, str]],
    candidates_per_sentence: int = 6,
) -> list[tuple[float, int, str, int, str]]:
    """Block sentence pairs by shared informative tokens before edit similarity."""
    inverted: dict[str, set[int]] = defaultdict(set)
    for prior_index, (_, sentence) in enumerate(prior):
        for token in _comparison_tokens(sentence):
            inverted[token].add(prior_index)

    pairs = []
    for current_position, current_sentence in current:
        overlap: Counter[int] = Counter()
        for token in _comparison_tokens(current_sentence):
            overlap.update(inverted.get(token, ()))
        for prior_index, shared in overlap.most_common(candidates_per_sentence):
            if shared < 2:
                continue
            prior_position, prior_sentence = prior[prior_index]
            similarity = SequenceMatcher(
                None,
                _normalize_sentence(current_sentence),
                _normalize_sentence(prior_sentence),
            ).ratio()
            if similarity >= 0.48:
                pairs.append(
                    (
                        similarity,
                        current_position,
                        current_sentence,
                        prior_position,
                        prior_sentence,
                    )
                )
    return pairs


def _comparison_tokens(sentence: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z]{3,}", sentence.lower())
        if token
        not in {
            "and",
            "the",
            "for",
            "from",
            "that",
            "this",
            "with",
            "company",
            "item",
        }
    }


def _causal_comparisons(issuer: pd.DataFrame) -> dict[str, FilingComparison]:
    comparisons = {}
    prior_by_key = {}
    for row in issuer.sort_values("acceptance_time").itertuples():
        comparable_key = _comparable_key(str(row.form), str(row.items))
        prior = prior_by_key.get(comparable_key)
        if prior is not None:
            current_url = _sec_url(int(row.cik), row.accession, row.primary_document)
            prior_url = _sec_url(int(prior.cik), prior.accession, prior.primary_document)
            changes, counts = compare_filing_texts(
                str(row.text),
                str(prior.text),
                current_accession=row.accession,
                prior_accession=prior.accession,
                current_source_url=current_url,
                prior_source_url=prior_url,
            )
            comparisons[row.accession] = FilingComparison(
                comparable_key=comparable_key,
                prior_accession=prior.accession,
                prior_accepted_at=pd.Timestamp(prior.acceptance_time).isoformat(),
                prior_source_url=prior_url,
                changes=changes,
                counts=counts,
            )
        prior_by_key[comparable_key] = row
    return comparisons


def _causal_novelty(texts: list[str]) -> list[float | None]:
    """Compare each document only with documents that existed before it."""
    if not texts:
        return []
    matrix = HashingVectorizer(
        n_features=2**14, alternate_sign=False, norm="l2", stop_words="english"
    ).transform(texts)
    values: list[float | None] = [None]
    for index in range(1, len(texts)):
        similarities = cosine_similarity(matrix[index], matrix[:index]).ravel()
        values.append(float(1.0 - similarities.max()) if similarities.size else None)
    return values


def _meaningful_sentences(text: str) -> list[tuple[int, str]]:
    sentences = [
        sentence.strip()
        for sentence in SENTENCE_PATTERN.split(html.unescape(text))
        if sentence.strip()
    ]
    return [
        (index, sentence)
        for index, sentence in enumerate(sentences)
        if 25 <= len(sentence) <= 700 and not _is_boilerplate(sentence)
    ]


def _is_boilerplate(sentence: str) -> bool:
    lower = sentence.lower()
    return any(
        phrase in lower
        for phrase in (
            "shall not be deemed",
            "emerging growth company",
            "pursuant to the requirements",
            "securities exchange act of 1934",
        )
    )


def _normalize_sentence(sentence: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", sentence.lower()).strip()


def _is_routine_period_update(current: str, prior: str) -> bool:
    """Suppress roll-forwards whose only change is a date or fiscal quarter."""
    current_signature = _period_signature(current)
    prior_signature = _period_signature(prior)
    return (
        _normalize_sentence(current) != _normalize_sentence(prior)
        and current_signature == prior_signature
    )


def _period_signature(sentence: str) -> str:
    value = sentence.lower()
    month = (
        r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
        r"dec(?:ember)?)"
    )
    value = re.sub(rf"\b{month}\s+\d{{1,2}},?\s+\d{{4}}\b", " date ", value)
    value = re.sub(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", " date ", value)
    if "quarter" in value:
        value = re.sub(r"\b(first|second|third|fourth)\b", " period ", value)
        value = re.sub(r"\bq[1-4]\b", " period ", value)
    return _normalize_sentence(value)


def _citation(
    sentence: str,
    position: int,
    accession: str,
    source_url: str,
) -> Citation:
    return Citation(
        anchor=f"{accession}#sentence-{position + 1}",
        accession=accession,
        source_url=source_url,
        text=sentence,
    )


def _rank_changes(changes: list[FilingChange], limit: int) -> list[FilingChange]:
    return sorted(
        changes,
        key=lambda change: _passage_score(
            (change.current or change.prior).text  # type: ignore[union-attr]
        ),
        reverse=True,
    )[:limit]


def _passage_score(sentence: str) -> int:
    lower = sentence.lower()
    return (
        2 * len(NUMBER_PATTERN.findall(sentence))
        + 2 * int("item " in lower)
        + 2
        * sum(
            word in lower
            for word in (
                "results",
                "revenue",
                "agreement",
                "appointed",
                "resigned",
                "impairment",
                "acquisition",
                "guidance",
                "dividend",
            )
        )
    )


def _comparable_key(form: str, raw_items: str) -> str:
    codes = _item_codes(raw_items)
    primary = next((code for code in codes if code != "9.01"), codes[0] if codes else "other")
    return f"{form.upper()}:{primary}"


def _rank_passages(text: str, accession: str, source_url: str, limit: int = 3) -> list[Citation]:
    text = html.unescape(text)
    sentences = [sentence.strip() for sentence in SENTENCE_PATTERN.split(text) if sentence.strip()]
    candidates = []
    for source_index, sentence in enumerate(sentences):
        if len(sentence) < 25 or len(sentence) > 700:
            continue
        score = _passage_score(sentence)
        score -= 8 * _is_boilerplate(sentence)
        if score > 0:
            candidates.append((score, source_index, sentence))
    selected = sorted(candidates, key=lambda value: (-value[0], value[1]))[:limit]
    return [
        Citation(
            anchor=f"{accession}#sentence-{source_index + 1}",
            accession=accession,
            source_url=source_url,
            text=sentence,
        )
        for _, source_index, sentence in selected
    ]


def _extract_entities(passages: list[Citation], limit: int = 12) -> list[FilingEntity]:
    """Extract typed values with offsets relative to their stable cited passage."""
    extracted: list[FilingEntity] = []
    seen: set[tuple[str, str, str]] = set()
    for passage in passages:
        for match in NUMBER_PATTERN.finditer(passage.text):
            entity = _numeric_entity(match, passage.anchor)
            key = (entity.kind, entity.text, entity.citation)
            if key in seen:
                continue
            seen.add(key)
            extracted.append(entity)
            if len(extracted) >= limit:
                return extracted
        for match in DATE_PATTERN.finditer(passage.text):
            text = match.group(0)
            key = ("date", text, passage.anchor)
            if key in seen:
                continue
            seen.add(key)
            extracted.append(
                FilingEntity(
                    text=text,
                    kind="date",
                    normalized_value=_normalize_date(text),
                    unit="calendar_date",
                    citation=passage.anchor,
                    source_start=match.start(),
                    source_end=match.end(),
                )
            )
            if len(extracted) >= limit:
                return extracted
    return extracted


def _numeric_entity(match: re.Match[str], citation: str) -> FilingEntity:
    text = match.group(0).strip()
    lower = text.lower().replace(",", "")
    number_match = re.search(r"\d+(?:\.\d+)?", lower)
    value = float(number_match.group(0)) if number_match else 0.0
    factor = 1.0
    if "thousand" in lower:
        factor = 1_000.0
    elif "million" in lower:
        factor = 1_000_000.0
    elif "billion" in lower:
        factor = 1_000_000_000.0
    if text.startswith("$"):
        kind, unit, normalized = "money", "USD", value * factor
    elif "%" in lower or "percent" in lower:
        kind, unit, normalized = "percentage", "ratio", value / 100.0
    else:
        kind, unit, normalized = "scaled_number", "count", value * factor
    return FilingEntity(
        text=text,
        kind=kind,
        normalized_value=f"{normalized:g}",
        unit=unit,
        citation=citation,
        source_start=match.start(),
        source_end=match.end(),
    )


def _normalize_date(value: str) -> str:
    for pattern in ("%B %d, %Y", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(value.title(), pattern).replace(tzinfo=UTC)
            return parsed.date().isoformat()
        except ValueError:
            continue
    return value


def _legacy_key_numbers(
    entities: list[FilingEntity], limit: int = 8
) -> list[dict[str, str]]:
    return [
        {"value": entity.text, "citation": entity.citation}
        for entity in entities
        if entity.kind != "date"
    ][:limit]


def _item_codes(raw: str) -> list[str]:
    return re.findall(r"\d\.\d{2}", raw)


def _sec_url(cik: int, accession: str, document: str) -> str:
    return (
        f"https://www.sec.gov/Archives/edgar/data/{cik}/"
        f"{accession.replace('-', '')}/{document}"
    )
