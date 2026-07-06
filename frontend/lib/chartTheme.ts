/** Recharts 共享主题（浅色 + 色盲友好配色） */

export const CHART_TOOLTIP_STYLE = {
  contentStyle: {
    backgroundColor: "#ffffff",
    border: "1px solid #cbd5e1",
    borderRadius: "0.5rem",
    fontSize: "0.9375rem",
    boxShadow: "0 4px 12px rgba(15, 23, 42, 0.08)",
  },
  labelStyle: { color: "#0f172a", fontWeight: 600 },
};

export const CHART_GRID_STROKE = "#e2e8f0";
export const CHART_TICK_FILL = "#475569";
export const CHART_BRUSH_STROKE = "#2563eb";
export const CHART_TICK_FONT_SIZE = 12;

/** 主序列：蓝色；对比序列：灰色；回撤策略：橙色（避免红绿配对） */
export const CHART_COLORS = {
  strategy: "#2563eb",
  benchmark: "#64748b",
  drawdownStrategy: "#ea580c",
  drawdownBenchmark: "#475569",
  close: "#1e293b",
  ma20: "#2563eb",
  ma60: "#7c3aed",
};

export const CHART_COMPARE_LINES = [
  "#2563eb",
  "#ea580c",
  "#7c3aed",
  "#0891b2",
  "#9333ea",
  "#c2410c",
  "#0369a1",
  "#a16207",
  "#4f46e5",
  "#b45309",
];
