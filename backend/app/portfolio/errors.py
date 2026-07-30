"""Filesystem and repository errors for Portfolio Intelligence (Phase 5.1B)."""

from __future__ import annotations

from typing import Any, Optional


class PortfolioRepositoryError(Exception):
    """Base error for Portfolio registry operations."""

    def __init__(
        self,
        message: str,
        *,
        portfolio_id: Optional[str] = None,
        portfolio_version: Optional[int] = None,
        operation: Optional[str] = None,
        path_category: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.portfolio_id = portfolio_id
        self.portfolio_version = portfolio_version
        self.operation = operation
        self.path_category = path_category
        self.context: dict[str, Any] = {
            key: value
            for key, value in {
                "portfolio_id": portfolio_id,
                "portfolio_version": portfolio_version,
                "operation": operation,
                "path_category": path_category,
            }.items()
            if value is not None
        }


class PortfolioNotFoundError(PortfolioRepositoryError):
    """Requested portfolio identity does not exist in the registry."""


class PortfolioVersionNotFoundError(PortfolioRepositoryError):
    """Requested published portfolio version does not exist."""


class PortfolioDraftNotFoundError(PortfolioRepositoryError):
    """Requested portfolio draft does not exist."""


class PortfolioAlreadyPublishedError(PortfolioRepositoryError):
    """Published version already exists (idempotent or conflict subclass context)."""


class PortfolioPublicationConflictError(PortfolioAlreadyPublishedError):
    """Same version exists with a different content checksum."""


class PortfolioIntegrityError(PortfolioRepositoryError):
    """Stored portfolio bytes do not match integrity metadata."""


class PortfolioLockError(PortfolioRepositoryError):
    """Unable to acquire the per-portfolio write lock."""


class PortfolioStorageError(PortfolioRepositoryError):
    """Filesystem failure inside the portfolio registry root."""


class PortfolioInvalidStoredManifestError(PortfolioRepositoryError):
    """Stored portfolio JSON is corrupt or fails Phase 5.1A contracts."""


class PortfolioInvalidStateError(PortfolioRepositoryError):
    """Manifest lifecycle or version is incompatible with the requested operation."""
