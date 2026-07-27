/** Recharts shared theme — CSS variables keep charts in sync with light/dark mode. */

export const CHART_TOOLTIP_STYLE = {
  contentStyle: {
    backgroundColor: "var(--chart-tooltip-bg)",
    border: "1px solid var(--chart-tooltip-border)",
    color: "var(--text-primary)",
    borderRadius: "0.5rem",
    fontSize: "0.9375rem",
    boxShadow: "var(--shadow)",
  },
  labelStyle: { color: "var(--text-primary)", fontWeight: 600 },
  itemStyle: { color: "var(--text-secondary)" },
};

export const CHART_GRID_STROKE = "var(--chart-grid)";
export const CHART_TICK_FILL = "var(--chart-tick)";
export const CHART_BRUSH_STROKE = "var(--chart-accent)";
export const CHART_TICK_FONT_SIZE = 12;

/** 主序列：蓝色；对比序列：灰色；回撤策略：橙色（避免红绿配对） */
export const CHART_COLORS = {
  strategy: "var(--chart-series-1)",
  benchmark: "var(--chart-series-2)",
  drawdownStrategy: "var(--chart-series-3)",
  drawdownBenchmark: "var(--chart-series-4)",
  close: "var(--chart-series-5)",
  ma20: "var(--chart-series-1)",
  ma60: "var(--chart-series-6)",
};

export const CHART_COMPARE_LINES = [
  "var(--chart-series-1)",
  "var(--chart-series-3)",
  "var(--chart-series-6)",
  "var(--chart-series-7)",
  "var(--chart-series-8)",
  "var(--chart-series-9)",
  "var(--chart-series-10)",
  "var(--chart-series-11)",
  "var(--chart-series-12)",
  "var(--chart-series-13)",
];
