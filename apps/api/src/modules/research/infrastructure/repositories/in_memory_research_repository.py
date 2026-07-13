"""Research 仓储内存实现（生产路径可替换为 Postgres 适配器）。"""

from __future__ import annotations

from threading import Lock
from uuid import UUID

from modules.research.domain.research import Research


class InMemoryResearchRepository:
    """线程安全的内存仓储 Stub，用于切片标准与集成测试。"""

    def __init__(self) -> None:
        self._items: dict[UUID, Research] = {}
        self._lock = Lock()

    def save(self, research: Research) -> Research:
        with self._lock:
            self._items[research.id] = research
            return research

    def get_by_id(self, research_id: UUID) -> Research | None:
        with self._lock:
            return self._items.get(research_id)

    def clear(self) -> None:
        """测试辅助：清空存储。"""
        with self._lock:
            self._items.clear()
