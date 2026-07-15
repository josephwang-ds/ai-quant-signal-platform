"""Lightweight in-memory retrieval over approved public documentation chunks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    citation_id: str
    source_type: str
    source_id: str
    label: str
    text: str
    tags: tuple[str, ...]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _read_excerpt(path: Path, max_chars: int = 1200) -> str:
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"^#+ ", "", text, flags=re.MULTILINE)
    return text[:max_chars].strip()


def build_default_chunks() -> list[DocumentChunk]:
    root = _repo_root()
    chunks: list[DocumentChunk] = []
    specs = [
        (
            "doc-execution",
            "documentation:look_ahead_policy",
            "documentation",
            "docs/slices/research-execution.md",
            "Look-ahead and position-lag policy",
            ("execution", "provenance", "lag", "cost", "look-ahead"),
        ),
        (
            "doc-validation",
            "documentation:validation_methodology",
            "documentation",
            "docs/slices/research-validation.md",
            "Research validation methodology",
            ("validation", "oos", "sensitivity", "data-quality"),
        ),
        (
            "doc-evaluation",
            "documentation:evaluation_governance",
            "documentation",
            "docs/slices/research-evaluation.md",
            "Research evaluation governance",
            ("evaluation", "coverage", "blockers", "limitations"),
        ),
        (
            "doc-authenticity",
            "documentation:authenticity_policy",
            "documentation",
            "docs/data/AUTHENTICITY_POLICY.md",
            "Authenticity policy",
            ("authenticity", "evidence", "fabricated"),
        ),
        (
            "doc-bible",
            "documentation:project_constitution",
            "documentation",
            "docs/PROJECT_BIBLE.md",
            "Project constitution",
            ("governance", "research", "ai"),
        ),
    ]
    for chunk_id, citation_id, source_type, rel_path, label, tags in specs:
        text = _read_excerpt(root / rel_path)
        if text:
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    citation_id=citation_id,
                    source_type=source_type,
                    source_id=rel_path,
                    label=label,
                    text=text,
                    tags=tags,
                )
            )
    return chunks


class RetrievalIndex:
    """Keyword-scored top-k retrieval — no external vector database."""

    def __init__(self, chunks: list[DocumentChunk] | None = None) -> None:
        self._chunks = chunks if chunks is not None else build_default_chunks()

    def search(self, query: str, *, limit: int = 4) -> list[DocumentChunk]:
        tokens = {
            token
            for token in re.findall(r"[a-z0-9]+", query.lower())
            if len(token) > 2
        }
        if not tokens:
            return self._chunks[:limit]

        scored: list[tuple[int, DocumentChunk]] = []
        for chunk in self._chunks:
            haystack = f"{chunk.label} {chunk.text} {' '.join(chunk.tags)}".lower()
            score = sum(1 for token in tokens if token in haystack)
            if score:
                scored.append((score, chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [chunk for _, chunk in scored[:limit]] or self._chunks[:limit]
