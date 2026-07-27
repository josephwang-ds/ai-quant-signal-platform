"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import MetricSummaryCard from "@/components/ui/MetricSummaryCard";
import ResearchCenterHeader from "@/components/features/research/ux/ResearchCenterHeader";
import {
  CHART_COLORS,
  CHART_COMPARE_LINES,
  CHART_GRID_STROKE,
  CHART_TICK_FILL,
  CHART_TICK_FONT_SIZE,
  CHART_TOOLTIP_STYLE,
} from "@/lib/chartTheme";
import type { Language } from "@/lib/i18n";
import { formatResearchTimestamp } from "@/lib/researchDisplay";
import type { FactorValidationResult } from "@/types/factorValidation";

export type FactorValidationLabels = {
  title: string;
  summary: string;
  meanRankIc: string;
  medianRankIc: string;
  positiveIc: string;
  icir: string;
  monthlyIc: string;
  rollingIc: string;
  quantileCumulative: string;
  longShortCumulative: string;
  q5Cumulative: string;
  q1Cumulative: string;
  lsCumulative: string;
  lsNetCumulative: string;
  meanTurnover: string;
  totalCost: string;
  warnings: string;
  generated: string;
  unavailable: string;
  factor: string;
  universe: string;
};

type Props = {
  validation: FactorValidationResult;
  labels: FactorValidationLabels;
  language: Language;
};

function fmtRatio(value: number | null | undefined, unavailable: string): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return unavailable;
  }
  return value.toFixed(4);
}

function fmtPct(value: number | null | undefined, unavailable: string): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return unavailable;
  }
  return `${(value * 100).toFixed(2)}%`;
}

const Q_COLORS: Record<string, string> = {
  Q1: CHART_COMPARE_LINES[1],
  Q2: CHART_COMPARE_LINES[4],
  Q3: CHART_COLORS.benchmark,
  Q4: CHART_COMPARE_LINES[3],
  Q5: CHART_COLORS.strategy,
  LS: CHART_COMPARE_LINES[2],
};

