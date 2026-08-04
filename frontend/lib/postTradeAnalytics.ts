import {
  API_REQUEST_TIMEOUT_MS,
  requestJson,
} from "@/lib/apiRequest";
import type {
  AnomalyDetectionRequest,
  AnomalyDetectionResult,
  AttributionRequest,
  AttributionResult,
  MetricObservation,
} from "@/types/postTradeAnalytics";

const BASE_TIME = Date.UTC(2026, 6, 29, 1, 30, 0);

function timestampAt(minutes: number): string {
  return new Date(BASE_TIME + minutes * 60_000).toISOString();
}

export const DEMO_ATTRIBUTION_REQUEST: AttributionRequest = {
  input_data_kind: "synthetic_demo",
  group_by: "venue",
  observations: [
    {
      trade_id: "pta-001",
      timestamp: timestampAt(0),
      strategy: "Cross-sectional momentum",
      venue: "XNAS",
      notional_usd: 1_250_000,
      gross_pnl_bps: 7.8,
      benchmark_pnl_bps: 1.6,
      fees_bps: 0.35,
      slippage_bps: 0.82,
    },
    {
      trade_id: "pta-002",
      timestamp: timestampAt(4),
      strategy: "Cross-sectional momentum",
      venue: "BATS",
      notional_usd: 980_000,
      gross_pnl_bps: 5.2,
      benchmark_pnl_bps: 1.4,
      fees_bps: 0.31,
      slippage_bps: 0.46,
    },
    {
      trade_id: "pta-003",
      timestamp: timestampAt(8),
      strategy: "Low-volatility factor",
      venue: "XNYS",
      notional_usd: 1_500_000,
      gross_pnl_bps: 4.1,
      benchmark_pnl_bps: 1.2,
      fees_bps: 0.29,
      slippage_bps: 0.58,
    },
    {
      trade_id: "pta-004",
      timestamp: timestampAt(13),
      strategy: "Low-volatility factor",
      venue: "XNAS",
      notional_usd: 1_100_000,
      gross_pnl_bps: 2.8,
      benchmark_pnl_bps: 1.1,
      fees_bps: 0.36,
      slippage_bps: 1.25,
    },
    {
      trade_id: "pta-005",
      timestamp: timestampAt(18),
      strategy: "Cross-sectional momentum",
      venue: "BATS",
      notional_usd: 1_320_000,
      gross_pnl_bps: 6.4,
      benchmark_pnl_bps: 1.7,
      fees_bps: 0.33,
      slippage_bps: 0.51,
    },
    {
      trade_id: "pta-006",
      timestamp: timestampAt(23),
      strategy: "Low-volatility factor",
      venue: "XNYS",
      notional_usd: 870_000,
      gross_pnl_bps: 3.5,
      benchmark_pnl_bps: 1.3,
      fees_bps: 0.28,
      slippage_bps: 0.63,
    },
  ],
};

function metricSeries(
  entity: string,
  values: number[],
  offsetMinutes = 0
): MetricObservation[] {
  return values.map((value, index) => ({
    timestamp: timestampAt(offsetMinutes + index),
    metric: "ack_latency_ms",
    entity,
    value,
  }));
}

export const DEMO_ANOMALY_REQUEST: AnomalyDetectionRequest = {
  input_data_kind: "synthetic_demo",
  baseline_window: 12,
  minimum_history: 6,
  threshold: 3.5,
  direction: "high",
  observations: [
    ...metricSeries("gateway-a", [
      1.2, 1.18, 1.24, 1.21, 1.19, 1.23, 1.2, 1.22, 1.17, 1.21, 1.2, 1.24,
      1.19, 1.23, 3.85, 1.26, 1.22, 1.2,
    ]),
    ...metricSeries("gateway-b", [
      1.42, 1.38, 1.45, 1.41, 1.4, 1.43, 1.39, 1.44, 1.42, 1.41, 1.43, 1.4,
      1.46, 1.42, 1.44, 1.41, 1.43, 1.42,
    ]),
  ],
};

export async function fetchPerformanceAttribution(
  request: AttributionRequest = DEMO_ATTRIBUTION_REQUEST,
  signal?: AbortSignal
): Promise<AttributionResult> {
  return requestJson<AttributionResult>(
    "/api/v1/post-trade/attribution",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
      signal,
    },
    { timeoutMs: API_REQUEST_TIMEOUT_MS }
  );
}

export async function fetchAnomalyDetection(
  request: AnomalyDetectionRequest = DEMO_ANOMALY_REQUEST,
  signal?: AbortSignal
): Promise<AnomalyDetectionResult> {
  return requestJson<AnomalyDetectionResult>(
    "/api/v1/post-trade/anomalies",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
      signal,
    },
    { timeoutMs: API_REQUEST_TIMEOUT_MS }
  );
}
