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
import type { IndicatorRow } from "@/types/market";

type PriceChartProps = {
  data: IndicatorRow[];
  labels: ChartLabels;
};

export default function PriceChart({ data, labels }: PriceChartProps) {
  if (data.length === 0) {
    return <EmptyState message={labels.noChartData} />;
  }

  return (
    <div>
      <div className="chart-panel__container">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
            <CartesianGrid stroke={CHART_GRID_STROKE} strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fill: CHART_TICK_FILL, fontSize: 11 }} minTickGap={32} />
            <YAxis tick={{ fill: CHART_TICK_FILL, fontSize: 11 }} domain={["auto", "auto"]} width={56} />
            <Tooltip
              {...CHART_TOOLTIP_STYLE}
              formatter={(value) => {
                if (value == null || value === "") {
                  return "N/A";
                }
                const num = typeof value === "number" ? value : Number(value);
                return Number.isFinite(num) ? num.toFixed(2) : "N/A";
              }}
            />
            <Legend wrapperStyle={{ fontSize: "0.8125rem", color: CHART_TICK_FILL }} />
            <Line type="monotone" dataKey="close" name={labels.close} stroke="#f1f5f9" dot={false} strokeWidth={2} connectNulls={false} />
            <Line type="monotone" dataKey="ma20" name="MA20" stroke="#38bdf8" dot={false} strokeWidth={1.5} connectNulls={false} />
            <Line type="monotone" dataKey="ma60" name="MA60" stroke="#4ade80" dot={false} strokeWidth={1.5} connectNulls={false} />
            <Brush dataKey="date" height={28} stroke={CHART_BRUSH_STROKE} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="helper-text">{labels.chartZoomHint}</p>
    </div>
  );
}
