"""Typed contracts for Portfolio Intelligence (Phase 5.1A).

Authority split
---------------
* **Portfolio domain contracts** in this module define identity, lifecycle,
  membership references, analytical weights, constraints, manifest shape,
  snapshot *references*, and validation issue codes.
* **Research evidence** remains owned by Phase 4. Members reference published
  ``run_*`` identities and snapshot IDs; they never embed research payloads.
* **Persistence / publication / builders / APIs** belong to later Phase 5
  slices and must not be imported here.

Analytical weights are research evidence, not live allocation or execution
authority.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.intelligence.schemas import is_valid_run_id, is_valid_snapshot_id

PORTFOLIO_MANIFEST_SCHEMA_VERSION = "portfolio-manifest/v1"
PORTFOLIO_SNAPSHOT_REF_SCHEMA_VERSION = "portfolio-snapshot-ref/v1"
PORTFOLIO_PUBLICATION_PROVENANCE_SCHEMA_VERSION = "portfolio-publication-provenance/v1"
CHECKSUM_ALGORITHM_SHA256 = "sha256"

# Matches ADR-0017: portfolio_{UTC timestamp}_{8-hex}
PORTFOLIO_ID_PATTERN = re.compile(r"^portfolio_\d{8}T\d{6}Z_[0-9a-f]{8}$")
SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")

WEIGHT_SUM_TOLERANCE_DEFAULT = Decimal("0.000001")
WEIGHT_SUM_TOLERANCE_MAX = Decimal("0.01")


class PortfolioLifecycleStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"


class RebalanceFrequency(str, Enum):
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"


class WeightMethod(str, Enum):
    """How member analytical weights are represented on the manifest.

    ``EQUAL`` — every member omits ``analytical_weight``; equal materialization
    belongs to later builders. No automatic normalization occurs here.

    ``OPERATOR_SPECIFIED`` — every member provides an explicit analytical weight.
    """

    EQUAL = "equal"
    OPERATOR_SPECIFIED = "operator_specified"


class PortfolioSnapshotType(str, Enum):
    """Portfolio-only snapshot taxonomy (separate from ResearchSnapshotType)."""

    PORTFOLIO_SUMMARY = "portfolio_summary"
    PORTFOLIO_MEMBERSHIP = "portfolio_membership"
    PORTFOLIO_WEIGHTS = "portfolio_weights"
    PORTFOLIO_EXPOSURE = "portfolio_exposure"
    PORTFOLIO_CONSTRAINTS = "portfolio_constraints"
    PORTFOLIO_RISK = "portfolio_risk"
    PORTFOLIO_REVIEW = "portfolio_review"
    PORTFOLIO_BACKTEST = "portfolio_backtest"


class PortfolioSnapshotAvailability(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    UNSUPPORTED = "UNSUPPORTED"
    INVALID = "INVALID"


class PortfolioValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


class PortfolioValidationIssueCode(str, Enum):
    INVALID_PORTFOLIO_ID = "INVALID_PORTFOLIO_ID"
    INVALID_VERSION = "INVALID_VERSION"
    INVALID_LIFECYCLE_STATUS = "INVALID_LIFECYCLE_STATUS"
    MISSING_MANDATE = "MISSING_MANDATE"
    INSUFFICIENT_MEMBERS = "INSUFFICIENT_MEMBERS"
    DUPLICATE_MEMBER = "DUPLICATE_MEMBER"
    INVALID_SOURCE_RUN_ID = "INVALID_SOURCE_RUN_ID"
    INVALID_WEIGHT = "INVALID_WEIGHT"
    WEIGHT_SUM_MISMATCH = "WEIGHT_SUM_MISMATCH"
    MISSING_EXPLICIT_WEIGHT = "MISSING_EXPLICIT_WEIGHT"
    UNEXPECTED_WEIGHT_IN_EQUAL_MODE = "UNEXPECTED_WEIGHT_IN_EQUAL_MODE"
    MEMBER_ORDER_CONFLICT = "MEMBER_ORDER_CONFLICT"
    CONSTRAINT_CONFLICT = "CONSTRAINT_CONFLICT"
    MAX_MEMBERS_EXCEEDED = "MAX_MEMBERS_EXCEEDED"
    MEMBER_WEIGHT_OUT_OF_BOUNDS = "MEMBER_WEIGHT_OUT_OF_BOUNDS"
    PUBLISHED_AT_REQUIRED = "PUBLISHED_AT_REQUIRED"
    PUBLISHED_AT_NOT_ALLOWED = "PUBLISHED_AT_NOT_ALLOWED"
    INVALID_TIMESTAMP = "INVALID_TIMESTAMP"
    INVALID_SCHEMA_VERSION = "INVALID_SCHEMA_VERSION"
    UNSUPPORTED_SEMANTICS = "UNSUPPORTED_SEMANTICS"


def require_aware_utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        raise ValueError("datetime must be timezone-aware UTC")
    return value.astimezone(timezone.utc)


def is_valid_portfolio_id(portfolio_id: str) -> bool:
    return bool(PORTFOLIO_ID_PATTERN.fullmatch(portfolio_id))


def parse_analytical_weight(value: Any) -> Decimal:
    """Parse a finite analytical weight in ``[0, 1]``.

    Accepts ``Decimal``, ``int`` (0 or 1 only), or decimal string.
    Rejects ``float`` (binary float coercion is unsafe for weight evidence),
    ``bool``, percentages, and out-of-range values. Does not normalize.
    """
    if isinstance(value, bool):
        raise ValueError("analytical_weight must not be a boolean")
    if isinstance(value, float):
        raise ValueError(
            "analytical_weight must be Decimal or decimal string, not float"
        )
    if isinstance(value, int):
        if value not in (0, 1):
            raise ValueError(
                "integer analytical_weight may only be 0 or 1; "
                "use a Decimal or decimal string for fractional weights"
            )
        return Decimal(value)
    if isinstance(value, Decimal):
        weight = value
    elif isinstance(value, str):
        cleaned = value.strip()
        if cleaned != value or not cleaned:
            raise ValueError("analytical_weight string must be non-empty and unpadded")
        if cleaned.endswith("%"):
            raise ValueError("percentage analytical_weight strings are not supported")
        try:
            weight = Decimal(cleaned)
        except InvalidOperation as exc:
            raise ValueError(f"invalid analytical_weight: {value!r}") from exc
    else:
        raise ValueError(f"unsupported analytical_weight type: {type(value)!r}")

    if not weight.is_finite():
        raise ValueError("analytical_weight must be finite")
    if weight < Decimal("0") or weight > Decimal("1"):
        raise ValueError("analytical_weight must be between 0 and 1 inclusive")
    return weight


class PortfolioId(BaseModel):
    """Validated stable portfolio identity.

    Canonical form: ``portfolio_<UTC timestamp>_<8-hex>``
    Example: ``portfolio_20260729T120000Z_a1b2c3d4``
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    value: str

    @field_validator("value")
    @classmethod
    def _validate(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("portfolio_id must be a string")
        if value != value.strip():
            raise ValueError("portfolio_id must not have leading or trailing whitespace")
        if not value:
            raise ValueError("portfolio_id must be non-empty")
        if "/" in value or "\\" in value or ".." in value:
            raise ValueError("portfolio_id must not contain path separators")
        if any(ch.isspace() for ch in value):
            raise ValueError("portfolio_id must not contain whitespace")
        if not is_valid_portfolio_id(value):
            raise ValueError(
                "portfolio_id must match portfolio_<YYYYMMDDTHHMMSSZ>_<8-hex>; "
                f"got {value!r}"
            )
        return value

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, PortfolioId):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)


