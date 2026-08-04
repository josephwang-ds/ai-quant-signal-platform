export type InputDataKind = "operator_supplied" | "synthetic_demo";

export type AttributionObservation = {
  trade_id: string;
  timestamp: string;
  strategy: string;
  venue: string;
  notional_usd: number;
  gross_pnl_bps: number;
  benchmark_pnl_bps: number;
  fees_bps: number;
  slippage_bps: number;
};

export type AttributionRequest = {
  observations: AttributionObservation[];
  group_by: "strategy" | "venue";
  input_data_kind: InputDataKind;
};

export type AttributionComponent = {
  key: "gross_edge" | "fees" | "slippage" | "net_active";
  label: string;
  contribution_bps: number;
  contribution_usd: number;
};

export type AttributionGroup = {
  group: string;
  observation_count: number;
  notional_usd: number;
  gross_edge_bps: number;
  fee_drag_bps: number;
  slippage_drag_bps: number;
  net_active_bps: number;
  net_active_usd: number;
};

export type AttributionResult = {
  methodology: string;
  input_data_kind: InputDataKind;
  group_by: "strategy" | "venue";
  observation_count: number;
  total_notional_usd: number;
  gross_edge_bps: number;
  fee_drag_bps: number;
  slippage_drag_bps: number;
  net_active_bps: number;
  net_active_usd: number;
  reconciliation_error_usd: number;
  components: AttributionComponent[];
  groups: AttributionGroup[];
};

export type MetricObservation = {
  timestamp: string;
  metric: string;
  entity: string;
  value: number;
};

export type AnomalyDetectionRequest = {
  observations: MetricObservation[];
  baseline_window: number;
  minimum_history: number;
  threshold: number;
  direction: "high" | "low" | "two_sided";
  input_data_kind: InputDataKind;
};

export type AnomalyEvent = {
  timestamp: string;
  metric: string;
  entity: string;
  value: number;
  baseline_median: number;
  robust_scale: number;
  robust_z_score: number;
  severity: "warning" | "critical";
  history_count: number;
};

export type MetricSeriesSummary = {
  metric: string;
  entity: string;
  observation_count: number;
  scored_count: number;
  anomaly_count: number;
  latest_value: number;
  latest_baseline_median: number | null;
  latest_robust_z_score: number | null;
  status: "normal" | "warning" | "critical" | "insufficient_history";
};

export type ScoredMetricPoint = {
  timestamp: string;
  metric: string;
  entity: string;
  value: number;
  baseline_median: number | null;
  upper_threshold: number | null;
  lower_threshold: number | null;
  robust_z_score: number | null;
  status: "warmup" | "normal" | "warning" | "critical";
};

export type AnomalyDetectionResult = {
  methodology: string;
  input_data_kind: InputDataKind;
  baseline_window: number;
  minimum_history: number;
  threshold: number;
  direction: "high" | "low" | "two_sided";
  observation_count: number;
  scored_count: number;
  anomaly_count: number;
  points: ScoredMetricPoint[];
  anomalies: AnomalyEvent[];
  series: MetricSeriesSummary[];
};
