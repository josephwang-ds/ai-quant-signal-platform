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
  CHART_COMPARE_LINES,
  CHART_GRID_STROKE,
  CHART_TICK_FILL,
  CHART_TICK_FONT_SIZE,
  CHART_TOOLTIP_STYLE,
} from "@/lib/chartTheme";
import type { ChartLabels } from "@/lib/i18n";
import type { CompareChartResponse } from "@/types/market";

const LINE_COLORS = CHART_COMPARE_LINES;

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
            <XAxis dataKey="date" tick={{ fill: CHART_TICK_FILL, fontSize: CHART_TICK_FONT_SIZE }} minTickGap={32} />
            <YAxis tick={{ fill: CHART_TICK_FILL, fontSize: CHART_TICK_FONT_SIZE }} domain={["auto", "auto"]} width={56} />
            <Tooltip {...CHART_TOOLTIP_STYLE} formatter={(value: number) => value.toFixed(2)} />
            <Legend wrapperStyle={{ fontSize: "0.9375rem", color: CHART_TICK_FILL }} />
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
