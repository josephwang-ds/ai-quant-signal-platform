"""Versioned concept registry for the general operating-company template."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

CONCEPT_REGISTRY_VERSION = "company-lens.fundamentals.concepts.v1"
TEMPLATE_ID = "general_operating_company"
TAXONOMY = "us-gaap"

PeriodKind = Literal["duration", "instant"]
UnitFamily = Literal["USD", "shares"]


@dataclass(frozen=True)
class ReportedConcept:
    metric_id: str
    label: str
    definition: str
    aliases: tuple[str, ...]
    unit_family: UnitFamily
    period_kind: PeriodKind


# Capex convention: SEC PaymentsToAcquirePropertyPlantAndEquipment is typically a
# positive payment magnitude in Company Facts USD units. Store the signed value as
# provided; free-cash-flow derivation subtracts abs(capex) when treating payments.
REPORTED_CONCEPTS: tuple[ReportedConcept, ...] = (
    ReportedConcept(
        metric_id="revenue",
        label="Revenue",
        definition="Net sales / contract revenue for the fiscal year",
        aliases=(
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "SalesRevenueNet",
            "Revenues",
        ),
        unit_family="USD",
        period_kind="duration",
    ),
    ReportedConcept(
        metric_id="gross_profit",
        label="Gross profit",
        definition="Revenue less cost of sales",
        aliases=("GrossProfit",),
        unit_family="USD",
        period_kind="duration",
    ),
    ReportedConcept(
        metric_id="operating_income",
        label="Operating income",
        definition="Operating income (loss)",
        aliases=("OperatingIncomeLoss",),
        unit_family="USD",
        period_kind="duration",
    ),
    ReportedConcept(
        metric_id="net_income",
        label="Net income",
        definition="Net income (loss)",
        aliases=("NetIncomeLoss",),
        unit_family="USD",
        period_kind="duration",
    ),
    ReportedConcept(
        metric_id="operating_cash_flow",
        label="Operating cash flow",
        definition="Net cash provided by (used in) operating activities",
        aliases=("NetCashProvidedByUsedInOperatingActivities",),
        unit_family="USD",
        period_kind="duration",
    ),
    ReportedConcept(
        metric_id="capex",
        label="Capital expenditures",
        definition=(
            "Payments to acquire property, plant and equipment; stored as signed "
            "SEC unit values (typically positive payment amounts)"
        ),
        aliases=("PaymentsToAcquirePropertyPlantAndEquipment",),
        unit_family="USD",
        period_kind="duration",
    ),
    ReportedConcept(
        metric_id="diluted_shares",
        label="Diluted shares",
        definition="Weighted-average diluted shares outstanding",
        aliases=("WeightedAverageNumberOfDilutedSharesOutstanding",),
        unit_family="shares",
        period_kind="duration",
    ),
    ReportedConcept(
        metric_id="total_assets",
        label="Total assets",
        definition="Total assets at fiscal year-end",
        aliases=("Assets",),
        unit_family="USD",
        period_kind="instant",
    ),
    ReportedConcept(
        metric_id="stockholders_equity",
        label="Stockholders' equity",
        definition="Total stockholders' equity at fiscal year-end",
        aliases=("StockholdersEquity",),
        unit_family="USD",
        period_kind="instant",
    ),
    ReportedConcept(
        metric_id="share_based_compensation",
        label="Share-based compensation",
        definition="Share-based compensation expense",
        aliases=("ShareBasedCompensation",),
        unit_family="USD",
        period_kind="duration",
    ),
    ReportedConcept(
        metric_id="share_repurchases",
        label="Share repurchases",
        definition="Payments for repurchase of common stock",
        aliases=("PaymentsForRepurchaseOfCommonStock",),
        unit_family="USD",
        period_kind="duration",
    ),
    ReportedConcept(
        metric_id="dividends_paid",
        label="Dividends paid",
        definition="Cash dividends paid",
        aliases=("PaymentsOfDividends",),
        unit_family="USD",
        period_kind="duration",
    ),
)

REPORTED_BY_ID = {concept.metric_id: concept for concept in REPORTED_CONCEPTS}
