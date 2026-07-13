"""跨模块可复用的领域与应用层错误基类。"""

from __future__ import annotations

from typing import Optional


class DomainError(Exception):
    """领域不变量或业务规则违反。"""

    def __init__(self, message: str, *, code: str = "domain_error") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class ValidationError(DomainError):
    """命令或输入未通过校验。"""

    def __init__(self, message: str, *, field: Optional[str] = None) -> None:
        code = f"validation.{field}" if field else "validation_error"
        super().__init__(message, code=code)
        self.field = field


class NotFoundError(DomainError):
    """请求的聚合或实体不存在。"""

    def __init__(self, message: str, *, code: str = "not_found") -> None:
        super().__init__(message, code=code)