class PortfolioVersion(BaseModel):
    """Positive immutable publication version (minimum 1)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    value: int

    @field_validator("value", mode="before")
    @classmethod
    def _validate(cls, value: Any) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("portfolio_version must be an integer (no float coercion)")
        if value < 1:
            raise ValueError("portfolio_version must be >= 1")
        return value

    def __int__(self) -> int:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, PortfolioVersion):
            return self.value == other.value
        if isinstance(other, int) and not isinstance(other, bool):
            return self.value == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)


class AnalyticalWeight(BaseModel):
    """Finite analytical weight in ``[0, 1]`` — not execution allocation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    value: Decimal

    @field_validator("value", mode="before")
    @classmethod
    def _validate(cls, value: Any) -> Decimal:
        return parse_analytical_weight(value)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, AnalyticalWeight):
            return self.value == other.value
        if isinstance(other, Decimal):
            return self.value == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)


class PortfolioMandate(BaseModel):
    """Analytical purpose and review boundary of a portfolio."""

    model_config = ConfigDict(extra="forbid")

    name: str
    description: Optional[str] = None
    objective: Optional[str] = None
    benchmark: Optional[str] = None
    rebalance_frequency: RebalanceFrequency
    base_currency: str = "USD"

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned or cleaned != value:
            raise ValueError("mandate name must be non-empty and unpadded")
        return cleaned

    @field_validator("description", "objective", "benchmark")
    @classmethod
    def _optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned or cleaned != value:
            raise ValueError("optional text fields must be non-empty when set and unpadded")
        return cleaned

    @field_validator("base_currency")
    @classmethod
    def _currency(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("base_currency must not have leading or trailing whitespace")
        if not value:
            raise ValueError("base_currency must be non-empty")
        if value != value.upper():
            raise ValueError("base_currency must be uppercase")
        if not re.fullmatch(r"[A-Z]{3}", value):
            raise ValueError("base_currency must be a 3-letter uppercase code")
        return value


class PortfolioMember(BaseModel):
    """Immutable reference to a published research run (MVP provenance seam).

    ``source_run_id`` references Phase 4 published evidence. It is not a permanent
    Strategy identity. Research payloads are never copied into this record.
    """

    model_config = ConfigDict(extra="forbid")

    source_run_id: str
    display_name: Optional[str] = None
    analytical_weight: Optional[AnalyticalWeight] = None
    member_order: int = Field(ge=0)
    selected_snapshot_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("source_run_id")
    @classmethod
    def _run_id(cls, value: str) -> str:
        if value != value.strip() or not value:
            raise ValueError("source_run_id must be non-empty and unpadded")
        if not is_valid_run_id(value):
            raise ValueError(f"invalid source_run_id format: {value!r}")
        return value

    @field_validator("display_name")
    @classmethod
    def _display_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned or cleaned != value:
            raise ValueError("display_name must be non-empty when set and unpadded")
        return cleaned

    @field_validator("analytical_weight", mode="before")
    @classmethod
    def _weight(cls, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, AnalyticalWeight):
            return value
        if isinstance(value, dict):
            return value
        return AnalyticalWeight(value=value)

    @field_validator("selected_snapshot_ids")
    @classmethod
    def _snapshots(cls, value: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for item in value:
            if not is_valid_snapshot_id(item):
                raise ValueError(f"invalid selected snapshot_id: {item!r}")
            if item in seen:
                raise ValueError(f"duplicate selected snapshot_id: {item!r}")
            seen.add(item)
            ordered.append(item)
        return ordered

    @field_validator("metadata")
    @classmethod
    def _metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("metadata must be a mapping")
        forbidden = {
            "buy",
            "sell",
            "execution",
            "order",
            "position",
            "expected_return",
            "target_price",
            "recommendation",
        }
        overlap = forbidden.intersection(str(key).lower() for key in value)
        if overlap:
            raise ValueError(
                "member metadata must not embed execution or recommendation fields: "
                + ", ".join(sorted(overlap))
            )
        return value


class PortfolioConstraintSet(BaseModel):
    """Deterministic portfolio constraints (analytical Guardrails)."""

    model_config = ConfigDict(extra="forbid")

    long_only: bool = True
    fully_invested: bool = True
    allow_cash: bool = False
    maximum_members: Optional[int] = Field(default=None, ge=2)
    minimum_member_weight: Optional[Decimal] = None
    maximum_member_weight: Optional[Decimal] = None
    maximum_sector_weight: Optional[Decimal] = None
    weight_sum_tolerance: Decimal = WEIGHT_SUM_TOLERANCE_DEFAULT

    @field_validator(
        "minimum_member_weight",
        "maximum_member_weight",
        "maximum_sector_weight",
        mode="before",
    )
    @classmethod
    def _optional_weight_bounds(cls, value: Any) -> Any:
        if value is None:
            return None
        return parse_analytical_weight(value)

    @field_validator("weight_sum_tolerance", mode="before")
    @classmethod
    def _tolerance(cls, value: Any) -> Decimal:
        weight = parse_analytical_weight(value)
        if weight <= Decimal("0"):
            raise ValueError("weight_sum_tolerance must be positive")
        if weight > WEIGHT_SUM_TOLERANCE_MAX:
            raise ValueError(
                f"weight_sum_tolerance must be <= {WEIGHT_SUM_TOLERANCE_MAX}"
            )
        return weight

    @model_validator(mode="after")
    def _consistency(self) -> PortfolioConstraintSet:
        if self.long_only is not True:
            raise ValueError("long_only must remain true in the initial Portfolio release")
        if self.fully_invested and self.allow_cash:
            raise ValueError(
                "fully_invested and allow_cash cannot both be true"
            )
        if not self.fully_invested and not self.allow_cash:
            raise ValueError(
                "either fully_invested must be true or allow_cash must be true"
            )
        if (
            self.minimum_member_weight is not None
            and self.maximum_member_weight is not None
            and self.minimum_member_weight > self.maximum_member_weight
        ):
            raise ValueError(
                "minimum_member_weight cannot exceed maximum_member_weight"
            )
        return self


class SelectedSnapshotProvenance(BaseModel):
    """Resolved snapshot evidence admitted for one Portfolio member."""

    model_config = ConfigDict(extra="forbid")

    snapshot_id: str
    checksum: str
    snapshot_type: str
    schema_version: str

    @field_validator("snapshot_id")
    @classmethod
    def _snapshot_id(cls, value: str) -> str:
        if not is_valid_snapshot_id(value):
            raise ValueError(f"invalid snapshot_id format: {value!r}")
        return value

    @field_validator("checksum")
    @classmethod
    def _checksum(cls, value: str) -> str:
        lowered = value.lower()
        if not SHA256_HEX_PATTERN.fullmatch(lowered):
            raise ValueError("checksum must be a 64-character sha256 hex digest")
        return lowered

    @field_validator("snapshot_type", "schema_version")
    @classmethod
    def _nonempty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned or cleaned != value:
            raise ValueError("must be non-empty and unpadded")
        return cleaned


class MemberPublicationProvenance(BaseModel):
    """Per-member admission provenance for a Published Portfolio."""

    model_config = ConfigDict(extra="forbid")

    source_run_id: str
    source_published_at: Optional[datetime] = None
    source_validation_ok: bool
    selected_snapshot_ids: list[str] = Field(default_factory=list)
    selected_snapshot_types: list[str] = Field(default_factory=list)
    selected_snapshot_checksums: list[SelectedSnapshotProvenance] = Field(
        default_factory=list
    )
    source_methodology_version: Optional[str] = None
    resolved_at: datetime

    @field_validator("source_run_id")
    @classmethod
    def _run_id(cls, value: str) -> str:
        if not is_valid_run_id(value):
            raise ValueError(f"invalid source_run_id format: {value!r}")
        return value

    @field_validator("source_published_at", "resolved_at")
    @classmethod
    def _aware(cls, value: Optional[datetime]) -> Optional[datetime]:
        return require_aware_utc(value)

    @field_validator("selected_snapshot_types")
    @classmethod
    def _types(cls, value: list[str]) -> list[str]:
        ordered: list[str] = []
        for item in value:
            cleaned = item.strip()
            if not cleaned or cleaned != item:
                raise ValueError("selected_snapshot_types must be non-empty and unpadded")
            ordered.append(cleaned)
        return ordered

    @field_validator("source_methodology_version")
    @classmethod
    def _method(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned or cleaned != value:
            raise ValueError(
                "source_methodology_version must be non-empty when set and unpadded"
            )
        return cleaned

    @model_validator(mode="after")
    def _selection_lengths(self) -> MemberPublicationProvenance:
        if len(self.selected_snapshot_types) not in (0, len(self.selected_snapshot_ids)):
            raise ValueError(
                "selected_snapshot_types length must match selected_snapshot_ids"
            )
        if len(self.selected_snapshot_checksums) not in (
            0,
            len(self.selected_snapshot_ids),
        ):
            raise ValueError(
                "selected_snapshot_checksums length must match selected_snapshot_ids"
            )
        return self


# Spec aliases used by Phase 5.1C handoff vocabulary.
PortfolioMemberProvenance = MemberPublicationProvenance


class PortfolioPublicationProvenance(BaseModel):
    """Portfolio-level publication provenance (not a Research aggregate copy)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = PORTFOLIO_PUBLICATION_PROVENANCE_SCHEMA_VERSION
    resolved_at: datetime
    members: list[MemberPublicationProvenance] = Field(default_factory=list)

    @field_validator("schema_version")
    @classmethod
    def _schema(cls, value: str) -> str:
        if value != PORTFOLIO_PUBLICATION_PROVENANCE_SCHEMA_VERSION:
            raise ValueError(
                f"unsupported publication provenance schema_version: {value!r}"
            )
        return value

    @field_validator("resolved_at")
    @classmethod
    def _aware(cls, value: datetime) -> datetime:
        result = require_aware_utc(value)
        assert result is not None
        return result


class PortfolioManifest(BaseModel):
    """Canonical operator-defined Portfolio input contract (Phase 5.1).

    Checksums are not caller-authored authoritative fields; infrastructure
    generates them during Phase 5.1B persistence.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: str = PORTFOLIO_MANIFEST_SCHEMA_VERSION
    portfolio_id: str
    portfolio_version: int
    lifecycle_status: PortfolioLifecycleStatus
    mandate: PortfolioMandate
    members: list[PortfolioMember]
    constraints: PortfolioConstraintSet
    weight_method: WeightMethod
    created_at: datetime
    published_at: Optional[datetime] = None
    methodology_version: Optional[str] = None
    publication_provenance: Optional[PortfolioPublicationProvenance] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("schema_version")
    @classmethod
    def _schema(cls, value: str) -> str:
        if value != PORTFOLIO_MANIFEST_SCHEMA_VERSION:
            raise ValueError(
                f"unsupported portfolio manifest schema_version: {value!r}"
            )
        return value

    @field_validator("portfolio_id")
    @classmethod
    def _portfolio_id(cls, value: str) -> str:
        return PortfolioId(value=value).value

    @field_validator("portfolio_version", mode="before")
    @classmethod
    def _version(cls, value: Any) -> int:
        return PortfolioVersion(value=value).value

    @field_validator("created_at", "published_at")
    @classmethod
    def _aware(cls, value: Optional[datetime]) -> Optional[datetime]:
        return require_aware_utc(value)

    @field_validator("methodology_version")
    @classmethod
    def _method_version(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned or cleaned != value:
            raise ValueError("methodology_version must be non-empty when set and unpadded")
        return cleaned

    @field_validator("metadata")
    @classmethod
    def _metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("metadata must be a mapping")
        return value

    @model_validator(mode="after")
    def _lifecycle_timestamps(self) -> PortfolioManifest:
        if self.lifecycle_status == PortfolioLifecycleStatus.PUBLISHED:
            if self.published_at is None:
                raise ValueError("PUBLISHED portfolios require published_at")
        elif self.published_at is not None:
            raise ValueError("DRAFT portfolios must not set published_at")
        if (
            self.lifecycle_status == PortfolioLifecycleStatus.DRAFT
            and self.publication_provenance is not None
        ):
            raise ValueError("DRAFT portfolios must not set publication_provenance")
        return self


class PortfolioSnapshotReference(BaseModel):
    """Reference contract for a portfolio snapshot file (no content, no path)."""

    model_config = ConfigDict(extra="forbid")

    snapshot_id: str
    portfolio_id: str
    portfolio_version: int
    snapshot_type: PortfolioSnapshotType
    schema_version: str = PORTFOLIO_SNAPSHOT_REF_SCHEMA_VERSION
    methodology_version: Optional[str] = None
    created_at: datetime
    content_checksum: Optional[str] = None
    availability: PortfolioSnapshotAvailability

    @field_validator("snapshot_id")
    @classmethod
    def _snapshot_id(cls, value: str) -> str:
        if not is_valid_snapshot_id(value):
            raise ValueError(f"invalid snapshot_id format: {value!r}")
        return value

    @field_validator("portfolio_id")
    @classmethod
    def _portfolio_id(cls, value: str) -> str:
        return PortfolioId(value=value).value

    @field_validator("portfolio_version", mode="before")
    @classmethod
    def _version(cls, value: Any) -> int:
        return PortfolioVersion(value=value).value

    @field_validator("created_at")
    @classmethod
    def _aware(cls, value: datetime) -> datetime:
        result = require_aware_utc(value)
        assert result is not None
        return result

    @field_validator("content_checksum")
    @classmethod
    def _checksum(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        lowered = value.lower()
        if not SHA256_HEX_PATTERN.fullmatch(lowered):
            raise ValueError("content_checksum must be a 64-character sha256 hex digest")
        return lowered


class PortfolioValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: PortfolioValidationIssueCode
    severity: PortfolioValidationSeverity
    field: Optional[str] = None
    message: str
    context: dict[str, Any] = Field(default_factory=dict)

    @field_validator("message")
    @classmethod
    def _message(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("validation issue message must be non-empty")
        return cleaned


class PortfolioValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    issues: list[PortfolioValidationIssue] = Field(default_factory=list)

    @model_validator(mode="after")
    def _derive_ok(self) -> PortfolioValidationResult:
        has_error = any(
            issue.severity == PortfolioValidationSeverity.ERROR for issue in self.issues
        )
        expected = not has_error
        if self.ok != expected:
            # Keep ok authoritative from construction helpers; reject inconsistency.
            raise ValueError(
                f"ok={self.ok} is inconsistent with issue severities "
                f"(expected ok={expected})"
            )
        return self


def manifest_to_dict(manifest: PortfolioManifest) -> dict[str, Any]:
    """Deterministic JSON-compatible dump for later checksum generation."""
    return manifest.model_dump(mode="json")


def manifest_from_dict(payload: dict[str, Any]) -> PortfolioManifest:
    return PortfolioManifest.model_validate(payload)
