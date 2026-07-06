"use client";

import {
  Brush,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import EmptyState from "@/components/ui/EmptyState";
import {
  CHART_BRUSH_STROKE,
  CHART_GRID_STROKE,
  CHART_TICK_FILL,
  CHART_TOOLTIP_STYLE,
} from "@/lib/chartTheme";
import type { ChartLabels } from "@/lib/i18n";
import type { CompareChartResponse } from "@/types/market";

const LINE_COLORS = [
  "#f1f5f9",
  "#38bdf8",
  "#4ade80",
  "#fbbf24",
  "#f87171",
  "#a78bfa",
  "#fb7185",
  "#22d3ee",
  "#86efac",
  "#fcd34d",
];

type CompareChartProps = {
  tickers: string[];
  data: CompareChartResponse["data"];
  labels: ChartLabels;
};

export default function CompareChart({ tickers, data, labels }: CompareChartProps) {
  if (data.length === 0) {
    return <EmptyState message={labels.noCompareData} />;
  }

  return (
    <div>
      <div className="chart-panel__container">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
            <CartesianGrid stroke={CHART_GRID_STROKE} strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fill: CHART_TICK_FILL, fontSize: 11 }} minTickGap={32} />
            <YAxis tick={{ fill: CHART_TICK_FILL, fontSize: 11 }} domain={["auto", "auto"]} width={56} />
            <Tooltip {...CHART_TOOLTIP_STYLE} formatter={(value: number) => value.toFixed(2)} />
            <Legend wrapperStyle={{ fontSize: "0.8125rem", color: CHART_TICK_FILL }} />
            {tickers.map((ticker, index) => (
              <Line
                key={ticker}
                type="monotone"
                dataKey={ticker}
                name={ticker}
                stroke={LINE_COLORS[index % LINE_COLORS.length]}
                dot={false}
                strokeWidth={1.5}
              />
            ))}
            <Brush dataKey="date" height={28} stroke={CHART_BRUSH_STROKE} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="helper-text">{labels.chartZoomHint}</p>
    </div>
  );
}
