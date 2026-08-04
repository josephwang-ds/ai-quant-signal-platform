"""Deterministic Portfolio manifest validation (Phase 5.1A).

Does **not** verify that referenced research runs exist — that belongs to
Phase 5.1C when Phase 4 query ports are available.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.portfolio.schemas import (
    PORTFOLIO_MANIFEST_SCHEMA_VERSION,
    PortfolioLifecycleStatus,
    PortfolioManifest,
    PortfolioValidationIssue,
    PortfolioValidationIssueCode,
    PortfolioValidationResult,
    PortfolioValidationSeverity,
    WeightMethod,
    is_valid_portfolio_id,
    is_valid_run_id,
)


def _issue(
    code: PortfolioValidationIssueCode,
    message: str,
    *,
    field: str | None = None,
    context: dict[str, Any] | None = None,
    severity: PortfolioValidationSeverity = PortfolioValidationSeverity.ERROR,
) -> PortfolioValidationIssue:
    return PortfolioValidationIssue(
        code=code,
        severity=severity,
        field=field,
        message=message,
        context=context or {},
    )


def _sort_key(issue: PortfolioValidationIssue) -> tuple[str, str, str]:
    return (issue.code.value, issue.field or "", issue.message)


def validate_portfolio_manifest(
    manifest: PortfolioManifest,
) -> PortfolioValidationResult:
    """Validate a complete Portfolio manifest without I/O.

    Returns all deterministically discoverable issues. Ordinary validation
    failures do not raise.
    """
    issues: list[PortfolioValidationIssue] = []

    if manifest.schema_version != PORTFOLIO_MANIFEST_SCHEMA_VERSION:
        issues.append(
            _issue(
                PortfolioValidationIssueCode.INVALID_SCHEMA_VERSION,
                f"unsupported schema_version {manifest.schema_version!r}; "
                f"expected {PORTFOLIO_MANIFEST_SCHEMA_VERSION!r}",
                field="schema_version",
            )
        )

    if not is_valid_portfolio_id(manifest.portfolio_id):
        issues.append(
            _issue(
                PortfolioValidationIssueCode.INVALID_PORTFOLIO_ID,
                f"invalid portfolio_id {manifest.portfolio_id!r}",
                field="portfolio_id",
            )
        )

    if (
        not isinstance(manifest.portfolio_version, int)
        or isinstance(manifest.portfolio_version, bool)
        or manifest.portfolio_version < 1
    ):
        issues.append(
            _issue(
                PortfolioValidationIssueCode.INVALID_VERSION,
                f"portfolio_version must be an integer >= 1; "
                f"got {manifest.portfolio_version!r}",
                field="portfolio_version",
            )
        )

    if manifest.created_at.tzinfo is None:
        issues.append(
            _issue(
                PortfolioValidationIssueCode.INVALID_TIMESTAMP,
                "created_at must be timezone-aware UTC",
                field="created_at",
            )
        )

    if manifest.lifecycle_status == PortfolioLifecycleStatus.PUBLISHED:
        if manifest.published_at is None:
            issues.append(
                _issue(
                    PortfolioValidationIssueCode.PUBLISHED_AT_REQUIRED,
                    "PUBLISHED portfolios require published_at",
                    field="published_at",
                )
            )
        elif manifest.published_at.tzinfo is None:
            issues.append(
                _issue(
                    PortfolioValidationIssueCode.INVALID_TIMESTAMP,
                    "published_at must be timezone-aware UTC",
                    field="published_at",
                )
            )
    elif manifest.published_at is not None:
        issues.append(
            _issue(
                PortfolioValidationIssueCode.PUBLISHED_AT_NOT_ALLOWED,
                "DRAFT portfolios must not set published_at",
                field="published_at",
            )
        )

    if manifest.mandate is None:  # pragma: no cover - forbidden by model
        issues.append(
            _issue(
                PortfolioValidationIssueCode.MISSING_MANDATE,
                "mandate is required",
                field="mandate",
            )
        )

    members = list(manifest.members)
    if len(members) < 2:
        issues.append(
            _issue(
                PortfolioValidationIssueCode.INSUFFICIENT_MEMBERS,
                f"portfolio requires at least two members; found {len(members)}",
                field="members",
                context={"member_count": len(members)},
            )
        )

    constraints = manifest.constraints
    if constraints.maximum_members is not None and len(members) > constraints.maximum_members:
        issues.append(
            _issue(
                PortfolioValidationIssueCode.MAX_MEMBERS_EXCEEDED,
                f"member count {len(members)} exceeds maximum_members "
                f"{constraints.maximum_members}",
                field="members",
                context={
                    "member_count": len(members),
                    "maximum_members": constraints.maximum_members,
                },
            )
        )

    if constraints.long_only is not True:
        issues.append(
            _issue(
                PortfolioValidationIssueCode.UNSUPPORTED_SEMANTICS,
                "long_only must be true; short or leveraged portfolios are unsupported",
                field="constraints.long_only",
            )
        )

    if constraints.fully_invested and constraints.allow_cash:
        issues.append(
            _issue(
                PortfolioValidationIssueCode.CONSTRAINT_CONFLICT,
                "fully_invested and allow_cash cannot both be true",
                field="constraints",
            )
        )
    if not constraints.fully_invested and not constraints.allow_cash:
        issues.append(
            _issue(
                PortfolioValidationIssueCode.CONSTRAINT_CONFLICT,
                "either fully_invested or allow_cash must be true",
                field="constraints",
            )
        )

    if (
        constraints.minimum_member_weight is not None
        and constraints.maximum_member_weight is not None
        and constraints.minimum_member_weight > constraints.maximum_member_weight
    ):
        issues.append(
            _issue(
                PortfolioValidationIssueCode.CONSTRAINT_CONFLICT,
                "minimum_member_weight cannot exceed maximum_member_weight",
                field="constraints",
            )
        )

    if constraints.weight_sum_tolerance <= Decimal("0"):
        issues.append(
            _issue(
                PortfolioValidationIssueCode.CONSTRAINT_CONFLICT,
                "weight_sum_tolerance must be positive",
                field="constraints.weight_sum_tolerance",
            )
        )

    seen_runs: set[str] = set()
    seen_orders: set[int] = set()
    weights: list[Decimal] = []
    missing_explicit = False
    unexpected_equal_weight = False

    for index, member in enumerate(members):
        field_prefix = f"members[{index}]"

        if not is_valid_run_id(member.source_run_id):
            issues.append(
                _issue(
                    PortfolioValidationIssueCode.INVALID_SOURCE_RUN_ID,
                    f"invalid source_run_id {member.source_run_id!r}",
                    field=f"{field_prefix}.source_run_id",
                )
            )
        elif member.source_run_id in seen_runs:
            issues.append(
                _issue(
                    PortfolioValidationIssueCode.DUPLICATE_MEMBER,
                    f"duplicate source_run_id {member.source_run_id!r}",
                    field=f"{field_prefix}.source_run_id",
                    context={"source_run_id": member.source_run_id},
                )
            )
        else:
            seen_runs.add(member.source_run_id)

        if member.member_order in seen_orders:
            issues.append(
                _issue(
                    PortfolioValidationIssueCode.MEMBER_ORDER_CONFLICT,
                    f"duplicate member_order {member.member_order}",
                    field=f"{field_prefix}.member_order",
                    context={"member_order": member.member_order},
                )
            )
        else:
            seen_orders.add(member.member_order)

        weight_value = (
            member.analytical_weight.value
            if member.analytical_weight is not None
            else None
        )

        if manifest.weight_method == WeightMethod.EQUAL:
            if weight_value is not None:
                unexpected_equal_weight = True
                issues.append(
                    _issue(
                        PortfolioValidationIssueCode.UNEXPECTED_WEIGHT_IN_EQUAL_MODE,
                        "equal weight_method requires omitted analytical_weight on members; "
                        "equal materialization belongs to later builders",
                        field=f"{field_prefix}.analytical_weight",
                    )
                )
        else:
            if weight_value is None:
                missing_explicit = True
                issues.append(
                    _issue(
                        PortfolioValidationIssueCode.MISSING_EXPLICIT_WEIGHT,
                        "operator_specified weight_method requires analytical_weight "
                        "on every member",
                        field=f"{field_prefix}.analytical_weight",
                    )
                )
            else:
                if weight_value < Decimal("0") or weight_value > Decimal("1"):
                    issues.append(
                        _issue(
                            PortfolioValidationIssueCode.INVALID_WEIGHT,
                            f"analytical_weight {weight_value} is outside [0, 1]",
                            field=f"{field_prefix}.analytical_weight",
                        )
                    )
                if (
                    constraints.minimum_member_weight is not None
                    and weight_value < constraints.minimum_member_weight
                ):
                    issues.append(
                        _issue(
                            PortfolioValidationIssueCode.MEMBER_WEIGHT_OUT_OF_BOUNDS,
                            f"analytical_weight {weight_value} is below "
                            f"minimum_member_weight {constraints.minimum_member_weight}",
                            field=f"{field_prefix}.analytical_weight",
                        )
                    )
                if (
                    constraints.maximum_member_weight is not None
                    and weight_value > constraints.maximum_member_weight
                ):
                    issues.append(
                        _issue(
                            PortfolioValidationIssueCode.MEMBER_WEIGHT_OUT_OF_BOUNDS,
                            f"analytical_weight {weight_value} exceeds "
                            f"maximum_member_weight {constraints.maximum_member_weight}",
                            field=f"{field_prefix}.analytical_weight",
                        )
                    )
                weights.append(weight_value)

    if (
        manifest.weight_method == WeightMethod.OPERATOR_SPECIFIED
        and not missing_explicit
        and len(weights) == len(members)
        and len(members) >= 1
    ):
        total = sum(weights, start=Decimal("0"))
        tolerance = constraints.weight_sum_tolerance
        if constraints.fully_invested:
            if abs(total - Decimal("1")) > tolerance:
                issues.append(
                    _issue(
                        PortfolioValidationIssueCode.WEIGHT_SUM_MISMATCH,
                        f"member analytical weights sum to {total}, outside the "
                        f"allowed tolerance of {tolerance} around 1 for a "
                        f"fully_invested portfolio",
                        field="members",
                        context={
                            "weight_sum": str(total),
                            "tolerance": str(tolerance),
                            "fully_invested": True,
                        },
                    )
                )
        elif constraints.allow_cash:
            if total - Decimal("1") > tolerance:
                issues.append(
                    _issue(
                        PortfolioValidationIssueCode.WEIGHT_SUM_MISMATCH,
                        f"member analytical weights sum to {total}, which exceeds "
                        f"1 by more than the allowed tolerance of {tolerance}",
                        field="members",
                        context={
                            "weight_sum": str(total),
                            "tolerance": str(tolerance),
                            "allow_cash": True,
                        },
                    )
                )
            if total < Decimal("0"):
                issues.append(
                    _issue(
                        PortfolioValidationIssueCode.WEIGHT_SUM_MISMATCH,
                        f"member analytical weights sum to {total}, which is negative",
                        field="members",
                        context={"weight_sum": str(total)},
                    )
                )

    # Quiet unused flag (issues already recorded per member).
    _ = unexpected_equal_weight

    issues_sorted = sorted(issues, key=_sort_key)
    return PortfolioValidationResult(
        ok=not any(
            issue.severity == PortfolioValidationSeverity.ERROR for issue in issues_sorted
        ),
        issues=issues_sorted,
    )
