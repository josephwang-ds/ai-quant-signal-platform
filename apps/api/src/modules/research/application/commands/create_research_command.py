"""CreateResearch 命令。"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class CreateResearchCommand:
    """创建 Research 的应用命令（无 HTTP / ORM 细节）。"""

    strategy_id: UUID
    title: str
    objective: str
    owner: str
    notes: str | None = None
