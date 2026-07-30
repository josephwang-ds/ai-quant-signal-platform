"""Deterministic performance attribution and robust anomaly detection."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from math import copysign
from statistics import median, pstdev

from app.post_trade.schemas import (
    AnomalyDetectionRequest,
    AnomalyDetectionResult,
    AnomalyEvent,
    AttributionComponent,
    AttributionGroup,
    AttributionObservation,
    AttributionRequest,
    AttributionResult,
    DetectionDirection,
    MetricObservation,
    MetricSeriesSummary,
)

BPS_DENOMINATOR = 10_000.0
ROBUST_MAD_SCALE = 1.4826
ZERO_SCALE_SCORE = 999.0


def _usd(notional: float, bps: float) -> float:
    return notional * bps / BPS_DENOMINATOR


@dataclass(frozen=True)
class _AttributionTotals:
    notional: float
    gross_edge_usd: float
    fees_usd: float
    slippage_usd: float

    @property
    def net_active_usd(self) -> float:
        return self.gross_edge_usd - self.fees_usd - self.slippage_usd

    def bps(self, amount_usd: float) -> float:
        return amount_usd / self.notional * BPS_DENOMINATOR


def _attribution_totals(
    observations: list[AttributionObservation],
) -> _AttributionTotals:
    notional = sum(item.notional_usd for item in observations)
    gross_edge = sum(
        _usd(
            item.notional_usd,
            item.gross_pnl_bps - item.benchmark_pnl_bps,
        )
        for item in observations
    )
    fees = sum(_usd(item.notional_usd, item.fees_bps) for item in observations)
    slippage = sum(
        _usd(item.notional_usd, item.slippage_bps) for item in observations
    )
    return _AttributionTotals(
        notional=notional,
        gross_edge_usd=gross_edge,
        fees_usd=fees,
        slippage_usd=slippage,
    )


def _round(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


def run_performance_attribution(request: AttributionRequest) -> AttributionResult:
    """Reconcile notional-weighted active PnL into edge, fees, and slippage."""
    totals = _attribution_totals(request.observations)
    group_rows: dict[str, list[AttributionObservation]] = defaultdict(list)
    for item in request.observations:
        group_rows[getattr(item, request.group_by)].append(item)

    groups: list[AttributionGroup] = []
    for group, rows in group_rows.items():
        subtotal = _attribution_totals(rows)
        groups.append(
            AttributionGroup(
                group=group,
                observation_count=len(rows),
                notional_usd=_round(subtotal.notional, 2),
                gross_edge_bps=_round(subtotal.bps(subtotal.gross_edge_usd)),
                fee_drag_bps=_round(-subtotal.bps(subtotal.fees_usd)),
                slippage_drag_bps=_round(-subtotal.bps(subtotal.slippage_usd)),
                net_active_bps=_round(subtotal.bps(subtotal.net_active_usd)),
                net_active_usd=_round(subtotal.net_active_usd, 2),
            )
        )
    groups.sort(key=lambda item: (-item.notional_usd, item.group))

    gross_edge_bps = totals.bps(totals.gross_edge_usd)
    fee_drag_bps = -totals.bps(totals.fees_usd)
    slippage_drag_bps = -totals.bps(totals.slippage_usd)
    net_active_bps = totals.bps(totals.net_active_usd)
    reconciled_usd = (
        totals.gross_edge_usd - totals.fees_usd - totals.slippage_usd
    )

    return AttributionResult(
        methodology=(
            "Notional-weighted active PnL: gross strategy PnL minus benchmark, "
            "fees, and realized slippage. Components reconcile in USD."
        ),
        input_data_kind=request.input_data_kind,
        group_by=request.group_by,
        observation_count=len(request.observations),
        total_notional_usd=_round(totals.notional, 2),
        gross_edge_bps=_round(gross_edge_bps),
        fee_drag_bps=_round(fee_drag_bps),
        slippage_drag_bps=_round(slippage_drag_bps),
        net_active_bps=_round(net_active_bps),
        net_active_usd=_round(totals.net_active_usd, 2),
        reconciliation_error_usd=_round(totals.net_active_usd - reconciled_usd, 10),
        components=[
            AttributionComponent(
                key="gross_edge",
                label="Gross edge vs benchmark",
                contribution_bps=_round(gross_edge_bps),
                contribution_usd=_round(totals.gross_edge_usd, 2),
            ),
            AttributionComponent(
                key="fees",
                label="Fees",
                contribution_bps=_round(fee_drag_bps),
                contribution_usd=_round(-totals.fees_usd, 2),
            ),
            AttributionComponent(
                key="slippage",
                label="Slippage",
                contribution_bps=_round(slippage_drag_bps),
                contribution_usd=_round(-totals.slippage_usd, 2),
            ),
            AttributionComponent(
                key="net_active",
                label="Net active PnL",
                contribution_bps=_round(net_active_bps),
                contribution_usd=_round(totals.net_active_usd, 2),
            ),
        ],
        groups=groups,
    )


def _robust_score(value: float, history: list[float]) -> tuple[float, float, float]:
    center = float(median(history))
    mad = float(median(abs(item - center) for item in history))
    scale = ROBUST_MAD_SCALE * mad
    if scale <= 0:
        scale = float(pstdev(history))
    if scale <= 0:
        score = 0.0 if value == center else copysign(ZERO_SCALE_SCORE, value - center)
        return center, 0.0, score
    return center, scale, (value - center) / scale


def _is_anomaly(
    score: float,
    *,
    direction: DetectionDirection,
    threshold: float,
) -> bool:
    if direction is DetectionDirection.HIGH:
        return score >= threshold
    if direction is DetectionDirection.LOW:
        return score <= -threshold
    return abs(score) >= threshold


def _series_status(events: list[AnomalyEvent], scored_count: int) -> str:
    if scored_count == 0:
        return "insufficient_history"
    if any(item.severity == "critical" for item in events):
        return "critical"
    if events:
        return "warning"
    return "normal"


def detect_anomalies(request: AnomalyDetectionRequest) -> AnomalyDetectionResult:
    """Detect degradation with a past-only rolling median/MAD baseline."""
    grouped: dict[tuple[str, str], list[MetricObservation]] = defaultdict(list)
    for item in request.observations:
        grouped[(item.metric, item.entity)].append(item)

    anomalies: list[AnomalyEvent] = []
    summaries: list[MetricSeriesSummary] = []
    scored_total = 0

    for (metric, entity), unsorted_rows in sorted(grouped.items()):
        rows = sorted(unsorted_rows, key=lambda item: item.timestamp)
        history: list[float] = []
        series_events: list[AnomalyEvent] = []
        latest_center = None
        latest_score = None
        scored_count = 0

        for item in rows:
            baseline = history[-request.baseline_window :]
            if len(baseline) >= request.minimum_history:
                center, scale, score = _robust_score(item.value, baseline)
                latest_center = center
                latest_score = score
                scored_count += 1
                scored_total += 1
                if _is_anomaly(
                    score,
                    direction=request.direction,
                    threshold=request.threshold,
                ):
                    severity = (
                        "critical"
                        if abs(score) >= request.threshold * 1.5
                        else "warning"
                    )
                    event = AnomalyEvent(
                        timestamp=item.timestamp,
                        metric=metric,
                        entity=entity,
                        value=_round(item.value),
                        baseline_median=_round(center),
                        robust_scale=_round(scale),
                        robust_z_score=_round(score),
                        severity=severity,
                        history_count=len(baseline),
                    )
                    anomalies.append(event)
                    series_events.append(event)
            history.append(item.value)

        summaries.append(
            MetricSeriesSummary(
                metric=metric,
                entity=entity,
                observation_count=len(rows),
                scored_count=scored_count,
                anomaly_count=len(series_events),
                latest_value=_round(rows[-1].value),
                latest_baseline_median=(
                    _round(latest_center) if latest_center is not None else None
                ),
                latest_robust_z_score=(
                    _round(latest_score) if latest_score is not None else None
                ),
                status=_series_status(series_events, scored_count),
            )
        )

    anomalies.sort(key=lambda item: (item.timestamp, item.metric, item.entity))
    return AnomalyDetectionResult(
        methodology=(
            "Past-only rolling robust z-score using median and MAD; standard "
            "deviation is used only when MAD is zero. No future observations "
            "enter a baseline."
        ),
        input_data_kind=request.input_data_kind,
        baseline_window=request.baseline_window,
        minimum_history=request.minimum_history,
        threshold=request.threshold,
        direction=request.direction,
        observation_count=len(request.observations),
        scored_count=scored_total,
        anomaly_count=len(anomalies),
        anomalies=anomalies,
        series=summaries,
    )
