"""Serving-layer errors for the read-only intelligence API."""

from __future__ import annotations

from typing import Optional


class IntelligenceServingError(Exception):
    """Base error for Phase 4.5 intelligence query serving."""

    error_code: str = "INTELLIGENCE_STORAGE_ERROR"
    http_status: int = 500

    def __init__(
        self,
        message: str,
        *,
        run_id: Optional[str] = None,
        resource_id: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.run_id = run_id
        self.resource_id = resource_id


class InvalidIntelligenceQueryError(IntelligenceServingError):
    error_code = "INVALID_QUERY"
    http_status = 400


class InvalidRunIdError(IntelligenceServingError):
    error_code = "INVALID_RUN_ID"
    http_status = 400


class InvalidSnapshotTypeError(IntelligenceServingError):
    error_code = "INVALID_SNAPSHOT_TYPE"
    http_status = 400


class RunNotFoundServingError(IntelligenceServingError):
    error_code = "RUN_NOT_FOUND"
    http_status = 404


class RunNotPublishedError(IntelligenceServingError):
    error_code = "RUN_NOT_PUBLISHED"
    http_status = 403


class LatestPublishedRunNotFoundError(IntelligenceServingError):
    error_code = "LATEST_NOT_FOUND"
    http_status = 404


class LatestPointerInvalidError(IntelligenceServingError):
    error_code = "LATEST_POINTER_INVALID"
    http_status = 409


class SnapshotNotFoundServingError(IntelligenceServingError):
    error_code = "SNAPSHOT_NOT_FOUND"
    http_status = 404


class SnapshotIntegrityServingError(IntelligenceServingError):
    error_code = "SNAPSHOT_INTEGRITY_FAILED"
    http_status = 409


class SnapshotContentInvalidError(IntelligenceServingError):
    error_code = "SNAPSHOT_CONTENT_INVALID"
    http_status = 422


class IntelligenceStorageServingError(IntelligenceServingError):
    error_code = "INTELLIGENCE_STORAGE_ERROR"
    http_status = 500


class ManifestValidationServingError(IntelligenceServingError):
    error_code = "MANIFEST_VALIDATION_ERROR"
    http_status = 500
