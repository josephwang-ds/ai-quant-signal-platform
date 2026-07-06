"use client";

import {
  Brush,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceDot,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import EmptyState from "@/components/ui/EmptyState";
import {
  CHART_BRUSH_STROKE,
  CHART_COLORS,
  CHART_GRID_STROKE,
  CHART_TICK_FILL,
  CHART_TICK_FONT_SIZE,
  CHART_TOOLTIP_STYLE,
} from "@/lib/chartTheme";
import type { ChartLabels } from "@/lib/i18n";
import type { BacktestRow } from "@/types/market";

type BacktestChartProps = {
  data: BacktestRow[];
  labels: ChartLabels;
};

function formatTooltipValue(value: unknown, decimals = 4): string {
  if (value == null || value === "") {
    return "N/A";
  }
  const num = typeof value === "number" ? value : Number(value);
  return Number.isFinite(num) ? num.toFixed(decimals) : "N/A";
}

export default function BacktestChart({ data, labels }: BacktestChartProps) {
  if (data.length === 0) {
    return <EmptyState message={labels.noBacktestData} />;
  }

  const chartData = data.map((row) => ({
    ...row,
    strategy_drawdown: row.strategy_drawdown ?? row.drawdown,
  }));

  const tradeMarkers = chartData.filter(
    (row) => row.trade_action === "BUY" || row.trade_action === "SELL"
  );

  return (
    <div className="chart-stack">
      <div className="chart-panel">
        <h4 className="chart-panel__title">{labels.strategyVsHold}</h4>
        <div className="chart-panel__container">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              syncId="backtestZoom"
              data={chartData}
              margin={{ top: 8, right: 16, left: 0, bottom: 8 }}
            >
              <CartesianGrid stroke={CHART_GRID_STROKE} strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fill: CHART_TICK_FILL, fontSize: CHART_TICK_FONT_SIZE }} minTickGap={32} />
              <YAxis tick={{ fill: CHART_TICK_FILL, fontSize: CHART_TICK_FONT_SIZE }} domain={["auto", "auto"]} width={56} />
              <Tooltip
                {...CHART_TOOLTIP_STYLE}
                formatter={(value) => formatTooltipValue(value, 4)}
              />
              <Legend wrapperStyle={{ fontSize: "0.9375rem", color: CHART_TICK_FILL }} />
              <Line type="monotone" dataKey="cumulative_strategy" name={labels.strategy} stroke={CHART_COLORS.strategy} dot={false} strokeWidth={2.5} />
              <Line type="monotone" dataKey="cumulative_benchmark" name={labels.buyHold} stroke={CHART_COLORS.benchmark} dot={false} strokeWidth={2} />
              {tradeMarkers.map((row) => (
                <ReferenceDot
                  key={`${row.date}-${row.trade_action}`}
                  x={row.date}
                  y={row.cumulative_strategy}
                  r={6}
                  fill={row.trade_action === "BUY" ? "#16a34a" : "#dc2626"}
                  stroke="#ffffff"
                  strokeWidth={2}
                  ifOverflow="extendDomain"
                />
              ))}
              <Brush dataKey="date" height={28} stroke={CHART_BRUSH_STROKE} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="chart-panel">
        <h4 className="chart-panel__title">{labels.strategyVsHoldDrawdown}</h4>
        <div className="chart-panel__container chart-panel__container--md">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              syncId="backtestZoom"
              data={chartData}
              margin={{ top: 8, right: 16, left: 0, bottom: 8 }}
            >
              <CartesianGrid stroke={CHART_GRID_STROKE} strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fill: CHART_TICK_FILL, fontSize: CHART_TICK_FONT_SIZE }} minTickGap={32} />
              <YAxis
                tick={{ fill: CHART_TICK_FILL, fontSize: CHART_TICK_FONT_SIZE }}
                domain={["auto", "auto"]}
                width={56}
                tickFormatter={(value: number) => `${(value * 100).toFixed(0)}%`}
              />
              <Tooltip
                {...CHART_TOOLTIP_STYLE}
                formatter={(value) => {
                  const num = typeof value === "number" ? value : Number(value);
                  return Number.isFinite(num) ? `${(num * 100).toFixed(2)}%` : "N/A";
                }}
              />
              <Legend wrapperStyle={{ fontSize: "0.9375rem", color: CHART_TICK_FILL }} />
              <Line type="monotone" dataKey="strategy_drawdown" name={labels.strategyDrawdown} stroke={CHART_COLORS.drawdownStrategy} dot={false} strokeWidth={2} strokeDasharray="6 3" />
              <Line type="monotone" dataKey="benchmark_drawdown" name={labels.benchmarkDrawdown} stroke={CHART_COLORS.drawdownBenchmark} dot={false} strokeWidth={2} />
              <Brush dataKey="date" height={28} stroke={CHART_BRUSH_STROKE} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <p className="helper-text">{labels.backtestZoomHint}</p>
    </div>
  );
}
