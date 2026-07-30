"""Phase 5.1A — Portfolio domain and contract tests."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.intelligence.schemas import ResearchSnapshotType
from app.portfolio.schemas import (
    PORTFOLIO_MANIFEST_SCHEMA_VERSION,
    AnalyticalWeight,
    PortfolioConstraintSet,
    PortfolioId,
    PortfolioLifecycleStatus,
    PortfolioMandate,
    PortfolioManifest,
    PortfolioMember,
    PortfolioSnapshotAvailability,
    PortfolioSnapshotReference,
    PortfolioSnapshotType,
    PortfolioValidationIssue,
    PortfolioValidationIssueCode,
    PortfolioValidationResult,
    PortfolioValidationSeverity,
    PortfolioVersion,
    RebalanceFrequency,
    WeightMethod,
    is_valid_portfolio_id,
    manifest_from_dict,
    manifest_to_dict,
)
from app.portfolio.validation import validate_portfolio_manifest

AWARE = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
PORTFOLIO_ID = "portfolio_20260729T120000Z_a1b2c3d4"
RUN_A = "run_20260728T041530Z_aaaaaaaa"
RUN_B = "run_20260728T041530Z_bbbbbbbb"
SNAP_A = "snapshot_aaaaaaaa"
SNAP_B = "snapshot_bbbbbbbb"


def _mandate(**overrides) -> PortfolioMandate:
    payload = {
        "name": "Cross-Sectional Factor Basket",
        "description": "Research review basket of published factor runs",
        "objective": "Compare analytical exposure across published research runs",
        "benchmark": "EQUAL_WEIGHT_UNIVERSE",
        "rebalance_frequency": RebalanceFrequency.MONTHLY,
        "base_currency": "USD",
    }
    payload.update(overrides)
    return PortfolioMandate(**payload)


def _constraints(**overrides) -> PortfolioConstraintSet:
    payload = {
        "long_only": True,
        "fully_invested": True,
        "allow_cash": False,
        "maximum_members": 10,
        "minimum_member_weight": Decimal("0.05"),
        "maximum_member_weight": Decimal("0.80"),
        "weight_sum_tolerance": Decimal("0.000001"),
    }
    payload.update(overrides)
    return PortfolioConstraintSet(**payload)


def _member(
    run_id: str,
    order: int,
    *,
    weight: Decimal | None = None,
    snapshots: list[str] | None = None,
) -> PortfolioMember:
    return PortfolioMember(
        source_run_id=run_id,
        display_name=f"Member {order}",
        analytical_weight=None if weight is None else AnalyticalWeight(value=weight),
        member_order=order,
        selected_snapshot_ids=snapshots or [],
    )


def _manifest(**overrides) -> PortfolioManifest:
    payload = {
        "schema_version": PORTFOLIO_MANIFEST_SCHEMA_VERSION,
        "portfolio_id": PORTFOLIO_ID,
        "portfolio_version": 1,
        "lifecycle_status": PortfolioLifecycleStatus.DRAFT,
        "mandate": _mandate(),
        "members": [
            _member(RUN_A, 0, weight=Decimal("0.5"), snapshots=[SNAP_A]),
            _member(RUN_B, 1, weight=Decimal("0.5"), snapshots=[SNAP_B]),
        ],
        "constraints": _constraints(),
        "weight_method": WeightMethod.OPERATOR_SPECIFIED,
        "created_at": AWARE,
        "published_at": None,
        "methodology_version": "portfolio-methodology/v1",
        "metadata": {},
    }
    payload.update(overrides)
    return PortfolioManifest(**payload)


# --- Identity ---


def test_valid_portfolio_id():
    pid = PortfolioId(value=PORTFOLIO_ID)
    assert pid.value == PORTFOLIO_ID
    assert is_valid_portfolio_id(PORTFOLIO_ID)
    assert pid == PORTFOLIO_ID
    assert hash(pid) == hash(PortfolioId(value=PORTFOLIO_ID))


@pytest.mark.parametrize(
    "bad",
    [
        "",
        " portfolio_20260729T120000Z_a1b2c3d4",
        "portfolio_20260729T120000Z_a1b2c3d4 ",
        "portfolio_20260729T120000Z_a1b2c3d4/x",
        "portfolio_../evil",
        "run_20260729T120000Z_a1b2c3d4",
        "portfolio_short",
        "portfolio_20260729T120000Z_AAAAAAA1",
    ],
)
def test_invalid_portfolio_id(bad: str):
    with pytest.raises(ValidationError):
        PortfolioId(value=bad)


# --- Version ---


def test_version_one_accepted():
    assert PortfolioVersion(value=1).value == 1


@pytest.mark.parametrize("bad", [0, -1, 1.5, True, "1"])
def test_version_rejects_invalid(bad):
    with pytest.raises(ValidationError):
        PortfolioVersion(value=bad)


# --- Lifecycle timestamps via manifest construction ---


def test_draft_without_published_at_accepted():
    manifest = _manifest(
        weight_method=WeightMethod.EQUAL,
        members=[_member(RUN_A, 0), _member(RUN_B, 1)],
    )
    assert manifest.lifecycle_status is PortfolioLifecycleStatus.DRAFT
    assert manifest.published_at is None


def test_published_with_timestamp_accepted():
    manifest = _manifest(
        lifecycle_status=PortfolioLifecycleStatus.PUBLISHED,
        published_at=AWARE,
        weight_method=WeightMethod.EQUAL,
        members=[_member(RUN_A, 0), _member(RUN_B, 1)],
    )
    assert manifest.published_at == AWARE


def test_published_without_timestamp_rejected():
    with pytest.raises(ValidationError):
        _manifest(
            lifecycle_status=PortfolioLifecycleStatus.PUBLISHED,
            published_at=None,
            weight_method=WeightMethod.EQUAL,
            members=[_member(RUN_A, 0), _member(RUN_B, 1)],
        )


def test_draft_with_published_at_rejected():
    with pytest.raises(ValidationError):
        _manifest(
            lifecycle_status=PortfolioLifecycleStatus.DRAFT,
            published_at=AWARE,
            weight_method=WeightMethod.EQUAL,
            members=[_member(RUN_A, 0), _member(RUN_B, 1)],
        )


def test_unknown_lifecycle_rejected():
    with pytest.raises(ValidationError):
        _manifest(lifecycle_status="ACTIVE")


# --- Membership ---


def test_two_valid_members_accepted():
    result = validate_portfolio_manifest(
        _manifest(
            weight_method=WeightMethod.EQUAL,
            members=[_member(RUN_A, 0), _member(RUN_B, 1)],
        )
    )
    assert result.ok


def test_one_member_rejected():
    result = validate_portfolio_manifest(
        PortfolioManifest.model_construct(
            schema_version=PORTFOLIO_MANIFEST_SCHEMA_VERSION,
            portfolio_id=PORTFOLIO_ID,
            portfolio_version=1,
            lifecycle_status=PortfolioLifecycleStatus.DRAFT,
            mandate=_mandate(),
            members=[_member(RUN_A, 0)],
            constraints=_constraints(),
            weight_method=WeightMethod.EQUAL,
            created_at=AWARE,
            published_at=None,
            methodology_version=None,
            metadata={},
        )
    )
    assert not result.ok
    assert any(
        i.code is PortfolioValidationIssueCode.INSUFFICIENT_MEMBERS for i in result.issues
    )


def test_duplicate_run_references_rejected():
    result = validate_portfolio_manifest(
        _manifest(
            weight_method=WeightMethod.EQUAL,
            members=[_member(RUN_A, 0), _member(RUN_A, 1)],
        )
    )
    assert not result.ok
    assert any(i.code is PortfolioValidationIssueCode.DUPLICATE_MEMBER for i in result.issues)


def test_invalid_run_reference_rejected_at_construction():
    with pytest.raises(ValidationError):
        _member("not-a-run", 0)


def test_member_order_conflict_rejected():
    result = validate_portfolio_manifest(
        _manifest(
            weight_method=WeightMethod.EQUAL,
            members=[_member(RUN_A, 0), _member(RUN_B, 0)],
        )
    )
    assert not result.ok
    assert any(
        i.code is PortfolioValidationIssueCode.MEMBER_ORDER_CONFLICT for i in result.issues
    )


# --- Weights ---


def test_equal_weight_mode_with_omitted_weights():
    result = validate_portfolio_manifest(
        _manifest(
            weight_method=WeightMethod.EQUAL,
            members=[_member(RUN_A, 0), _member(RUN_B, 1)],
        )
    )
    assert result.ok


def test_operator_specified_weights_valid():
    result = validate_portfolio_manifest(_manifest())
    assert result.ok


def test_negative_weight_rejected():
    with pytest.raises(ValidationError):
        AnalyticalWeight(value=Decimal("-0.1"))


def test_weight_above_one_rejected():
    with pytest.raises(ValidationError):
        AnalyticalWeight(value=Decimal("1.01"))


def test_float_weight_rejected():
    with pytest.raises(ValidationError):
        AnalyticalWeight(value=0.5)


def test_weight_sum_below_tolerance_rejected():
    result = validate_portfolio_manifest(
        _manifest(
            members=[
                _member(RUN_A, 0, weight=Decimal("0.40")),
                _member(RUN_B, 1, weight=Decimal("0.40")),
            ]
        )
    )
    assert not result.ok
    assert any(
        i.code is PortfolioValidationIssueCode.WEIGHT_SUM_MISMATCH for i in result.issues
    )


def test_weight_sum_above_tolerance_rejected():
    result = validate_portfolio_manifest(
        _manifest(
            members=[
                _member(RUN_A, 0, weight=Decimal("0.60")),
                _member(RUN_B, 1, weight=Decimal("0.60")),
            ]
        )
    )
    assert not result.ok
    assert any(
        i.code is PortfolioValidationIssueCode.WEIGHT_SUM_MISMATCH for i in result.issues
    )


def test_weight_sum_within_tolerance_accepted():
    result = validate_portfolio_manifest(
        _manifest(
            constraints=_constraints(weight_sum_tolerance=Decimal("0.001")),
            members=[
                _member(RUN_A, 0, weight=Decimal("0.5005")),
                _member(RUN_B, 1, weight=Decimal("0.4995")),
            ],
        )
    )
    assert result.ok


def test_missing_explicit_weight_rejected_in_operator_mode():
    result = validate_portfolio_manifest(
        _manifest(
            weight_method=WeightMethod.OPERATOR_SPECIFIED,
            members=[_member(RUN_A, 0), _member(RUN_B, 1, weight=Decimal("1"))],
        )
    )
    assert not result.ok
    assert any(
        i.code is PortfolioValidationIssueCode.MISSING_EXPLICIT_WEIGHT for i in result.issues
    )


def test_equal_mode_rejects_materialized_weights():
    result = validate_portfolio_manifest(
        _manifest(
            weight_method=WeightMethod.EQUAL,
            members=[
                _member(RUN_A, 0, weight=Decimal("0.5")),
                _member(RUN_B, 1, weight=Decimal("0.5")),
            ],
        )
    )
    assert not result.ok
    assert any(
        i.code is PortfolioValidationIssueCode.UNEXPECTED_WEIGHT_IN_EQUAL_MODE
        for i in result.issues
    )


def test_no_automatic_normalization_from_percent_string():
    with pytest.raises(ValidationError):
        AnalyticalWeight(value="25%")


# --- Constraints ---


def test_minimum_above_maximum_rejected():
    with pytest.raises(ValidationError):
        _constraints(
            minimum_member_weight=Decimal("0.5"),
            maximum_member_weight=Decimal("0.2"),
        )


def test_max_members_below_count_rejected():
    result = validate_portfolio_manifest(
        _manifest(
            weight_method=WeightMethod.EQUAL,
            members=[_member(RUN_A, 0), _member(RUN_B, 1)],
            constraints=_constraints(maximum_members=2),
        )
    )
    # exactly at max is ok
    assert result.ok

    result = validate_portfolio_manifest(
        _manifest(
            weight_method=WeightMethod.EQUAL,
            members=[
                _member(RUN_A, 0),
                _member(RUN_B, 1),
                _member("run_20260728T041530Z_cccccccc", 2),
            ],
            constraints=_constraints(maximum_members=2),
        )
    )
    assert not result.ok
    assert any(
        i.code is PortfolioValidationIssueCode.MAX_MEMBERS_EXCEEDED for i in result.issues
    )


def test_short_enabled_rejected():
    with pytest.raises(ValidationError):
        _constraints(long_only=False)


def test_fully_invested_and_cash_conflict():
    with pytest.raises(ValidationError):
        _constraints(fully_invested=True, allow_cash=True)


def test_invalid_tolerance_rejected():
    with pytest.raises(ValidationError):
        _constraints(weight_sum_tolerance=Decimal("0"))
    with pytest.raises(ValidationError):
        _constraints(weight_sum_tolerance=Decimal("0.5"))


def test_allow_cash_weight_sum_may_be_below_one():
    result = validate_portfolio_manifest(
        _manifest(
            constraints=_constraints(
                fully_invested=False,
                allow_cash=True,
                minimum_member_weight=Decimal("0.05"),
            ),
            members=[
                _member(RUN_A, 0, weight=Decimal("0.40")),
                _member(RUN_B, 1, weight=Decimal("0.40")),
            ],
        )
    )
    assert result.ok


# --- Snapshot types ---


def test_research_snapshot_enum_unchanged():
    assert {item.value for item in ResearchSnapshotType} == {
        "research_summary",
        "signal",
    }


def test_portfolio_snapshot_enum_values():
    assert {item.value for item in PortfolioSnapshotType} == {
        "portfolio_summary",
        "portfolio_membership",
        "portfolio_weights",
        "portfolio_exposure",
        "portfolio_constraints",
        "portfolio_risk",
        "portfolio_review",
        "portfolio_backtest",
    }


def test_snapshot_availability_and_reference_round_trip():
    ref = PortfolioSnapshotReference(
        snapshot_id=SNAP_A,
        portfolio_id=PORTFOLIO_ID,
        portfolio_version=1,
        snapshot_type=PortfolioSnapshotType.PORTFOLIO_SUMMARY,
        created_at=AWARE,
        content_checksum="a" * 64,
        availability=PortfolioSnapshotAvailability.AVAILABLE,
    )
    dumped = ref.model_dump(mode="json")
    restored = PortfolioSnapshotReference.model_validate(dumped)
    assert restored == ref
    assert dumped["availability"] == "AVAILABLE"
    assert dumped["snapshot_type"] == "portfolio_summary"


# --- Validation result ---


def test_validation_result_deterministic_ordering_and_multiple_issues():
    result = validate_portfolio_manifest(
        PortfolioManifest.model_construct(
            schema_version="wrong/v0",
            portfolio_id="bad-id",
            portfolio_version=0,
            lifecycle_status=PortfolioLifecycleStatus.PUBLISHED,
            mandate=_mandate(),
            members=[_member(RUN_A, 0)],
            constraints=_constraints(),
            weight_method=WeightMethod.OPERATOR_SPECIFIED,
            created_at=AWARE,
            published_at=None,
            methodology_version=None,
            metadata={},
        )
    )
    assert not result.ok
    assert len(result.issues) >= 3
    codes = [issue.code.value for issue in result.issues]
    assert codes == sorted(codes)
    assert result.ok is False


def test_validation_result_ok_inconsistent_with_errors_rejected():
    with pytest.raises(ValidationError):
        PortfolioValidationResult(
            ok=True,
            issues=[
                PortfolioValidationIssue(
                    code=PortfolioValidationIssueCode.INVALID_PORTFOLIO_ID,
                    severity=PortfolioValidationSeverity.ERROR,
                    message="bad",
                )
            ],
        )


# --- Serialization ---


def test_manifest_round_trip_and_stable_member_order():
    manifest = _manifest(
        weight_method=WeightMethod.EQUAL,
        members=[_member(RUN_A, 0), _member(RUN_B, 1)],
    )
    payload = manifest_to_dict(manifest)
    restored = manifest_from_dict(payload)
    assert restored.model_dump(mode="json") == payload
    assert payload["created_at"].endswith("+00:00") or payload["created_at"].endswith("Z")
    assert [m["source_run_id"] for m in payload["members"]] == [RUN_A, RUN_B]
    assert payload["weight_method"] == "equal"


def test_mutable_default_leakage_absent():
    a = _member(RUN_A, 0)
    b = _member(RUN_B, 1)
    a.selected_snapshot_ids.append(SNAP_A)
    assert b.selected_snapshot_ids == []
    a.metadata["x"] = 1
    assert b.metadata == {}


def test_naive_timestamp_rejected():
    with pytest.raises(ValidationError):
        _manifest(created_at=datetime(2026, 7, 29, 12, 0, 0))
