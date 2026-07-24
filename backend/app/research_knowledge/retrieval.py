"""Deterministic lexical Research Rulebook retrieval — no vector DB."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

from app.research_knowledge.catalog import (
    DOCUMENTS_DIR,
    KnowledgeDocument,
    active_catalog,
)


@dataclass(frozen=True)
class KnowledgeHit:
    knowledge_id: str
    title: str
    topic: str
    research_type: str
    version: str
    status: str
    source_path: str
    excerpt: str
    score: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


_TOKEN_RE = re.compile(r"[a-z0-9_]+", re.IGNORECASE)


def _tokenize(text: str) -> set[str]:
    return {token.lower() for token in _TOKEN_RE.findall(text or "")}


def _load_text(doc: KnowledgeDocument) -> str:
    path = DOCUMENTS_DIR / doc.source_path
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8").strip()


class ResearchRulebookRetriever:
    """Metadata-filtered lexical ranking over curated Markdown rulebook docs."""

    def __init__(self, catalog: list[KnowledgeDocument] | None = None) -> None:
        self.catalog = catalog if catalog is not None else active_catalog()

    def retrieve(
        self,
        *,
        query: str,
        research_type: str | None = None,
        topic: str | None = None,
        top_k: int = 4,
    ) -> list[KnowledgeHit]:
        query_tokens = _tokenize(query)
        if topic:
            query_tokens |= _tokenize(topic)
        hits: list[KnowledgeHit] = []
        for doc in self.catalog:
            if doc.status != "active":
                continue
            if research_type and doc.research_type not in ("all", research_type):
                continue
            if topic and topic.lower() not in {
                doc.topic.lower(),
                *(tag.lower() for tag in doc.tags),
            }:
                # soft filter — still allow lexical match below
                pass
            text = _load_text(doc)
            if not text:
                continue
            doc_tokens = _tokenize(text) | _tokenize(doc.title) | set(doc.tags)
            overlap = len(query_tokens & doc_tokens)
            type_bonus = 2 if research_type and doc.research_type == research_type else 0
            topic_bonus = (
                2
                if topic
                and (
                    topic.lower() == doc.topic.lower()
                    or topic.lower() in {t.lower() for t in doc.tags}
                )
                else 0
            )
            score = float(overlap + type_bonus + topic_bonus)
            if score <= 0 and not query_tokens:
                score = 1.0 if doc.research_type in ("all", research_type or "all") else 0.0
            if score <= 0:
                continue
            excerpt = text[:600].strip()
            hits.append(
                KnowledgeHit(
                    knowledge_id=doc.knowledge_id,
                    title=doc.title,
                    topic=doc.topic,
                    research_type=doc.research_type,
                    version=doc.version,
                    status=doc.status,
                    source_path=str(doc.source_path),
                    excerpt=excerpt,
                    score=score,
                )
            )
        hits.sort(key=lambda item: (-item.score, item.knowledge_id))
        return hits[: max(1, top_k)]


def retrieve_rulebook(
    *,
    query: str,
    research_type: str | None = None,
    topic: str | None = None,
    top_k: int = 4,
) -> list[dict[str, Any]]:
    return [
        hit.as_dict()
        for hit in ResearchRulebookRetriever().retrieve(
            query=query,
            research_type=research_type,
            topic=topic,
            top_k=top_k,
        )
    ]
