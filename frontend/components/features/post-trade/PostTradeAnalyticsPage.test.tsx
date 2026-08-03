import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import PostTradeAnalyticsPage from "@/components/features/post-trade/PostTradeAnalyticsPage";

vi.stubGlobal(
  "ResizeObserver",
  class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
);

vi.mock("@/lib/useWorkspaceLanguage", () => ({
  useWorkspaceLanguage: () => ({
    language: "en" as const,
    setLanguage: vi.fn(),
  }),
}));

vi.mock("@/components/layout/AppShell", () => ({
  default: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="app-shell">{children}</div>
  ),
}));

vi.mock("@/lib/postTradeAnalytics", () => ({
  DEMO_ATTRIBUTION_REQUEST: {
    input_data_kind: "synthetic_demo",
    group_by: "venue",
    observations: [],
  },
  fetchPerformanceAttribution: vi.fn().mockResolvedValue({
    methodology: "Notional-weighted active PnL.",
    input_data_kind: "synthetic_demo",
    group_by: "venue",
    observation_count: 6,
    total_notional_usd: 7_020_000,
    gross_edge_bps: 4.0,
    fee_drag_bps: -0.3,
    slippage_drag_bps: -0.7,
    net_active_bps: 3.0,
    net_active_usd: 2_106,
    reconciliation_error_usd: 0,
    components: [
      {
        key: "gross_edge",
        label: "Gross edge vs benchmark",
        contribution_bps: 4.0,
        contribution_usd: 2_808,
      },
      {
        key: "fees",
        label: "Fees",
        contribution_bps: -0.3,
        contribution_usd: -210.6,
      },
      {
        key: "slippage",
        label: "Slippage",
        contribution_bps: -0.7,
        contribution_usd: -491.4,
      },
      {
        key: "net_active",
        label: "Net active PnL",
        contribution_bps: 3.0,
        contribution_usd: 2_106,
      },
    ],
    groups: [
      {
        group: "XNAS",
        observation_count: 2,
        notional_usd: 2_350_000,
        gross_edge_bps: 4.2,
        fee_drag_bps: -0.35,
        slippage_drag_bps: -1.0,
        net_active_bps: 2.85,
        net_active_usd: 669.75,
      },
    ],
  }),
  fetchAnomalyDetection: vi.fn().mockResolvedValue({
    methodology: "Past-only rolling median/MAD.",
    input_data_kind: "synthetic_demo",
    baseline_window: 12,
    minimum_history: 6,
    threshold: 3.5,
    direction: "high",
    observation_count: 36,
    scored_count: 24,
    anomaly_count: 1,
    points: [
      {
        timestamp: "2026-07-29T01:44:00.000Z",
        metric: "ack_latency_ms",
        entity: "gateway-a",
        value: 3.85,
        baseline_median: 1.21,
        upper_threshold: 1.32,
        lower_threshold: 1.1,
        robust_z_score: 88,
        status: "critical",
      },
    ],
    anomalies: [
      {
        timestamp: "2026-07-29T01:44:00.000Z",
        metric: "ack_latency_ms",
        entity: "gateway-a",
        value: 3.85,
        baseline_median: 1.21,
        robust_scale: 0.03,
        robust_z_score: 88,
        severity: "critical",
        history_count: 12,
      },
    ],
    series: [],
  }),
}));

describe("PostTradeAnalyticsPage", () => {
  it("renders both JD-focused evidence sections and the data boundary", async () => {
    render(<PostTradeAnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByTestId("performance-attribution")).toBeInTheDocument();
    });
    expect(screen.getByTestId("anomaly-detection")).toBeInTheDocument();
    expect(screen.getByRole("note")).toHaveTextContent("not live orders");
    expect(screen.getAllByText("+3.00 bps")).toHaveLength(2);
    expect(screen.getAllByText("gateway-a").length).toBeGreaterThan(0);
    expect(screen.getByText("critical")).toBeInTheDocument();
  });
});
