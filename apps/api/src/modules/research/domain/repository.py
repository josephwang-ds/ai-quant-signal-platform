"""Research 仓储端口（领域层接口，无基础设施依赖）。"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from modules.research.domain.research import Research


class ResearchRepository(Protocol):
    """Research 聚合持久化端口。"""

    def save(self, research: Research) -> Research:
        """持久化新建或更新的 Research，返回存储后的快照。"""
        ...

    def get_by_id(self, research_id: UUID) -> Research | None:
        """按 ID 读取；不存在时返回 None。"""
        ...