export default function FactorValidationPanel({
  validation,
  labels,
  language,
}: Props) {
  const summary = validation.ic.summary;
  const icChart = validation.ic.series.map((point) => ({
    date: point.date,
    rankIc: point.value,
  }));
  const rollingChart = validation.ic.rolling_series.map((point) => ({
    date: point.date,
    rollingIc: point.value,
  }));

  const quantileDates =
    validation.quantiles.cumulative_returns.Q1?.map((p) => p.date) ??
    validation.long_short.cumulative_returns.map((p) => p.date);

  const quantileChart = quantileDates.map((date, index) => {
    const row: Record<string, string | number> = { date };
    for (const q of ["Q1", "Q2", "Q3", "Q4", "Q5"]) {
      const series = validation.quantiles.cumulative_returns[q];
      if (series?.[index]) row[q] = series[index].value;
    }
    return row;
  });

  const lsChart = validation.long_short.cumulative_returns.map((point, index) => {
    const net =
      validation.long_short.cumulative_returns_net_of_cost?.[index]?.value;
    return {
      date: point.date,
      ls: point.value,
      ...(typeof net === "number" ? { lsNet: net } : {}),
    };
  });

  return (
    <section className="research-validation-panel factor-validation-panel">
      <ResearchCenterHeader
        title={labels.title}
        description={`${labels.factor}: ${validation.factor_id} · ${labels.universe}: ${validation.universe_id}`}
      />
      <p className="section-meta">{labels.summary}</p>

      <div className="metric-summary-grid">
        <MetricSummaryCard
          label={labels.meanRankIc}
          value={fmtRatio(summary.mean_rank_ic, labels.unavailable)}
        />
        <MetricSummaryCard
          label={labels.medianRankIc}
          value={fmtRatio(summary.median_rank_ic, labels.unavailable)}
        />
        <MetricSummaryCard
          label={labels.positiveIc}
          value={fmtPct(summary.positive_ic_ratio, labels.unavailable)}
        />
        <MetricSummaryCard
          label={labels.icir}
          value={fmtRatio(summary.icir, labels.unavailable)}
        />
        <MetricSummaryCard
          label={labels.q5Cumulative}
          value={fmtPct(
            validation.quantiles.cumulative_returns.Q5?.at(-1)?.value ?? null,
            labels.unavailable
          )}
        />
        <MetricSummaryCard
          label={labels.q1Cumulative}
          value={fmtPct(
            validation.quantiles.cumulative_returns.Q1?.at(-1)?.value ?? null,
            labels.unavailable
          )}
        />
        <MetricSummaryCard
          label={labels.lsCumulative}
          value={fmtPct(
            validation.long_short.cumulative_final,
            labels.unavailable
          )}
          tone="emphasis"
        />
        <MetricSummaryCard
          label={labels.lsNetCumulative}
          value={fmtPct(
            validation.long_short.cumulative_final_net_of_cost ?? null,
            labels.unavailable
          )}
        />
        <MetricSummaryCard
          label={labels.meanTurnover}
          value={fmtRatio(
            validation.quantiles.turnover.mean,
            labels.unavailable
          )}
        />
        <MetricSummaryCard
          label={labels.totalCost}
          value={fmtPct(
            validation.quantiles.transaction_cost.total,
            labels.unavailable
          )}
        />
      </div>

      <div className="factor-validation-charts">
        <div className="chart-panel">
          <h3 className="chart-panel__title">{labels.monthlyIc}</h3>
          <div className="chart-panel__body" style={{ width: "100%", height: 260 }}>
            <ResponsiveContainer>
              <LineChart data={icChart} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
                <CartesianGrid stroke={CHART_GRID_STROKE} strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  hide={icChart.length > 24}
                  tick={{ fill: CHART_TICK_FILL, fontSize: CHART_TICK_FONT_SIZE }}
                />
                <YAxis
                  tick={{ fill: CHART_TICK_FILL, fontSize: CHART_TICK_FONT_SIZE }}
                  tickFormatter={(v) => Number(v).toFixed(2)}
                  width={48}
                />
                <Tooltip {...CHART_TOOLTIP_STYLE} />
                <Line
                  type="monotone"
                  dataKey="rankIc"
                  name="RankIC"
                  stroke={Q_COLORS.LS}
                  dot={false}
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-panel">
          <h3 className="chart-panel__title">{labels.rollingIc}</h3>
          <div className="chart-panel__body" style={{ width: "100%", height: 260 }}>
            <ResponsiveContainer>
              <LineChart
                data={rollingChart}
                margin={{ top: 8, right: 16, left: 0, bottom: 8 }}
              >
                <CartesianGrid stroke={CHART_GRID_STROKE} strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  hide={rollingChart.length > 24}
                  tick={{ fill: CHART_TICK_FILL, fontSize: CHART_TICK_FONT_SIZE }}
                />
                <YAxis
                  tick={{ fill: CHART_TICK_FILL, fontSize: CHART_TICK_FONT_SIZE }}
                  tickFormatter={(v) => Number(v).toFixed(2)}
                  width={48}
                />
                <Tooltip {...CHART_TOOLTIP_STYLE} />
                <Line
                  type="monotone"
                  dataKey="rollingIc"
                  name="Rolling IC"
                  stroke={Q_COLORS.Q5}
                  dot={false}
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-panel">
          <h3 className="chart-panel__title">{labels.quantileCumulative}</h3>
          <div className="chart-panel__body" style={{ width: "100%", height: 280 }}>
            <ResponsiveContainer>
              <LineChart
                data={quantileChart}
                margin={{ top: 8, right: 16, left: 0, bottom: 8 }}
              >
                <CartesianGrid stroke={CHART_GRID_STROKE} strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  hide={quantileChart.length > 24}
                  tick={{ fill: CHART_TICK_FILL, fontSize: CHART_TICK_FONT_SIZE }}
                />
                <YAxis
                  tick={{ fill: CHART_TICK_FILL, fontSize: CHART_TICK_FONT_SIZE }}
                  tickFormatter={(v) => `${(Number(v) * 100).toFixed(0)}%`}
                  width={48}
                />
                <Tooltip
                  {...CHART_TOOLTIP_STYLE}
                  formatter={(value) =>
                    typeof value === "number" ? fmtPct(value, labels.unavailable) : value
                  }
                />
                <Legend />
                {(["Q1", "Q2", "Q3", "Q4", "Q5"] as const).map((q) => (
                  <Line
                    key={q}
                    type="monotone"
                    dataKey={q}
                    stroke={Q_COLORS[q]}
                    dot={false}
                    strokeWidth={q === "Q5" || q === "Q1" ? 2 : 1.25}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-panel">
          <h3 className="chart-panel__title">{labels.longShortCumulative}</h3>
          <div className="chart-panel__body" style={{ width: "100%", height: 260 }}>
            <ResponsiveContainer>
              <LineChart data={lsChart} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
                <CartesianGrid stroke={CHART_GRID_STROKE} strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  hide={lsChart.length > 24}
                  tick={{ fill: CHART_TICK_FILL, fontSize: CHART_TICK_FONT_SIZE }}
                />
                <YAxis
                  tick={{ fill: CHART_TICK_FILL, fontSize: CHART_TICK_FONT_SIZE }}
                  tickFormatter={(v) => `${(Number(v) * 100).toFixed(0)}%`}
                  width={48}
                />
                <Tooltip
                  {...CHART_TOOLTIP_STYLE}
                  formatter={(value) =>
                    typeof value === "number" ? fmtPct(value, labels.unavailable) : value
                  }
                />
                <Line
                  type="monotone"
                  dataKey="ls"
                  name="Q5−Q1 (gross)"
                  stroke={Q_COLORS.LS}
                  dot={false}
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="lsNet"
                  name="Q5−Q1 (net of cost)"
                  stroke={Q_COLORS.Q4}
                  dot={false}
                  strokeWidth={2}
                  strokeDasharray="4 3"
                />
                <Legend />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {validation.long_short.note ? (
        <p className="section-meta">{validation.long_short.note}</p>
      ) : null}

      {validation.warnings.length > 0 ? (
        <div className="research-validation-panel__warnings">
          <h3>{labels.warnings}</h3>
          <ul>
            {validation.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <p className="section-meta">
        {labels.generated}:{" "}
        {formatResearchTimestamp(validation.generated_at, language)}
      </p>
    </section>
  );
}
